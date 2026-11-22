import { useEffect, useState } from 'react';
import { checkHealth } from '../services/api';
import { useLang } from '../i18n/LanguageContext';
import { PICKER } from '../i18n/strings';

export default function Navbar() {
  const { t, uiLang, openPicker } = useLang();
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    checkHealth()
      .then((r) => setStatus(r.status === 'mock' ? 'mock' : 'online'))
      .catch(() => setStatus('offline'));
  }, []);

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="brand-row">
          {/* One letter from each supported language: Bengali, Tamil, English */}
          <div className="brand-mark" aria-hidden="true">
            <span className="m-bn">অ</span>
            <span className="m-ta">அ</span>
            <span className="m-en">A</span>
          </div>
          <div>
            <h1 className="brand">FormScan-Lite</h1>
            <p className={`tagline text-${uiLang}`}>{t('tagline')}</p>
          </div>
        </div>
        <div className="navbar-actions">
          <span className={`status status-${status}`}>{t(`status.${status}`)}</span>
          <button
            className={`lang-button text-${uiLang}`}
            onClick={openPicker}
            aria-label={`${t('changeLanguage')}: ${PICKER[uiLang].name}`}
          >
            {PICKER[uiLang].name}
          </button>
        </div>
      </div>
    </header>
  );
}
