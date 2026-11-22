import { useEffect, useState } from 'react';
import { sendFeedback } from '../services/api';
import { useLang } from '../i18n/LanguageContext';

export default function FeedbackButtons({ feature, details }) {
  const { t } = useLang();
  const [sent, setSent] = useState(null);

  useEffect(() => setSent(null), [details?.text]);

  const handle = async (helpful) => {
    try {
      await sendFeedback(feature, helpful, details);
    } catch {
      // Feedback failing should never block the user
    }
    setSent(helpful);
  };

  if (sent !== null) {
    return <p className="feedback-done">{t('fb.done')}</p>;
  }

  return (
    <div className="feedback">
      <span>{t('fb.ask')}</span>
      <button className="btn-small" onClick={() => handle(true)}>{t('fb.yes')}</button>
      <button className="btn-small" onClick={() => handle(false)}>{t('fb.no')}</button>
    </div>
  );
}
