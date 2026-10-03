"use client";

import { ClipboardPasteIcon, XIcon } from "lucide-react";
import { type ChangeEvent, useRef } from "react";
import { Button } from "@qzl/ui/components/button";
import { Textarea } from "@qzl/ui/components/textarea";
import { MAX_TEXT_LENGTH } from "@/lib/transliterate-contract";
import { displayedCharacterCount } from "@/lib/transliterate-text";
import {
  useTransliterateActions,
  useTransliterateEditor,
} from "./transliterate-context";
import { usePasteFeedback } from "@qzl/ui/hooks/use-clipboard-feedback";

const LIMIT_LABEL = MAX_TEXT_LENGTH.toLocaleString("en-US");

export function SourceEditor() {
  const { text } = useTransliterateEditor();
  const { changeText, pasteText, clearText } = useTransliterateActions();
  const { paste } = usePasteFeedback(pasteText);
  const input = useRef<HTMLTextAreaElement>(null);
  const pendingPaste = useRef(false);

  const charCount = displayedCharacterCount(text);
  const tooLong = charCount > MAX_TEXT_LENGTH;
  const showCount = charCount > MAX_TEXT_LENGTH - 1000;
  const hasText = text.trim() !== "";

  const handleTextChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    if (pendingPaste.current) {
      pendingPaste.current = false;
      pasteText(event.target.value);
    } else {
      changeText(event.target.value);
    }
  };

  const handleNativePaste = () => {
    pendingPaste.current = true;
  };

  const handleClear = () => {
    clearText();
    input.current?.focus();
  };

  const handlePaste = () => {
    paste();
    input.current?.focus();
  };

  return (
    <section
      className="relative flex min-h-0 flex-col"
      aria-label="Source text"
    >
      {hasText && (
        <div className="absolute top-1 right-1 z-10 flex items-center text-muted-foreground">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Clear"
            title="Clear"
            onClick={handleClear}
          >
            <XIcon />
          </Button>
        </div>
      )}
      <Textarea
        id="source"
        ref={input}
        autoFocus
        dir="auto"
        placeholder="Enter text"
        aria-label="Text to transliterate"
        aria-invalid={tooLong || undefined}
        aria-describedby={showCount ? "source-limit" : undefined}
        className="min-h-40 flex-1 resize-none overflow-y-auto rounded-lg border-0 bg-transparent pl-2 pr-10 text-2xl md:text-2xl field-sizing-fixed focus-visible:ring-3 focus-visible:ring-inset"
        value={text}
        onChange={handleTextChange}
        onPaste={handleNativePaste}
      />
      {!hasText && (
        <Button
          type="button"
          variant="outline"
          aria-label="Paste from clipboard"
          title="Paste from clipboard"
          onClick={handlePaste}
          className="mt-2 w-full text-base md:hidden"
        >
          <ClipboardPasteIcon />
          Paste from clipboard
        </Button>
      )}
      {showCount && (
        <span
          id="source-limit"
          className={
            tooLong
              ? "self-end text-xs text-destructive"
              : "self-end text-xs text-muted-foreground"
          }
        >
          {charCount.toLocaleString("en-US")} / {LIMIT_LABEL}
        </span>
      )}
    </section>
  );
}
