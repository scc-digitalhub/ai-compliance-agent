import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { en } from "./locales/en";
import { it } from "./locales/it";

const STORAGE_KEY = "ai-compliance-webui.language";

export const SUPPORTED_LANGUAGES = ["en", "it"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

const storedLanguage = (localStorage.getItem(STORAGE_KEY) as SupportedLanguage | null) ?? "en";

i18n.use(initReactI18next).init({
  resources: { en, it },
  lng: storedLanguage,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

i18n.on("languageChanged", (lng) => {
  localStorage.setItem(STORAGE_KEY, lng);
});

export default i18n;
