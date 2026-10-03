import { AUTO_LANGUAGE } from "./transliterate-contract";

export type ReadingStyle = "romaji" | "furigana" | "both";

export const READING_STYLES: ReadingStyle[] = ["romaji", "furigana", "both"];

export const READING_STYLE_LABELS: Record<ReadingStyle, string> = {
  romaji: "Romaji",
  furigana: "Furigana",
  both: "Both",
};

export function isReadingStyle(value: unknown): value is ReadingStyle {
  return (
    typeof value === "string" && READING_STYLES.includes(value as ReadingStyle)
  );
}

const PREFERENCES_KEY = "qzl.transliterate.preferences.v1";

export interface Preferences {
  language: string;
  style: ReadingStyle;
}

export interface StorageReader {
  getItem(key: string): string | null;
}

export interface StorageWriter {
  setItem(key: string, value: string): void;
}

interface StoredPreferences {
  language?: unknown;
  style?: unknown;
}

function fallbackPreferences(): Preferences {
  return { language: AUTO_LANGUAGE, style: "both" };
}

export function parseTransliteratePreferences(value: unknown): Preferences {
  const fallback = fallbackPreferences();
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return fallback;
  }
  const stored = value as StoredPreferences;

  const language =
    typeof stored.language === "string" && stored.language.trim() !== ""
      ? stored.language.trim()
      : fallback.language;
  const style = isReadingStyle(stored.style) ? stored.style : fallback.style;

  return { language, style };
}

export function loadTransliteratePreferences(
  storage: StorageReader | null,
): Preferences {
  if (!storage) return fallbackPreferences();
  try {
    const stored = storage.getItem(PREFERENCES_KEY);
    if (!stored) return fallbackPreferences();
    return parseTransliteratePreferences(JSON.parse(stored));
  } catch {
    return fallbackPreferences();
  }
}

export function saveTransliteratePreferences(
  storage: StorageWriter | null,
  preferences: Preferences,
): void {
  if (!storage) return;
  const stored: StoredPreferences = {
    language: preferences.language,
    style: preferences.style,
  };
  try {
    storage.setItem(PREFERENCES_KEY, JSON.stringify(stored));
  } catch {}
}

export function browserStorage(): (StorageReader & StorageWriter) | null {
  try {
    if (typeof window === "undefined") return null;
    return window.localStorage;
  } catch {
    return null;
  }
}
