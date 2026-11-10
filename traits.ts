import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { TypeSafeClient, TypeSafeDecisionModel } from "@effect/ai-typesafe";
import { Effect, Layer, Redacted, Stream } from "effect";
import { AiError, LanguageModel } from "effect/ai";
import type { TraitsConfig } from "traits";

const JEV_MODEL = "jev-latest";
const KEYCHAIN_SERVICE = "typesafe-api-key";

const run = promisify(execFile);

const keychainKey = Effect.tryPromise(() =>
  run("security", ["find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"]),
).pipe(
  Effect.map(({ stdout }) => stdout.trim()),
  Effect.orElseSucceed(() => ""),
);

const typeSafeApiKey = Effect.map(keychainKey, (fromKeychain) => {
  const key = fromKeychain || process.env.TYPESAFE_API_KEY?.trim() || "";
  return key ? Redacted.make(key) : undefined;
});

const layerTypeSafeClient = Layer.unwrap(
  Effect.map(typeSafeApiKey, (apiKey) => TypeSafeClient.layer({ apiKey })),
);

const layerJevDecisionModel = TypeSafeDecisionModel.layer({ model: JEV_MODEL }).pipe(
  Layer.provide(layerTypeSafeClient),
);

const noGeneration = AiError.make({
  module: "traits.ts",
  method: "generateText",
  reason: new AiError.UnknownError({
    description:
      "traits.ts configures no generation model. Split the proposal into single-rule traits, or reconcile it with the conflicting trait, and submit those instead.",
  }),
});

const layerNoLanguageModel = Layer.effect(
  LanguageModel.LanguageModel,
  LanguageModel.make({
    generateText: () => Effect.fail(noGeneration),
    streamText: () => Stream.fail(noGeneration),
  }),
);

export default {
  excludes: ["node_modules/**", "**/node_modules/**", "**/dist/**", ".venv/**"],
  layerDecisionModel: layerJevDecisionModel,
  layerLanguageModel: layerNoLanguageModel,
} satisfies TraitsConfig;
