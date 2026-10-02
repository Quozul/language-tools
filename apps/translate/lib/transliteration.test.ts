import { describe, expect, it } from "vitest";
import { joinRomaji, type TransliterationToken } from "./transliteration";

function token(romaji: string, joinWithPrevious = false): TransliterationToken {
  return { surface: "", romaji, ruby: [], joinWithPrevious };
}

describe("joinRomaji", () => {
  it("separates words unless the token joins its predecessor", () => {
    expect(
      joinRomaji([
        token("tōkyō"),
        token("wa"),
        token("ōkii"),
        token("desu", true),
      ]),
    ).toBe("tōkyō wa ōkiidesu");
  });

  it("returns an empty string for no tokens", () => {
    expect(joinRomaji([])).toBe("");
  });
});
