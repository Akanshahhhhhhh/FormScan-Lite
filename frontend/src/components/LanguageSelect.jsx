import { LANGUAGES } from '../utils/constants';
import { useLang } from '../i18n/LanguageContext';

export default function LanguageSelect({ label, value, onChange, exclude, id }) {
  const { langLabel } = useLang();
  return (
    <label className="field" htmlFor={id}>
      <span className="field-label">{label}</span>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
        {LANGUAGES.filter((l) => l.code !== exclude).map((l) => {
          const shown = langLabel(l.code);
          return (
            <option key={l.code} value={l.code}>
              {l.native === shown ? l.native : `${l.native} (${shown})`}
            </option>
          );
        })}
      </select>
    </label>
  );
}
