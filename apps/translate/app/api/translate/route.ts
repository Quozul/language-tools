import { type NextRequest, NextResponse } from "next/server";
import { ApiError } from "@/lib/server/errors";
import { createCompletionFromEnvironment } from "@/lib/server/openai-adapter";
import { translateRequest } from "@/lib/server/translation-service";
import { transliterateClient } from "@/lib/server/transliterate-client";
import {
  type TranslationResponseBody,
  translationRequestBodySchema,
} from "@/lib/translation-contract";

export const runtime = "nodejs";

function failure(status: number, message: string, code?: string): NextResponse {
  return NextResponse.json({ error: message, code }, { status });
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  let json: unknown;
  try {
    json = await request.json();
  } catch {
    return failure(400, "Invalid JSON body.");
  }
  const parsed = translationRequestBodySchema.safeParse(json);
  if (!parsed.success) {
    return failure(400, "Invalid request.");
  }

  try {
    const completion = createCompletionFromEnvironment();
    const outcome = await translateRequest(parsed.data, {
      completion,
      signal: request.signal,
    });
    const body: TranslationResponseBody = {
      translation: outcome.translation,
      family: outcome.family.id,
      preset: outcome.preset,
      cached: outcome.fromCache,
      durationMs: outcome.durationMs,
    };
    // Transliteration is an enhancement: the service may be down or lack the
    // language, and that must never fail the translation itself.
    try {
      const transliteration = await transliterateClient().transliterate(
        outcome.translation,
        parsed.data.target,
        request.signal,
      );
      if (transliteration !== null) body.transliteration = transliteration;
    } catch (error) {
      if (request.signal.aborted) throw error;
      console.error("[translate] transliteration failed:", error);
    }
    return NextResponse.json(body);
  } catch (error) {
    if (request.signal.aborted) {
      return failure(499, "Request aborted.");
    }
    if (error instanceof ApiError) {
      console.error(`[translate] ${error.code}:`, error.cause ?? error);
      return failure(error.status, error.message, error.code);
    }
    console.error("[translate] unexpected failure:", error);
    return failure(500, "Translation failed.");
  }
}
