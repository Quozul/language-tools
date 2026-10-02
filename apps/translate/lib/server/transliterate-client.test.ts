import { describe, expect, it, vi } from "vitest";
import { createTransliterateClient } from "./transliterate-client";

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
  });
}

const capabilities = { languages: ["ja"] };

const compactResponse = {
  language: "ja",
  tokens: [
    {
      surface: "東京",
      romaji: "tōkyō",
      ruby: [{ base: "東京", text: "とうきょう", scope: "group" }],
      join_with_previous: false,
    },
    {
      surface: "は",
      romaji: "wa",
      ruby: [],
      join_with_previous: false,
    },
  ],
};

function clientWith(fetchImpl: typeof fetch) {
  return createTransliterateClient({
    baseUrl: "http://transliterate.test",
    fetchImpl,
  });
}

describe("createTransliterateClient", () => {
  it("annotates supported languages in compact mode and maps tokens", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(jsonResponse(capabilities))
      .mockResolvedValueOnce(jsonResponse(compactResponse));
    const result = await clientWith(fetchImpl).transliterate(
      "東京は",
      "ja",
      undefined,
    );
    expect(result).not.toBeNull();
    expect(result?.language).toBe("ja");
    expect(result?.lines[0]?.[0]).toEqual({
      surface: "東京",
      romaji: "tōkyō",
      ruby: [{ base: "東京", text: "とうきょう", scope: "group" }],
      joinWithPrevious: false,
    });
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://transliterate.test/v1/capabilities",
      expect.objectContaining({ signal: undefined }),
    );
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://transliterate.test/v1/annotate",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          text: "東京は",
          language: "ja",
          detail: "compact",
        }),
      }),
    );
  });

  it("annotates each line separately so line breaks survive", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(jsonResponse(capabilities))
      .mockResolvedValueOnce(jsonResponse(compactResponse))
      .mockResolvedValueOnce(jsonResponse({ language: "ja", tokens: [] }));
    const result = await clientWith(fetchImpl).transliterate(
      "東京は\n\n",
      "ja",
      undefined,
    );
    expect(result?.lines).toHaveLength(3);
    expect(result?.lines[0]?.[0]?.surface).toBe("東京");
    expect(result?.lines[1]).toEqual([]);
    expect(result?.lines[2]).toEqual([]);
    // Blank lines never reach the service.
    expect(fetchImpl).toHaveBeenCalledTimes(2);
    expect(fetchImpl).toHaveBeenNthCalledWith(
      2,
      "http://transliterate.test/v1/annotate",
      expect.objectContaining({
        body: JSON.stringify({
          text: "東京は",
          language: "ja",
          detail: "compact",
        }),
      }),
    );
  });

  it("skips unsupported languages without calling annotate", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(jsonResponse(capabilities));
    const result = await clientWith(fetchImpl).transliterate(
      "hello",
      "fr",
      undefined,
    );
    expect(result).toBeNull();
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it("returns null when the service is unreachable", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockRejectedValue(new TypeError("fetch failed"));
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(
      await clientWith(fetchImpl).transliterate("東京", "ja", undefined),
    ).toBeNull();
    spy.mockRestore();
  });

  it("returns null when annotate responds with an error status", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(jsonResponse(capabilities))
      .mockResolvedValue(new Response(null, { status: 500 }));
    expect(
      await clientWith(fetchImpl).transliterate("東京", "ja", undefined),
    ).toBeNull();
  });

  it("caches capabilities across requests", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(jsonResponse(capabilities))
      .mockResolvedValue(jsonResponse(compactResponse));
    const client = clientWith(fetchImpl);
    await client.transliterate("東京は", "ja", undefined);
    await client.transliterate("東京は", "ja", undefined);
    expect(fetchImpl).toHaveBeenCalledTimes(3);
  });
});
