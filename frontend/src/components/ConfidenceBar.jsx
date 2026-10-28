import { LOW_CONFIDENCE } from '../utils/constants';

export default function ConfidenceBar({ value, label = 'Reading confidence' }) {
  if (value === undefined || value === null) return null;
  const pct = Math.round(value * 100);
  const level = value >= 0.85 ? 'high' : value >= LOW_CONFIDENCE ? 'medium' : 'low';
  const verdict = {
    high: 'Likely correct',
    medium: 'Check a few words',
    low: 'Check carefully before using',
  }[level];

  return (
    <div className={`confidence confidence-${level}`}>
      <div className="confidence-head">
        <span>{label}</span>
        <strong>{pct}%</strong>
      </div>
      <div className="confidence-track" aria-hidden="true">
        <div className="confidence-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="confidence-verdict">{verdict}</p>
    </div>
  );
}
