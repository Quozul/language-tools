"use client";

import { createContext, type ReactNode, useContext } from "react";
import {
  type TransliterateActions,
  type TransliterateEditorSlice,
  type TransliterateSessionSlice,
  type TransliterateSettingsSlice,
  useTransliterateController,
} from "./use-transliterate";

const TransliterateSettingsContext =
  createContext<TransliterateSettingsSlice | null>(null);
const TransliterateEditorContext =
  createContext<TransliterateEditorSlice | null>(null);
const TransliterateSessionContext =
  createContext<TransliterateSessionSlice | null>(null);
const TransliterateActionsContext = createContext<TransliterateActions | null>(
  null,
);

export function TransliterateProvider({ children }: { children: ReactNode }) {
  const { settingsSlice, editorSlice, sessionSlice, actions } =
    useTransliterateController();
  return (
    <TransliterateSettingsContext.Provider value={settingsSlice}>
      <TransliterateEditorContext.Provider value={editorSlice}>
        <TransliterateSessionContext.Provider value={sessionSlice}>
          <TransliterateActionsContext.Provider value={actions}>
            {children}
          </TransliterateActionsContext.Provider>
        </TransliterateSessionContext.Provider>
      </TransliterateEditorContext.Provider>
    </TransliterateSettingsContext.Provider>
  );
}

function useSlice<T>(context: React.Context<T | null>, hookName: string): T {
  const value = useContext(context);
  if (!value) {
    throw new Error(`${hookName} must be used inside TransliterateProvider`);
  }
  return value;
}

export function useTransliterateSettings(): TransliterateSettingsSlice {
  return useSlice(TransliterateSettingsContext, "useTransliterateSettings");
}

export function useTransliterateEditor(): TransliterateEditorSlice {
  return useSlice(TransliterateEditorContext, "useTransliterateEditor");
}

export function useTransliterateSession(): TransliterateSessionSlice {
  return useSlice(TransliterateSessionContext, "useTransliterateSession");
}

export function useTransliterateActions(): TransliterateActions {
  return useSlice(TransliterateActionsContext, "useTransliterateActions");
}
