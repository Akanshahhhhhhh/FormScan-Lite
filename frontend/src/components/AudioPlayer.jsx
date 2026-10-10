import { useEffect, useState } from 'react';
import { generateSpeech, resolveAudioUrl } from '../services/api';
import { USE_MOCK, langName } from '../utils/constants';

export default function AudioPlayer({ text, language }) {
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
      else setError('The server did not return an audio file.');
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
          {loading ? 'Preparing audio…' : `Listen in ${langName(language)}`}
        </button>
      )}
      {url && <audio controls autoPlay src={url} />}
      {mockNote && <p className="hint">Audio plays once the backend is connected.</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
