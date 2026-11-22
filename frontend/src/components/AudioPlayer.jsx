import { useEffect, useState } from 'react';
import { generateSpeech, resolveAudioUrl } from '../services/api';
import { USE_MOCK } from '../utils/constants';
import { useLang } from '../i18n/LanguageContext';

export default function AudioPlayer({ text, language }) {
  const { t, langLabel } = useLang();
  const [url, setUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mockNote, setMockNote] = useState(false);

  // Reset when the text changes
  useEffect(() => {
    setUrl(null);
    setError('');
    setMockNote(false);
  }, [text, language]);

  const handleListen = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await generateSpeech(text, language);
      const audio = resolveAudioUrl(res.audio_url);
      if (audio) setUrl(audio);
      else if (USE_MOCK) setMockNote(true);
      else setError(t('audio.noFile'));
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  if (!text) return null;

  return (
    <div className="audio">
      {!url && (
        <button className="btn btn-secondary" onClick={handleListen} disabled={loading}>
          {loading ? t('audio.loading') : t('audio.listen', { lang: langLabel(language) })}
        </button>
      )}
      {url && <audio controls autoPlay src={url} />}
      {mockNote && <p className="hint">{t('audio.mock')}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
