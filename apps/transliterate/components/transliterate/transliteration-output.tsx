"use client";

import { Button } from "@qzl/ui/components/button";
import { languageLabel } from "@/lib/languages";
import {
  useTransliterateActions,
  useTransliterateSession,
  useTransliterateSettings,
} from "./transliterate-context";
import { TransliteratedText } from "@qzl/ui/components/transliterated-text";

export function TransliterationOutput() {
  const { result } = useTransliterateSession();
  const { request } = useTransliterateSession();
  const { style } = useTransliterateSettings();
  const { retry } = useTransliterateActions();

  const busy = request.status === "waiting" || request.status === "loading";
  const errorMessage = request.status === "error" ? request.message : "";
  const hasResult = result !== null;
  const showRuby = style !== "romaji";
  const showRomaji = style !== "furigana";
  const resultLabel = result === null ? "" : languageLabel(result.language);

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
