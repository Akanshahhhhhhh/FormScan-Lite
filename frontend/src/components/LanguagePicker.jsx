import { useEffect, useRef } from 'react';
import { useLang } from '../i18n/LanguageContext';
import { PICKER, PICKER_NOTE, PICKER_TITLE, UI_LANGS } from '../i18n/strings';

// Shown on first launch, and again when the user taps the language button
export default function LanguagePicker() {
  const { chosen, uiLang, chooseLanguage, closePicker } = useLang();
  const firstButton = useRef(null);

  useEffect(() => {
    firstButton.current?.focus();
    const onKey = (e) => {
      if (e.key === 'Escape' && chosen) closePicker();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [chosen, closePicker]);

  return (
    <div className="picker" role="dialog" aria-modal="true" aria-labelledby="picker-title">
      <div className="picker-inner">
        <div className="brand-mark brand-mark-large" aria-hidden="true">
          <span className="m-bn">অ</span>
          <span className="m-ta">அ</span>
          <span className="m-en">A</span>
        </div>

        <h1 id="picker-title" className="picker-title">
          {PICKER_TITLE.map((line, i) => (
            <span key={line} className={i === 0 ? 'text-bn' : i === 1 ? 'text-ta' : ''}>{line}</span>
          ))}
        </h1>

        <div className="picker-options">
          {UI_LANGS.map((code, i) => (
            <button
              key={code}
              ref={i === 0 ? firstButton : null}
              className={`picker-option picker-${code} ${chosen && uiLang === code ? 'picker-current' : ''}`}
              lang={code}
              onClick={() => chooseLanguage(code)}
            >
              <span className={`picker-name text-${code}`}>{PICKER[code].name}</span>
              <span className={`picker-action text-${code}`}>{PICKER[code].action}</span>
            </button>
          ))}
        </div>

        <p className="picker-note">{PICKER_NOTE[chosen ? uiLang : 'en']}</p>
      </div>
    </div>
  );
}
