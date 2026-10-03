import { describe, expect, it } from "vitest";
import {
  loadTransliteratePreferences,
  parseTransliteratePreferences,
  type StorageReader,
  type StorageWriter,
  saveTransliteratePreferences,
} from "./preferences";

function memoryStorage(initial: Record<string, string> = {}) {
  const data = new Map(Object.entries(initial));
  const storage: StorageReader & StorageWriter = {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => {
      data.set(key, value);
    },
  };
  return { storage, data };
}

describe("parseTransliteratePreferences", () => {
  it("falls back for missing or malformed values", () => {
    expect(parseTransliteratePreferences(null)).toEqual({
      language: "auto",
      style: "both",
    });
    expect(
      parseTransliteratePreferences({ language: "", style: "nope" }),
    ).toEqual({ language: "auto", style: "both" });
    expect(parseTransliteratePreferences([1, 2])).toEqual({
      language: "auto",
      style: "both",
    });
  });

  it("keeps valid stored values", () => {
    expect(
      parseTransliteratePreferences({ language: "ja", style: "furigana" }),
    ).toEqual({ language: "ja", style: "furigana" });
    expect(
      parseTransliteratePreferences({ language: "auto", style: "romaji" }),
    ).toEqual({ language: "auto", style: "romaji" });
  });
});

describe("loadTransliteratePreferences / saveTransliteratePreferences", () => {
  it("round-trips preferences through storage", () => {
    const { storage, data } = memoryStorage();
    saveTransliteratePreferences(storage, {
      language: "ja",
      style: "romaji",
    });
    const key = "qzl.transliterate.preferences.v1";
    expect(JSON.parse(data.get(key) ?? "{}")).toEqual({
      language: "ja",
      style: "romaji",
    });
    expect(loadTransliteratePreferences(storage)).toEqual({
      language: "ja",
      style: "romaji",
    });
  });

  it("falls back on empty or corrupt storage", () => {
    expect(loadTransliteratePreferences(null)).toEqual({
      language: "auto",
      style: "both",
    });
    const { storage } = memoryStorage({
      "qzl.transliterate.preferences.v1": "not json",
    });
    expect(loadTransliteratePreferences(storage)).toEqual({
      language: "auto",
      style: "both",
    });
  });
});
