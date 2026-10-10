import { useEffect, useState } from 'react';
import { sendFeedback } from '../services/api';

export default function FeedbackButtons({ feature, details }) {
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
    return <p className="feedback-done">Feedback recorded. Thank you.</p>;
  }

  return (
    <div className="feedback">
      <span>Was this result useful?</span>
      <button className="btn-small" onClick={() => handle(true)}>Yes</button>
      <button className="btn-small" onClick={() => handle(false)}>No</button>
    </div>
  );
}
