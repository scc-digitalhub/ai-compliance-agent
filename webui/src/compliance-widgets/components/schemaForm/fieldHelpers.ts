import i18next from "i18next";
import { humanize, humanizeEnumValue } from "../../schema/resolver";

/** Long-text-ish keys get a multiline textfield instead of a single-line one. */
const LONG_TEXT_KEYS = new Set([
  "description", "goal", "purpose", "audience", "rationale", "requirement_text", "summary",
  "content", "justification", "narrative",
]);

export function isLongTextKey(key: string): boolean {
  return LONG_TEXT_KEYS.has(key);
}

/**
 * `fieldLabel`/`enumLabel` are called from plain (non-hook) helper code, so they use the default
 * `i18next` package singleton directly rather than `useTranslation()`. This resolves correctly as
 * long as the host app registers the widgets' translations into that same default instance (see
 * `registerComplianceWidgetsI18n`) — which is what every `useTranslation()` call in this module
 * relies on too.
 */
export function fieldLabel(key: string): string {
  return i18next.t(`fields.${key}`, { defaultValue: humanize(key) });
}

export function enumLabel(value: string): string {
  return i18next.t(`enumValues.${value}`, { defaultValue: humanizeEnumValue(value) });
}
