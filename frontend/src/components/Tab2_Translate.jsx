import { useEffect, useState } from 'react';
import { translateText } from '../services/api';
import LanguageSelect from './LanguageSelect';
import AudioPlayer from './AudioPlayer';
import FeedbackButtons from './FeedbackButtons';

const MAX_CHARS = 1000;

export default function Tab2_Translate() {
  const [text, setText] = useState('');
  const [src, setSrc] = useState('en');
  const [tgt, setTgt] = useState('bn');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
      <h2>Translate text</h2>
      <p className="lead">Type or paste a message, notice or instruction.</p>

      <div className="row row-end">
        <LanguageSelect id="src-lang" label="From" value={src} onChange={setSrc} />
        <button className="btn-small swap" onClick={swap} aria-label="Swap languages">⇄</button>
        <LanguageSelect id="tgt-lang" label="To" value={tgt} onChange={setTgt} exclude={src} />
      </div>

      <textarea
        className={`text-${src}`}
        rows={5}
        maxLength={MAX_CHARS}
        placeholder="Enter text to translate"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <p className="hint">{text.length}/{MAX_CHARS} characters</p>

      <button className="btn" onClick={handleTranslate} disabled={!text.trim() || loading}>
        {loading ? 'Translating…' : 'Translate'}
      </button>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result">
          <h3>Translation</h3>
          <p className={`output text-${tgt}`}>{result}</p>
          <AudioPlayer text={result} language={tgt} />
          <FeedbackButtons feature="translate" details={{ text, src, tgt }} />
        </div>
      )}
    </section>
  );
}
