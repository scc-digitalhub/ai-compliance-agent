import type { i18n as I18nInstance } from "i18next";
import { en } from "./resources/en";
import { it } from "./resources/it";

export { en, it };

/**
 * Merges the compliance widgets' bundled translations (English + Italian) into an existing,
 * already-initialized i18next instance. Call this once during your app's i18n setup — the
 * widgets' `useTranslation()` calls (and the non-hook `fieldLabel`/`enumLabel` helpers, which use
 * the default i18next singleton) will then resolve their strings from it.
 *
 * ```ts
 * import i18n from "i18next";
 * import { registerComplianceWidgetsI18n } from "compliance-widgets";
 * i18n.init({ ... });
 * registerComplianceWidgetsI18n(i18n);
 * ```
 *
 * @param namespace defaults to i18next's default namespace ("translation"); pass your own if
 * your app configured a different `defaultNS`.
 */
export function registerComplianceWidgetsI18n(i18nInstance: I18nInstance, namespace = "translation"): void {
  i18nInstance.addResourceBundle("en", namespace, en, true, true);
  i18nInstance.addResourceBundle("it", namespace, it, true, true);
}
