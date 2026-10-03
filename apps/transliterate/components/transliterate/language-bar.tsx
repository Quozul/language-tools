"use client";

import { LanguagePicker } from "@/components/language-picker";
import {
  useTransliterateActions,
  useTransliterateSettings,
} from "./transliterate-context";
import { TransliterateSettings } from "./transliterate-settings";
import { detectLanguageLabel } from "./use-transliterate";

export function LanguageBar() {
  const { language, languages, detectedLanguage } = useTransliterateSettings();
  const { chooseLanguage } = useTransliterateActions();

  return (
    <div className="flex items-center gap-2 border-b px-3 py-2">
      <div className="min-w-0 flex-1">
        <LanguagePicker
          selected={language}
          languages={languages}
          onSelect={chooseLanguage}
          ariaLabel="Language"
          detectLabel={detectLanguageLabel(detectedLanguage)}
        />
      </div>
      <TransliterateSettings />
    </div>
  );
}
