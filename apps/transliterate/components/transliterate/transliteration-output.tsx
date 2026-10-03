"use client";

import { CopyIcon } from "lucide-react";
import { Button } from "@qzl/ui/components/button";
import { languageLabel } from "@/lib/languages";
import { joinRomaji, type TransliterationToken } from "@qzl/ui/lib/transliteration";
import {
  useTransliterateActions,
  useTransliterateSession,
  useTransliterateSettings,
} from "./transliterate-context";
import { TransliteratedText } from "@qzl/ui/components/transliterated-text";
import { useCopyFeedback } from "@qzl/ui/hooks/use-clipboard-feedback";

function joinSurface(lines: readonly (readonly TransliterationToken[])[]) {
  return lines
    .map((tokens) => {
      let out = "";
      for (const token of tokens) {
        if (out !== "" && !token.joinWithPrevious) out += " ";
        out += token.surface;
      }
      return out;
    })
    .join("\n");
}

export function TransliterationOutput() {
  const { result } = useTransliterateSession();
  const { request } = useTransliterateSession();
  const { style } = useTransliterateSettings();
  const { retry } = useTransliterateActions();
  const { copy } = useCopyFeedback();

  const busy = request.status === "waiting" || request.status === "loading";
  const errorMessage = request.status === "error" ? request.message : "";
  const hasResult = result !== null;
  const showRuby = style !== "romaji";
  const showRomaji = style !== "furigana";
  const resultLabel = result === null ? "" : languageLabel(result.language);

  const copyText =
    result === null
      ? ""
      : style === "romaji"
        ? result.lines.map((line) => joinRomaji(line)).join("\n")
        : joinSurface(result.lines);

  return (
    <section
      className="min-h-0 overflow-y-auto pt-3 md:pt-0"
      aria-label="Transliteration"
      aria-busy={busy}
    >
      {hasResult && (
        <>
          <div aria-label={`${resultLabel} transliteration`}>
            <TransliteratedText
              lines={result.lines}
              lang={result.language}
              showRuby={showRuby}
              showRomaji={showRomaji}
            />
          </div>
          <div className="mt-3 flex justify-end">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Copy"
              title="Copy"
              onClick={() => copy(copyText)}
            >
              <CopyIcon />
            </Button>
          </div>
        </>
      )}

      {!hasResult && (
        <p className="text-2xl wrap-break-word text-muted-foreground">
          Transliteration
          {busy && <BouncingDots />}
        </p>
      )}

      {hasResult && busy && (
        <div className="text-muted-foreground">
          <BouncingDots />
        </div>
      )}

      {errorMessage !== "" && (
        <div className="mt-3 text-[0.9375rem] text-destructive" role="alert">
          <p>{errorMessage}</p>
          <Button
            type="button"
            variant="link"
            className="-ml-2"
            onClick={retry}
          >
            Try again
          </Button>
        </div>
      )}
    </section>
  );
}

function BouncingDots() {
  return (
    <span
      aria-hidden="true"
      className="ml-1 inline-flex items-center gap-1 align-middle"
    >
      <span className="size-1 animate-dot-bounce rounded-full bg-current [animation-delay:0ms]" />
      <span className="size-1 animate-dot-bounce rounded-full bg-current [animation-delay:150ms]" />
      <span className="size-1 animate-dot-bounce rounded-full bg-current [animation-delay:300ms]" />
    </span>
  );
}
