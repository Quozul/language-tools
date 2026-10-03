import { MAX_TEXT_LENGTH } from "./transliterate-contract";

const CONTROL_CHARACTERS = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/;

export function normalizeTransliterateText(text: string): string {
  return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
}

export function countTransliterateCharacters(text: string): number {
  return [...text].length;
}

export type TransliterateTextIssueCode = "too_long" | "control_characters";

export interface TransliterateTextIssue {
  code: TransliterateTextIssueCode;
  message: string;
}

export function validateTransliterateInput(
  text: string,
): TransliterateTextIssue | null {
  if (countTransliterateCharacters(text) > MAX_TEXT_LENGTH) {
    return {
      code: "too_long",
      message: `Please shorten your text to ${MAX_TEXT_LENGTH.toLocaleString("en-US")} characters or fewer.`,
    };
  }
  if (CONTROL_CHARACTERS.test(text)) {
    return {
      code: "control_characters",
      message: "Text contains unsupported control characters.",
    };
  }
  return null;
}

export function displayedCharacterCount(raw: string): number {
  return countTransliterateCharacters(normalizeTransliterateText(raw));
}
