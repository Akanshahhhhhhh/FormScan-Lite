import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { LANG_NAMES, STRINGS, UI_LANGS } from './strings';

const STORAGE_KEY = 'formscan.uiLang';
const LanguageContext = createContext(null);

// Browser storage can be blocked (private mode, strict settings): never let that break the app
function readSaved() {
  try {
    const v = window.localStorage.getItem(STORAGE_KEY);
    return UI_LANGS.includes(v) ? v : null;
  } catch {
    return null;
  }
}
function save(lang) {
  try {
    window.localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    /* choice still applies for this visit */
  }
}

export function LanguageProvider({ children }) {
  const [uiLang, setUiLangState] = useState(readSaved); // null = not chosen yet
  const [pickerOpen, setPickerOpen] = useState(() => readSaved() === null);

  const chooseLanguage = useCallback((lang) => {
    setUiLangState(lang);
    save(lang);
    setPickerOpen(false);
  }, []);

  useEffect(() => {
    document.documentElement.lang = uiLang || 'en';
  }, [uiLang]);

  const value = useMemo(() => {
    const lang = uiLang || 'en';
    const t = (key, vars = {}) => {
      const text = STRINGS[lang][key] ?? STRINGS.en[key] ?? key;
      return text.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? vars[k] : `{${k}}`));
    };
    const langLabel = (code) => LANG_NAMES[lang][code] || code;
    return {
      uiLang: lang,
      chosen: uiLang !== null,
      t,
      langLabel,
      chooseLanguage,
      pickerOpen,
      openPicker: () => setPickerOpen(true),
      closePicker: () => setPickerOpen(false),
    };
  }, [uiLang, pickerOpen, chooseLanguage]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLang must be used inside LanguageProvider');
  return ctx;
}

// Sensible starting languages for each feature, given the interface language
export function defaultsFor(uiLang) {
  const other = uiLang === 'en' ? 'bn' : 'en';
  return {
    docLang: other,        // a notice in another language...
    targetLang: uiLang,    // ...translated into the user's language
    faqLang: uiLang,
  };
}
