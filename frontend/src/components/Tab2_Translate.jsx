import { useEffect, useState } from 'react';
import { translateText } from '../services/api';
import LanguageSelect from './LanguageSelect';
import AudioPlayer from './AudioPlayer';
import FeedbackButtons from './FeedbackButtons';
import { useLang } from '../i18n/LanguageContext';

const MAX_CHARS = 1000;

// Typed text goes from another language into the user's own
const startPair = (ui) => (ui === 'en' ? ['bn', 'en'] : ['en', ui]);

export default function Tab2_Translate() {
  const { t, uiLang } = useLang();
  const [text, setText] = useState('');
  const [src, setSrc] = useState(() => startPair(uiLang)[0]);
  const [tgt, setTgt] = useState(() => startPair(uiLang)[1]);
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // When the interface language changes, reset the language pair (the typed text is kept)
  useEffect(() => {
    const [s, g] = startPair(uiLang);
    setSrc(s);
    setTgt(g);
  }, [uiLang]);

  useEffect(() => {
    if (src === tgt) setTgt(src === 'en' ? 'bn' : 'en');
  }, [src, tgt]);

  const swap = () => {
    setSrc(tgt);
    setTgt(src);
    if (result) {
      setText(result);
      setResult('');
    }
  };

  const handleTranslate = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await translateText(text, src, tgt);
      setResult(res.translated_text);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  return (
    <section className="panel">
      <h2>{t('tr.title')}</h2>
      <p className="lead">{t('tr.lead')}</p>

      <div className="row row-end">
        <LanguageSelect id="src-lang" label={t('tr.from')} value={src} onChange={setSrc} />
        <button className="btn-small swap" onClick={swap} aria-label={t('tr.swap')}>⇄</button>
        <LanguageSelect id="tgt-lang" label={t('tr.to')} value={tgt} onChange={setTgt} exclude={src} />
      </div>

      <textarea
        className={`text-${src}`}
        rows={5}
        maxLength={MAX_CHARS}
        placeholder={t('tr.placeholder')}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <p className="hint">{t('tr.chars', { n: text.length, max: MAX_CHARS })}</p>

      <button className="btn" onClick={handleTranslate} disabled={!text.trim() || loading}>
        {loading ? t('translate.loading') : t('translate.button')}
      </button>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result">
          <h3>{t('translation')}</h3>
          <p className={`output text-${tgt}`}>{result}</p>
          <AudioPlayer text={result} language={tgt} />
          <FeedbackButtons feature="translate" details={{ text, src, tgt }} />
        </div>
      )}
    </section>
  );
}
