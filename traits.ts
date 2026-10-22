import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { Effect, Layer, Stream } from "effect";
import { AiError, DecisionModel, LanguageModel, Tool } from "effect/ai";
import type { Decision, Prompt } from "effect/ai";
import type { TraitsConfig } from "traits";

const CLAUDE_MODEL = "sonnet";

const run = promisify(execFile);

const messageText = (message: Prompt.Message): string =>
  typeof message.content === "string"
    ? message.content
    : message.content
        .flatMap((part) => (part.type === "text" ? [part.text] : []))
        .join("\n");

const claudeFailure = (description: string) =>
  AiError.make({
    module: "ClaudeCode",
    method: "generateText",
    reason: new AiError.UnknownError({ description }),
  });

const CLAUDE_ARGS = [
  "-p",
  "--output-format=json",
  "--model",
  CLAUDE_MODEL,
  "--tools",
  "",
  "--strict-mcp-config",
  "--setting-sources",
  "",
  "--disable-slash-commands",
  "--no-session-persistence",
];

const runClaude = (args: ReadonlyArray<string>) =>
  Effect.gen(function* () {
    const { stdout } = yield* Effect.tryPromise({
      try: () => run("claude", [...args], { maxBuffer: 64 * 1024 * 1024 }),
      catch: (cause) =>
        claudeFailure(
          `claude -p failed: ${cause instanceof Error && "stdout" in cause ? String(cause.stdout) : String(cause)}`,
        ),
    });
    const result: unknown = yield* Effect.try({
      try: () => JSON.parse(stdout),
      catch: () => claudeFailure("claude -p printed non-JSON output"),
    });
    if (
      typeof result !== "object" ||
      result === null ||
      !("is_error" in result) ||
      result.is_error !== false
    ) {
      const detail =
        typeof result === "object" && result !== null && "result" in result
          ? String(result.result)
          : "";
      return yield* claudeFailure(`claude -p returned an error: ${detail}`);
    }
    return result;
  });

const askClaude = (options: LanguageModel.ProviderOptions) =>
  Effect.gen(function* () {
    const system = options.prompt.content
      .filter((message) => message.role === "system")
      .map(messageText);
    const conversation = options.prompt.content
      .filter((message) => message.role !== "system")
      .map((message) => `${message.role}:\n${messageText(message)}`);
    const args = [...CLAUDE_ARGS];
    if (system.length > 0) args.push("--system-prompt", system.join("\n\n"));
    if (options.responseFormat.type === "json") {
      args.push(
        "--json-schema",
        JSON.stringify(
          Tool.getJsonSchemaFromSchema(options.responseFormat.schema),
        ),
      );
    }
    args.push(conversation.join("\n\n"));

    const result = yield* runClaude(args);
    const text =
      options.responseFormat.type === "json" && "structured_output" in result
        ? JSON.stringify(result.structured_output)
        : "result" in result
          ? String(result.result)
          : "";
    return [
      { type: "text" as const, text },
      {
        type: "finish" as const,
        reason: "stop" as const,
        usage: { inputTokens: {}, outputTokens: {} },
      },
    ];
  });

const layerClaudeLanguageModel = Layer.effect(
  LanguageModel.LanguageModel,
  LanguageModel.make({
    generateText: askClaude,
    streamText: () =>
      Stream.fail(
        claudeFailure("streamText is not supported by the claude -p model"),
      ),
  }),
);

const decisionLabels = (decision: Decision.Any): ReadonlyArray<string> | null =>
  decision._tag === "Classify"
    ? Object.keys(decision.criteria)
    : decision._tag === "Rate"
      ? decision.criteria.map((level) => level.label)
      : null;

const unitNumber = { type: "number", minimum: 0, maximum: 1 };

const decisionSchema = (decisions: Record<string, Decision.Any>) => ({
  type: "object",
  additionalProperties: false,
  required: Object.keys(decisions),
  properties: Object.fromEntries(
    Object.entries(decisions).map(([key, decision]) => {
      const labels = decisionLabels(decision);
      const field =
        labels === null
          ? { probability: unitNumber }
          : {
              probabilities: {
                type: "object",
                additionalProperties: false,
                required: labels,
                properties: Object.fromEntries(labels.map((label) => [label, unitNumber])),
              },
            };
      return [
        key,
        { type: "object", additionalProperties: false, required: Object.keys(field), properties: field },
      ];
    }),
  ),
});

const normalized = (labels: ReadonlyArray<string>, raw: Record<string, number>) => {
  const total = labels.reduce((sum, label) => sum + Math.max(0, raw[label] ?? 0), 0);
  return Object.fromEntries(
    labels.map((label) => [
      label,
      total > 0 ? Math.max(0, raw[label] ?? 0) / total : 1 / labels.length,
    ]),
  );
};

const decideWithClaude = (options: DecisionModel.ProviderOptions) =>
  Effect.gen(function* () {
    const result = yield* runClaude([
      ...CLAUDE_ARGS,
      "--system-prompt",
      "Make each decision in `decisions` about `input`. Follow each decision's instructions and criteria. Give calibrated probabilities that reflect your real uncertainty.",
      "--json-schema",
      JSON.stringify(decisionSchema(options.decisions)),
      JSON.stringify({ input: options.state, decisions: options.decisions }),
    ]);
    if (!("structured_output" in result) || typeof result.structured_output !== "object") {
      return yield* claudeFailure("claude -p returned no structured decision output");
    }
    const output = result.structured_output as Record<
      string,
      { probabilities?: Record<string, number>; probability?: number }
    >;
    const answers: Record<string, DecisionModel.ProviderAnswer> = {};
    for (const [key, decision] of Object.entries(options.decisions)) {
      const labels = decisionLabels(decision);
      if (labels === null) {
        answers[key] = { _tag: "Probability", probability: output[key]?.probability ?? 0.5 };
        continue;
      }
      const probabilities = normalized(labels, output[key]?.probabilities ?? {});
      const label = labels.reduce((best, l) => (probabilities[l] > probabilities[best] ? l : best));
      answers[key] =
        decision._tag === "Classify"
          ? { _tag: "Classify", label, probabilities }
          : {
              _tag: "Rate",
              rating: labels.reduce((sum, l, i) => sum + i * probabilities[l], 0),
              probabilities,
            };
    }
    return { answers, usage: { inputTokens: undefined, outputTokens: undefined } };
  });

const layerClaudeDecisionModel = Layer.effect(
  DecisionModel.DecisionModel,
  DecisionModel.make({ decide: decideWithClaude }),
);

export default {
  excludes: ["node_modules/**", "**/node_modules/**", "**/dist/**", ".venv/**"],
  layerDecisionModel: layerClaudeDecisionModel,
  layerLanguageModel: layerClaudeLanguageModel,
} satisfies TraitsConfig;
