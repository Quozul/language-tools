"use client";

import { useCallback, useMemo, useState } from "react";
import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxInput,
  ComboboxItem,
  ComboboxLabel,
  ComboboxList,
} from "@qzl/ui/components/combobox";
import { languageLabel, matchesLanguageCode } from "@/lib/languages";
import { AUTO_LANGUAGE } from "@/lib/transliterate-contract";

interface LanguagePickerProps {
  selected: string;
  languages: string[];
  onSelect: (code: string) => void;
  ariaLabel?: string;
  detectLabel: string;
}

export function LanguagePicker({
  selected,
  languages,
  onSelect,
  ariaLabel = "Language",
  detectLabel,
}: LanguagePickerProps) {
  const [query, setQuery] = useState<string | null>(null);
  const itemToStringLabel = useCallback(
    (value: string) =>
      value === AUTO_LANGUAGE ? detectLabel : languageLabel(value),
    [detectLabel],
  );
  const inputValue = query ?? itemToStringLabel(selected);

  const filtered = useMemo(
    () => languages.filter((code) => matchesLanguageCode(code, query ?? "")),
    [languages, query],
  );

  const items = useMemo(() => [AUTO_LANGUAGE, ...filtered], [filtered]);

  return (
    <Combobox
      items={items}
      itemToStringLabel={itemToStringLabel}
      filter={() => true}
      autoHighlight
      value={selected}
      onValueChange={(value) => {
        if (typeof value === "string" && value !== "") onSelect(value);
      }}
      inputValue={inputValue}
      onInputValueChange={(value) => setQuery(value)}
      onOpenChange={(open, details) => {
        if (!open) {
          setQuery(null);
          return;
        }
        if (details.reason === "input-change") return;
        setQuery("");
      }}
    >
      <ComboboxInput
        aria-label={ariaLabel}
        autoComplete="off"
        className="w-auto border-transparent bg-transparent hover:bg-muted"
      />
      <ComboboxContent>
        <ComboboxList>
          <ComboboxEmpty>No languages found.</ComboboxEmpty>
          <ComboboxGroup>
            <ComboboxItem value={AUTO_LANGUAGE}>{detectLabel}</ComboboxItem>
          </ComboboxGroup>
          {filtered.length > 0 && (
            <ComboboxGroup>
              <ComboboxLabel>Supported languages</ComboboxLabel>
              {filtered.map((code) => (
                <ComboboxItem key={code} value={code}>
                  <span className="flex min-w-0 flex-1 items-baseline gap-2">
                    <span>{languageLabel(code)}</span>
                  </span>
                </ComboboxItem>
              ))}
            </ComboboxGroup>
          )}
        </ComboboxList>
      </ComboboxContent>
    </Combobox>
  );
}
