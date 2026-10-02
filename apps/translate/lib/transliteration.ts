import { z } from "zod";

/**
 * Transliteration data (furigana ruby and romanization) for a translated text,
 * produced by the qzl-transliterate service when it supports the target
 * language. Tokens arrive pre-segmented; the client renders ruby over the
 * surface text and joins romanization with `joinWithPrevious`.
 */

export const transliterationRubySchema = z.object({
  base: z.string(),
  text: z.string(),
  scope: z.string(),
});

export const transliterationTokenSchema = z.object({
  surface: z.string(),
  romaji: z.string(),
  ruby: z.array(transliterationRubySchema),
  joinWithPrevious: z.boolean(),
});

export const transliterationSchema = z.object({
  language: z.string(),
  /** One token list per source line: the tokenizer drops line breaks. */
  lines: z.array(z.array(transliterationTokenSchema)),
});

export type TransliterationRubySegment = z.infer<
  typeof transliterationRubySchema
>;
export type TransliterationToken = z.infer<typeof transliterationTokenSchema>;
export type Transliteration = z.infer<typeof transliterationSchema>;

/**
 * Joins the romanization of consecutive tokens in one line: a token that does
 * not join its predecessor starts a new word and gets the separator.
 */
export function joinRomaji(
  tokens: readonly TransliterationToken[],
  separator = " ",
): string {
  let out = "";
  for (const token of tokens) {
    if (out !== "" && !token.joinWithPrevious) out += separator;
    out += token.romaji;
  }
  return out;
}
