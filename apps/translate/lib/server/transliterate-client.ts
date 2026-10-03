import "server-only";
import { z } from "zod";
import type { Transliteration } from "@qzl/ui/lib/transliteration";

export const DEFAULT_TRANSLITERATE_URL = "http://localhost:8000";
export const CAPABILITIES_TTL_MS = 5 * 60_000;
export const TRANSLITERATE_TIMEOUT_MS = 10_000;

const capabilitiesResponseSchema = z.object({
  languages: z.array(z.string()),
});

const remoteRubySchema = z.object({
  base: z.string(),
  text: z.string(),
  scope: z.string(),
});

const remoteCompactTokenSchema = z.object({
  surface: z.string(),
  romaji: z.string(),
  ruby: z.array(remoteRubySchema),
  join_with_previous: z.boolean(),
});

const compactAnnotateResponseSchema = z.object({
  language: z.string(),
  tokens: z.array(remoteCompactTokenSchema),
});

export interface TransliterateClient {
  /**
   * Annotates `text` in `language` when the service supports it. Returns null
   * (never throws) when the language is unsupported or the service fails:
   * transliteration is an enhancement, never a requirement for translation.
   */
  transliterate(
    text: string,
    language: string,
    signal?: AbortSignal,
  ): Promise<Transliteration | null>;
}

export interface TransliterateClientOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
  now?: () => number;
  capabilitiesTtlMs?: number;
  timeoutMs?: number;
}

function normalizeLanguage(language: string): string {
  return language.trim().toLowerCase();
}

export function createTransliterateClient(
  options: TransliterateClientOptions = {},
): TransliterateClient {
  const baseUrl = (
    options.baseUrl ??
    process.env.TRANSLITERATE_API_URL ??
    DEFAULT_TRANSLITERATE_URL
  ).replace(/\/+$/, "");
  const fetchImpl = options.fetchImpl ?? fetch;
  const now = options.now ?? Date.now;
  const ttl = options.capabilitiesTtlMs ?? CAPABILITIES_TTL_MS;
  const timeoutMs = options.timeoutMs ?? TRANSLITERATE_TIMEOUT_MS;

  let capabilities: { at: number; languages: Set<string> } | null = null;

  async function supportedLanguages(
    signal?: AbortSignal,
  ): Promise<Set<string> | null> {
    if (capabilities !== null && now() - capabilities.at < ttl) {
      return capabilities.languages;
    }
    try {
      const response = await fetchImpl(`${baseUrl}/v1/capabilities`, {
        signal,
        cache: "no-store",
      });
      if (!response.ok) return null;
      const parsed = capabilitiesResponseSchema.safeParse(
        await response.json(),
      );
      if (!parsed.success) return null;
      const languages = new Set(parsed.data.languages.map(normalizeLanguage));
      capabilities = { at: now(), languages };
      return languages;
    } catch (error) {
      if (signal?.aborted) throw error;
      return null;
    }
  }

  async function annotateLine(
    text: string,
    language: string,
    signal?: AbortSignal,
  ): Promise<Transliteration["lines"][number] | null> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const onOuterAbort = () => controller.abort();
    signal?.addEventListener("abort", onOuterAbort);
    try {
      const response = await fetchImpl(`${baseUrl}/v1/annotate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language, detail: "compact" }),
        signal: controller.signal,
      });
      if (!response.ok) return null;
      const parsed = compactAnnotateResponseSchema.safeParse(
        await response.json(),
      );
      if (!parsed.success) return null;
      return parsed.data.tokens.map((token) => ({
        surface: token.surface,
        romaji: token.romaji,
        ruby: token.ruby,
        joinWithPrevious: token.join_with_previous,
      }));
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener("abort", onOuterAbort);
    }
  }

  async function transliterate(
    text: string,
    language: string,
    signal?: AbortSignal,
  ): Promise<Transliteration | null> {
    if (text.trim() === "") return null;
    try {
      const languages = await supportedLanguages(signal);
      if (languages === null || !languages.has(normalizeLanguage(language))) {
        return null;
      }
      // The tokenizer drops whitespace, so line breaks are lost inside one
      // request: annotate line by line and keep the breaks in the structure.
      const lines = text.split(/\r\n|\r|\n/);
      const annotated: Transliteration["lines"] = [];
      for (const line of lines) {
        if (line.trim() === "") {
          annotated.push([]);
          continue;
        }
        const tokens = await annotateLine(line, language, signal);
        if (tokens === null) return null;
        annotated.push(tokens);
      }
      return { language, lines: annotated };
    } catch (error) {
      if (signal?.aborted) throw error;
      console.error("[transliterate] unavailable:", error);
      return null;
    }
  }

  return { transliterate };
}

let client: TransliterateClient | null = null;

export function transliterateClient(): TransliterateClient {
  client ??= createTransliterateClient();
  return client;
}
