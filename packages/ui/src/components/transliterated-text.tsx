"use client";

import { joinRomaji, type TransliterationToken } from "@qzl/ui/lib/transliteration";

/**
 * Ruby segments only cover annotated runs of the surface text, so the plain
 * parts (kana, punctuation) between segments are recovered as-is.
 */
function tokenNodes(token: TransliterationToken) {
  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  for (const [index, segment] of token.ruby.entries()) {
    const at = token.surface.indexOf(segment.base, cursor);
    if (at === -1) continue;
    if (at > cursor) nodes.push(token.surface.slice(cursor, at));
    nodes.push(
      segment.text !== "" && segment.text !== segment.base ? (
        <ruby key={`${index}-${segment.base}`}>
          {segment.base}
          <rt>{segment.text}</rt>
        </ruby>
      ) : (
        segment.base
      ),
    );
    cursor = at + segment.base.length;
  }
  if (cursor < token.surface.length) nodes.push(token.surface.slice(cursor));
  return nodes;
}

export function TransliteratedText({
  lines,
  lang,
  showRuby = true,
  showRomaji = true,
}: {
  lines: readonly (readonly TransliterationToken[])[];
  lang?: string;
  showRuby?: boolean;
  showRomaji?: boolean;
}) {
  const romaji = lines.map((line) => joinRomaji(line)).join("\n");
  if (!showRuby) {
    return (
      <p
        dir="auto"
        lang={lang}
        className="text-2xl leading-normal wrap-break-word whitespace-pre-wrap"
      >
        {romaji}
      </p>
    );
  }
  return (
    <>
      <p
        dir="auto"
        lang={lang}
        className="text-2xl leading-loose wrap-break-word whitespace-pre-wrap"
      >
        {lines.map((tokens, line) => (
          // Tokens are replaced wholesale with each result; position is identity.
          // biome-ignore lint/suspicious/noArrayIndexKey: stable per rendered result
          <span key={line}>
            {line > 0 ? "\n" : null}
            {tokens.map((token, index) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: stable per rendered result
              <span key={index}>
                {index > 0 && !token.joinWithPrevious ? " " : null}
                {tokenNodes(token)}
              </span>
            ))}
          </span>
        ))}
      </p>
      {showRomaji && romaji.trim() !== "" && (
        <p className="mt-2 text-sm wrap-break-word whitespace-pre-wrap text-muted-foreground">
          {romaji}
        </p>
      )}
    </>
  );
}
