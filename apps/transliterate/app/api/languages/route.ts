import { NextResponse } from "next/server";
import { transliterateClient } from "@/lib/server/transliterate-client";

export const runtime = "nodejs";

/** Languages the transliterate service supports, per its capabilities. */
export async function GET(): Promise<NextResponse> {
  const languages = await transliterateClient().supportedLanguages();
  if (languages === null) {
    return NextResponse.json(
      { error: "Transliteration service unavailable." },
      { status: 503 },
    );
  }
  return NextResponse.json({ languages });
}
