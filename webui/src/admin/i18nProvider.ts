import type { I18nProvider, TranslationMessages } from "react-admin";
import polyglotI18nProvider from "ra-i18n-polyglot";
import englishMessages from "ra-language-english";
import { complianceWidgetMessages } from "@/compliance-widgets";
import { appMessages, SUPPORTED_LANGUAGES, type SupportedLanguage } from "@/i18n";

const STORAGE_KEY = "ai-compliance-webui.language";
type MessageTree = Record<string, unknown>;

function mergeMessages(...sources: MessageTree[]): MessageTree {
  return sources.reduce<MessageTree>((result, source) => {
    Object.entries(source).forEach(([key, value]) => {
      const current = result[key];
      result[key] =
        value && typeof value === "object" && !Array.isArray(value)
          ? mergeMessages((current as MessageTree) ?? {}, value as MessageTree)
          : value;
    });
    return result;
  }, {});
}

function normalizeInterpolation(value: unknown): unknown {
  if (typeof value === "string") {
    return value.replace(/\{\{\s*([\w.]+)\s*\}\}/g, "%{$1}");
  }
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return Object.fromEntries(Object.entries(value).map(([key, child]) => [key, normalizeInterpolation(child)]));
  }
  return value;
}

const messages: Record<SupportedLanguage, TranslationMessages> = {
  en: normalizeInterpolation(
    mergeMessages(englishMessages, appMessages.en, complianceWidgetMessages.en),
  ) as TranslationMessages,
  it: normalizeInterpolation(
    mergeMessages(englishMessages, appMessages.it, complianceWidgetMessages.it),
  ) as TranslationMessages,
};

const storedLanguage = localStorage.getItem(STORAGE_KEY) as SupportedLanguage | null;
const initialLanguage = storedLanguage && SUPPORTED_LANGUAGES.includes(storedLanguage) ? storedLanguage : "en";
const provider = polyglotI18nProvider(
  (locale) => messages[locale as SupportedLanguage] ?? messages.en,
  initialLanguage,
  SUPPORTED_LANGUAGES.map((locale) => ({ locale, name: locale.toUpperCase() })),
  { allowMissing: true },
);

export const adminI18nProvider: I18nProvider = {
  ...provider,
  changeLocale: async (locale) => {
    await provider.changeLocale(locale);
    localStorage.setItem(STORAGE_KEY, locale);
  },
};