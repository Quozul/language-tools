import { z } from "zod";
import { transliterationSchema } from "@qzl/ui/lib/transliteration";

/** Keep in sync with MAX_TEXT_LENGTH of the qzl-transliterate service. */
export const MAX_TEXT_LENGTH = 5000;

/** Pseudo-language for the language combobox: let the detector decide. */
export const AUTO_LANGUAGE = "auto";

export const transliterateRequestBodySchema = z.object({
  text: z.string(),
  language: z.string().min(1),
});

export type TransliterateRequestBody = z.infer<
  typeof transliterateRequestBodySchema
>;

export const transliterateResponseBodySchema = transliterationSchema.extend({
  detected: z.string().optional(),
});

export type TransliterateResponseBody = z.infer<
  typeof transliterateResponseBodySchema
>;
