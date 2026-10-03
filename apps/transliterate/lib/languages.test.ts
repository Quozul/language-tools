import { describe, expect, it } from "vitest";
import { languageLabel, matchesLanguageCode } from "./languages";

describe("languageLabel", () => {
  it("names known languages", () => {
    expect(languageLabel("ja")).toBe("Japanese");
    expect(languageLabel("JA")).toBe("Japanese");
  });

  it("falls back to the code for unknown languages", () => {
    expect(languageLabel("ko")).toBe("ko");
  });
});

describe("matchesLanguageCode", () => {
  it("matches by name, code, and empty query", () => {
    expect(matchesLanguageCode("ja", "")).toBe(true);
    expect(matchesLanguageCode("ja", "jap")).toBe(true);
    expect(matchesLanguageCode("ja", "ja")).toBe(true);
    expect(matchesLanguageCode("ja", "junk")).toBe(false);
  });
});
