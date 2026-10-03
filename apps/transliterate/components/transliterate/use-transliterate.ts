"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { languageLabel } from "@/lib/languages";
import {
  browserStorage,
  loadTransliteratePreferences,
  type ReadingStyle,
  saveTransliteratePreferences,
} from "@/lib/preferences";
import {
  AUTO_LANGUAGE,
  type TransliterateResponseBody,
  transliterateResponseBodySchema,
} from "@/lib/transliterate-contract";
import {
  normalizeTransliterateText,
  validateTransliterateInput,
} from "@/lib/transliterate-text";

const DEBOUNCE_MS = 400;

export type RequestState =
  | { status: "idle" }
  | { status: "waiting" }
  | { status: "loading" }
  | { status: "error"; message: string };

export interface TransliterationResult {
  language: string;
  lines: TransliterateResponseBody["lines"];
  detected: string | null;
}

export interface TransliterateSettingsSlice {
  language: string;
  style: ReadingStyle;
  languages: string[];
  detectedLanguage: string | null;
}

export interface TransliterateEditorSlice {
  text: string;
}

export interface TransliterateSessionSlice {
  request: RequestState;
  result: TransliterationResult | null;
}

export interface TransliterateActions {
  changeText: (value: string) => void;
  pasteText: (value: string) => void;
  clearText: () => void;
  chooseLanguage: (code: string) => void;
  changeStyle: (style: ReadingStyle) => void;
  retry: () => void;
}

export function detectLanguageLabel(detected: string | null): string {
  return detected === null
    ? "Detect language"
    : `Detect language (${languageLabel(detected)})`;
}

function errorMessage(error: unknown): string {
  return error instanceof Error && error.message !== ""
    ? error.message
    : "Transliteration failed.";
}

export function useTransliterateController(): {
  settingsSlice: TransliterateSettingsSlice;
  editorSlice: TransliterateEditorSlice;
  sessionSlice: TransliterateSessionSlice;
  actions: TransliterateActions;
} {
  const [hydrated, setHydrated] = useState(false);
  const [text, setText] = useState("");
  const [language, setLanguage] = useState(AUTO_LANGUAGE);
  const [style, setStyle] = useState<ReadingStyle>("both");
  const [languages, setLanguages] = useState<string[]>([]);
  const [request, setRequest] = useState<RequestState>({ status: "idle" });
  const [result, setResult] = useState<TransliterationResult | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);

  useEffect(() => {
    const preferences = loadTransliteratePreferences(browserStorage());
    setLanguage(preferences.language);
    setStyle(preferences.style);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    saveTransliteratePreferences(browserStorage(), { language, style });
  }, [hydrated, language, style]);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/languages")
      .then((response) => (response.ok ? response.json() : null))
      .then((body: unknown) => {
        if (cancelled) return;
        if (
          typeof body === "object" &&
          body !== null &&
          Array.isArray((body as { languages?: unknown }).languages)
        ) {
          setLanguages(
            (body as { languages: unknown[] }).languages.filter(
              (entry): entry is string => typeof entry === "string",
            ),
          );
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: retryNonce exists only to re-trigger this effect
  useEffect(() => {
    if (!hydrated) return;
    const trimmed = normalizeTransliterateText(text);
    if (trimmed === "") {
      setResult(null);
      setRequest({ status: "idle" });
      return;
    }
    const issue = validateTransliterateInput(trimmed);
    if (issue !== null) {
      setRequest({ status: "error", message: issue.message });
      return;
    }
    const controller = new AbortController();
    setRequest({ status: "waiting" });
    const timer = setTimeout(() => {
      setRequest({ status: "loading" });
      fetch("/api/transliterate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: trimmed, language }),
        signal: controller.signal,
      })
        .then(async (response) => {
          if (!response.ok) {
            const body: unknown = await response.json().catch(() => ({}));
            const message =
              typeof (body as { error?: unknown }).error === "string"
                ? (body as { error: string }).error
                : "Transliteration failed.";
            throw new Error(message);
          }
          return response.json();
        })
        .then((body: unknown) => {
          const parsed = transliterateResponseBodySchema.safeParse(body);
          if (!parsed.success) {
            throw new Error("Unexpected response from the server.");
          }
          setResult({
            language: parsed.data.language,
            lines: parsed.data.lines,
            detected: parsed.data.detected ?? null,
          });
          setRequest({ status: "idle" });
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          setRequest({ status: "error", message: errorMessage(error) });
        });
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [hydrated, text, language, retryNonce]);

  const changeText = useCallback((value: string) => setText(value), []);
  const pasteText = useCallback((value: string) => setText(value), []);
  const clearText = useCallback(() => setText(""), []);
  const chooseLanguage = useCallback((code: string) => {
    if (code.trim() === "") return;
    setLanguage(code);
  }, []);
  const changeStyle = useCallback((value: ReadingStyle) => setStyle(value), []);
  const retry = useCallback(() => setRetryNonce((nonce) => nonce + 1), []);

  const detectedLanguage = result?.detected ?? null;

  const settingsSlice = useMemo<TransliterateSettingsSlice>(
    () => ({ language, style, languages, detectedLanguage }),
    [language, style, languages, detectedLanguage],
  );

  const editorSlice = useMemo<TransliterateEditorSlice>(
    () => ({ text }),
    [text],
  );

  const sessionSlice = useMemo<TransliterateSessionSlice>(
    () => ({ request, result }),
    [request, result],
  );

  const actions = useMemo<TransliterateActions>(
    () => ({
      changeText,
      pasteText,
      clearText,
      chooseLanguage,
      changeStyle,
      retry,
    }),
    [changeText, pasteText, clearText, chooseLanguage, changeStyle, retry],
  );

  return { settingsSlice, editorSlice, sessionSlice, actions };
}
