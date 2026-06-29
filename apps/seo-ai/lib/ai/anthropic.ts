import type Anthropic from "@anthropic-ai/sdk";

/**
 * Anthropic client helpers for the SEO-AI auditor.
 *
 * The module is import-safe even when ANTHROPIC_API_KEY is absent — the SDK is
 * lazily imported and the client is only constructed when `askClaudeJSON` is
 * actually invoked, so callers can `import` this freely and fall back to
 * heuristics when live AI is disabled.
 */

const DEFAULT_MODEL = "claude-sonnet-4-6";

/** True when an Anthropic API key is configured in the environment. */
export function isLiveAIEnabled(): boolean {
  const key = process.env.ANTHROPIC_API_KEY;
  return typeof key === "string" && key.trim().length > 0;
}

/** The model id to use, overridable via ANTHROPIC_MODEL. */
export function getModel(): string {
  const model = process.env.ANTHROPIC_MODEL;
  return typeof model === "string" && model.trim().length > 0
    ? model.trim()
    : DEFAULT_MODEL;
}

let cachedClient: Anthropic | null = null;

async function getClient(): Promise<Anthropic> {
  if (cachedClient) return cachedClient;

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (typeof apiKey !== "string" || apiKey.trim().length === 0) {
    throw new Error(
      "ANTHROPIC_API_KEY is not set; live AI features are unavailable.",
    );
  }

  // Lazy import so the module compiles and loads without the SDK key present.
  const mod = await import("@anthropic-ai/sdk");
  const AnthropicCtor = mod.default;
  cachedClient = new AnthropicCtor({ apiKey });
  return cachedClient;
}

/** Concatenate all text content blocks from a Claude message response. */
function extractText(content: Anthropic.Messages.ContentBlock[]): string {
  let out = "";
  for (const block of content) {
    if (block.type === "text") {
      out += block.text;
    }
  }
  return out;
}

/**
 * Extract the first balanced `{...}` JSON object from a string. Handles braces
 * nested inside string literals (and escapes) so we don't stop early on a `}`
 * that lives inside a quoted value.
 */
function extractFirstJsonObject(text: string): string | null {
  const start = text.indexOf("{");
  if (start === -1) return null;

  let depth = 0;
  let inString = false;
  let escaped = false;

  for (let i = start; i < text.length; i++) {
    const ch = text[i];

    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }

    if (ch === '"') {
      inString = true;
    } else if (ch === "{") {
      depth++;
    } else if (ch === "}") {
      depth--;
      if (depth === 0) {
        return text.slice(start, i + 1);
      }
    }
  }

  return null;
}

/**
 * Ask Claude a question and parse a single JSON object out of its reply.
 *
 * The caller's prompt is responsible for instructing JSON-only output. We then
 * pull the first balanced `{...}` block from the text content and `JSON.parse`
 * it. Throws on any failure (no key, API error, no JSON, bad JSON) so callers
 * can fall back to non-AI heuristics.
 */
export async function askClaudeJSON<T>(system: string, user: string): Promise<T> {
  const client = await getClient();

  const response = await client.messages.create({
    model: getModel(),
    max_tokens: 1500,
    system,
    messages: [{ role: "user", content: user }],
  });

  const text = extractText(response.content);
  const jsonBlock = extractFirstJsonObject(text);
  if (jsonBlock === null) {
    throw new Error("Claude response did not contain a JSON object.");
  }

  return JSON.parse(jsonBlock) as T;
}
