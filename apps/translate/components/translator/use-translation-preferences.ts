"use client";

import { useCallback, useMemo, useRef } from "react";
import { FREQUENT_LANGUAGE_LIMIT } from "@/lib/languages";
import type { ModelFamilyId, ModelPreset } from "@/lib/models";
import {
  browserStorage,
  getFrequentLanguages,
  loadTranslationPreferences,
  type Preferences,
  saveTranslationPreferences,
} from "@/lib/preferences";

export function usePreferenceStore() {
  const usageRef = useRef<Record<string, number>>({});

  const restore = useCallback((): Preferences => {
    const preferences = loadTranslationPreferences(browserStorage());
    usageRef.current = preferences.usage;
    return preferences;
  }, []);

  const persist = useCallback(
    (fields: {
      target: string;
      source: string;
      family: ModelFamilyId;
      preset: ModelPreset;
      debugInfo: boolean;
    }): void => {
      saveTranslationPreferences(browserStorage(), {
        target: fields.target,
        source: fields.source,
        family: fields.family,
        preset: fields.preset,
        debugInfo: fields.debugInfo,
        usage: usageRef.current,
      });
    },
    [],
  );

  const recordTranslation = useCallback((target: string): string[] => {
    usageRef.current = {
      ...usageRef.current,
      [target]: (usageRef.current[target] ?? 0) + 1,
    };
    return getFrequentLanguages(usageRef.current, FREQUENT_LANGUAGE_LIMIT);
  }, []);

  const frequent = useCallback(
    (): string[] =>
      getFrequentLanguages(usageRef.current, FREQUENT_LANGUAGE_LIMIT),
    [],
  );

  return useMemo(
    () => ({ restore, persist, recordTranslation, frequent }),
    [restore, persist, recordTranslation, frequent],
  );
}
