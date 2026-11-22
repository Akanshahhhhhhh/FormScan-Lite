import { LOW_CONFIDENCE } from '../utils/constants';
import { useLang } from '../i18n/LanguageContext';

export default function ConfidenceBar({ value, label }) {
  const { t } = useLang();
  if (value === undefined || value === null) return null;
  const pct = Math.round(value * 100);
  const level = value >= 0.85 ? 'high' : value >= LOW_CONFIDENCE ? 'medium' : 'low';

  return (
    <div className={`confidence confidence-${level}`}>
      <div className="confidence-head">
        <span>{label || t('conf.label')}</span>
        <strong>{pct}%</strong>
      </div>
      <div className="confidence-track" aria-hidden="true">
        <div className="confidence-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="confidence-verdict">{t(`conf.${level}`)}</p>
    </div>
  );
}
