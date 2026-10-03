import "server-only";
import { z } from "zod";

export const DEFAULT_DETECT_URL = "http://localhost:8000";
export const DETECT_TIMEOUT_MS = 5_000;

const detectResponseSchema = z.object({
  language: z.string(),
});

export interface DetectionClient {
  /**
   * Detects the language of `text` via the language-detection service. Returns
   * an ISO language code, or null (never throws, except on abort) when the
   * service is unavailable or refuses to guess: detection failure must never
   * fail the transliteration itself.
   */
  detect(text: string, signal?: AbortSignal): Promise<string | null>;
}

export interface DetectionClientOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

export function createDetectionClient(
  options: DetectionClientOptions = {},
): DetectionClient {
  const baseUrl = (
    options.baseUrl ??
    process.env.DETECT_API_URL ??
    DEFAULT_DETECT_URL
  ).replace(/\/+$/, "");
  const fetchImpl = options.fetchImpl ?? fetch;
  const timeoutMs = options.timeoutMs ?? DETECT_TIMEOUT_MS;

  async function detect(
    text: string,
    signal?: AbortSignal,
  ): Promise<string | null> {
    if (text.trim() === "") return null;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const onOuterAbort = () => controller.abort();
    signal?.addEventListener("abort", onOuterAbort);
    try {
      const response = await fetchImpl(`${baseUrl}/v1/detect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
        signal: controller.signal,
      });
      if (!response.ok) return null;
      const parsed = detectResponseSchema.safeParse(await response.json());
      if (!parsed.success) return null;
      const language = parsed.data.language.trim();
      return language === "" ? null : language;
    } catch (error) {
      if (signal?.aborted) throw error;
      console.error("[detect] unavailable:", error);
      return null;
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener("abort", onOuterAbort);
    }
  }

  return { detect };
}

let client: DetectionClient | null = null;

export function detectionClient(): DetectionClient {
  client ??= createDetectionClient();
  return client;
}
