import { LANGUAGES } from '../utils/constants';

export default function LanguageSelect({ label, value, onChange, exclude, id }) {
  return (
    <label className="field" htmlFor={id}>
      <span className="field-label">{label}</span>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
        {LANGUAGES.filter((l) => l.code !== exclude).map((l) => (
          <option key={l.code} value={l.code}>
            {l.native === l.name ? l.name : `${l.native} (${l.name})`}
          </option>
        ))}
      </select>
    </label>
  );
}
