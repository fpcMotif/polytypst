import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { TypeSafeClient, TypeSafeDecisionModel } from "@effect/ai-typesafe";
import { Effect, Layer, Stream } from "effect";
import { AiError, LanguageModel, Tool } from "effect/ai";
import type { Prompt } from "effect/ai";
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

const askClaude = (options: LanguageModel.ProviderOptions) =>
  Effect.gen(function* () {
    const system = options.prompt.content
      .filter((message) => message.role === "system")
      .map(messageText);
    const conversation = options.prompt.content
      .filter((message) => message.role !== "system")
      .map((message) => `${message.role}:\n${messageText(message)}`);
    const args = [
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

    const { stdout } = yield* Effect.tryPromise({
      try: () => run("claude", args, { maxBuffer: 64 * 1024 * 1024 }),
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

export default {
  excludes: ["node_modules/**", "**/node_modules/**", "**/dist/**", ".venv/**"],
  layerDecisionModel: TypeSafeDecisionModel.layer({ model: "jev-latest" }).pipe(
    Layer.provide(TypeSafeClient.layerConfig()),
  ),
  layerLanguageModel: layerClaudeLanguageModel,
} satisfies TraitsConfig;
