import { humanize, humanizeEnumValue } from "@/schema/resolver";
import i18n from "@/i18n";

/** Long-text-ish keys get a multiline textfield instead of a single-line one. */
const LONG_TEXT_KEYS = new Set([
  "description", "goal", "purpose", "audience", "rationale", "requirement_text", "summary",
  "content", "justification", "narrative",
]);

export function isLongTextKey(key: string): boolean {
  return LONG_TEXT_KEYS.has(key);
}

export function fieldLabel(key: string): string {
  return i18n.t(`fields.${key}`, humanize(key));
}

export function enumLabel(value: string): string {
  return i18n.t(`enumValues.${value}`, humanizeEnumValue(value));
}
