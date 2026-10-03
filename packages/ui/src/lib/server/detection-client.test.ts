import { describe, expect, it, vi } from "vitest";
import { createDetectionClient } from "./detection-client";

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
  });
}

function clientWith(fetchImpl: typeof fetch) {
  return createDetectionClient({
    baseUrl: "http://detect.test",
    fetchImpl,
  });
}

describe("createDetectionClient", () => {
  it("returns the detected language code", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse({ language: "es", confidence: 0.98 }));
    const result = await clientWith(fetchImpl).detect("hola mundo", undefined);
    expect(result).toBe("es");
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://detect.test/v1/detect",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ text: "hola mundo" }),
      }),
    );
  });

  it("skips the service for blank text", async () => {
    const fetchImpl = vi.fn<typeof fetch>();
    expect(await clientWith(fetchImpl).detect("   ", undefined)).toBeNull();
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("returns null when the service responds with an error status", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response(null, { status: 422 }));
    expect(await clientWith(fetchImpl).detect("...", undefined)).toBeNull();
  });

  it("returns null on a malformed response", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse({ tongue: "es" }));
    expect(await clientWith(fetchImpl).detect("hola", undefined)).toBeNull();
  });

  it("returns null when the service is unreachable", async () => {
    const fetchImpl = vi
      .fn<typeof fetch>()
      .mockRejectedValue(new TypeError("fetch failed"));
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(await clientWith(fetchImpl).detect("hola", undefined)).toBeNull();
    spy.mockRestore();
  });

  it("rethrows when the caller aborts", async () => {
    const controller = new AbortController();
    const fetchImpl = vi.fn<typeof fetch>(() => {
      controller.abort();
      return Promise.reject(new DOMException("aborted", "AbortError"));
    });
    await expect(
      clientWith(fetchImpl).detect("hola", controller.signal),
    ).rejects.toSatisfy(
      (error: unknown) =>
        error instanceof DOMException && error.name === "AbortError",
    );
  });
});
