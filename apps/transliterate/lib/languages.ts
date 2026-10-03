/**
 * Display names for languages reported by the transliterate service
 * capabilities endpoint. Unknown codes fall back to the code itself, so new
 * service languages work without a client release.
 */

const LANGUAGE_NAMES: Record<string, string> = {
  ja: "Japanese",
};

const NAME_BY_CODE = new Map(
  Object.entries(LANGUAGE_NAMES).map(([code, name]) => [
    code.toLowerCase(),
    name,
  ]),
);

export function languageLabel(code: string): string {
  const trimmed = code.trim();
  return NAME_BY_CODE.get(trimmed.toLowerCase()) ?? trimmed;
}

export function normalizeLanguageQuery(query: string): string {
  return query.trim().toLowerCase();
}

export function matchesLanguageCode(code: string, query: string): boolean {
  const normalized = normalizeLanguageQuery(query);
  if (normalized === "") return true;
  return [languageLabel(code), code].some((value) =>
    value.toLowerCase().includes(normalized),
  );
}
