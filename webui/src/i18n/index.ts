import { en } from "./locales/en";
import { it } from "./locales/it";

export const SUPPORTED_LANGUAGES = ["en", "it"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

export const appMessages = {
  en: en.translation,
  it: it.translation,
};

