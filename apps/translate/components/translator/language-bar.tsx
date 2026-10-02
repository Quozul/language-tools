"use client";

import { LanguagePicker } from "@/components/language-picker";
import { SwapLanguages } from "@/components/translator/swap-languages";
import { DETECT_SOURCE } from "@/lib/models";
import {
  useTranslatorActions,
  useTranslatorPreferences,
  useTranslatorSession,
} from "./translator-context";
import { TranslatorSettings } from "./translator-settings";
import { detectLanguageLabel } from "./translator-state";

export function LanguageBar() {
  const { source, target, frequent } = useTranslatorPreferences();
  const { detectedLanguage } = useTranslatorSession();
  const { changeSource, chooseLanguage } = useTranslatorActions();

  const detectOption = {
    value: DETECT_SOURCE,
    label: detectLanguageLabel(detectedLanguage),
  };

  return (
    <div className="flex items-center gap-2 border-b px-3 py-2">
      <div className="min-w-0 flex-1">
        <LanguagePicker
          selected={source}
          frequent={frequent}
          onSelect={changeSource}
          ariaLabel="Source language"
          detect={detectOption}
        />
      </div>
      <SwapLanguages />
      <div className="min-w-0 flex-1">
        <LanguagePicker
          selected={target}
          frequent={frequent}
          onSelect={chooseLanguage}
        />
      </div>
      <TranslatorSettings />
    </div>
  );
}
