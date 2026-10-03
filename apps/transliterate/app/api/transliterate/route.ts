import { type NextRequest, NextResponse } from "next/server";
import { languageLabel } from "@/lib/languages";
import { detectionClient } from "@qzl/ui/lib/server/detection-client";
import { transliterateClient } from "@/lib/server/transliterate-client";
import {
  AUTO_LANGUAGE,
  type TransliterateRequestBody,
  transliterateRequestBodySchema,
} from "@/lib/transliterate-contract";

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
  const parsed = transliterateRequestBodySchema.safeParse(json);
  if (!parsed.success) {
    return failure(400, "Invalid request.");
  }
  const body: TransliterateRequestBody = parsed.data;
  if (body.text.trim() === "") {
    return failure(400, "Text is empty.");
  }

  try {
    const client = transliterateClient();
    let language = body.language;
    let detected: string | null = null;

    if (language.trim().toLowerCase() === AUTO_LANGUAGE) {
      detected = await detectionClient().detect(body.text, request.signal);
      if (detected === null) {
        return failure(
          422,
          "Could not detect the language. Pick one manually.",
          "detection_failed",
        );
      }
      language = detected;
    }

    const lines = await client.transliterate(
      body.text,
      language,
      request.signal,
    );
    if (lines === null) {
      const isAuto = body.language.trim().toLowerCase() === AUTO_LANGUAGE;
      if (isAuto) {
        return failure(
          422,
          `Transliteration is not supported for ${languageLabel(language)} yet.`,
          "unsupported_language",
        );
      }
      return failure(
        422,
        "Transliteration failed. The service may be unavailable.",
        "transliteration_failed",
      );
    }

    const response: Record<string, unknown> = {
      language,
      lines,
    };
    if (detected !== null) response.detected = detected;
    return NextResponse.json(response);
  } catch (error) {
    if (request.signal.aborted) {
      return failure(499, "Request aborted.");
    }
    console.error("[transliterate] unexpected failure:", error);
    return failure(500, "Transliteration failed.");
  }
}
