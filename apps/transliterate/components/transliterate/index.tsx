"use client";

import { LanguageBar } from "./language-bar";
import { SourceEditor } from "./source-editor";
import { TransliterateProvider } from "./transliterate-context";
import { TransliterationOutput } from "./transliteration-output";

export function TransliterateApp() {
  return (
    <TransliterateProvider>
      <div className="flex min-h-dvh flex-col justify-center md:px-6 md:py-8">
        <main className="mx-auto flex min-h-dvh w-full max-w-190 flex-col-reverse md:flex-col md:h-136 md:max-h-[calc(100dvh-4rem)] md:min-h-0 md:max-w-295 md:overflow-hidden md:rounded-2xl md:border">
          <LanguageBar />
          <div className="grid min-h-0 flex-1 grid-rows-[1fr_1fr] p-3 md:grid-cols-2 md:grid-rows-[1fr] md:gap-6">
            <SourceEditor />
            <div className="overflow-hidden">
              <TransliterationOutput />
            </div>
          </div>
        </main>
      </div>
    </TransliterateProvider>
  );
}
