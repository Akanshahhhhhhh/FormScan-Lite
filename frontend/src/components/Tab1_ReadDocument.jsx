import { useEffect, useState } from 'react';
import { extractText, translateText } from '../services/api';
import { ALLOWED_TYPES, LOW_CONFIDENCE, MAX_FILE_MB } from '../utils/constants';
import LanguageSelect from './LanguageSelect';
import ConfidenceBar from './ConfidenceBar';
import AudioPlayer from './AudioPlayer';
import FeedbackButtons from './FeedbackButtons';
import { defaultsFor, useLang } from '../i18n/LanguageContext';

export default function Tab1_ReadDocument() {
  const { t, uiLang } = useLang();
  const [docLang, setDocLang] = useState(() => defaultsFor(uiLang).docLang);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [ocr, setOcr] = useState(null);         // { text, confidence }
  const [text, setText] = useState('');         // editable OCR text
  const [targetLang, setTargetLang] = useState(() => defaultsFor(uiLang).targetLang);
  const [translation, setTranslation] = useState('');
  const [loading, setLoading] = useState('');   // '' | 'ocr' | 'translate'
  const [error, setError] = useState('');

  // Free the preview URL when the file changes
  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

  // When the interface language changes, translate into the new language by default
  useEffect(() => { setTargetLang(defaultsFor(uiLang).targetLang); }, [uiLang]);

  // Target language must differ from document language
  useEffect(() => {
    if (targetLang === docLang) setTargetLang(docLang === 'en' ? 'bn' : 'en');
  }, [docLang, targetLang]);

  const handleFile = (e) => {
    const f = e.target.files[0];
    setError('');
    setOcr(null);
    setTranslation('');
    if (!f) return;
    if (!ALLOWED_TYPES.includes(f.type)) {
      setError(t('read.badType'));
      return;
    }
    if (f.size > MAX_FILE_MB * 1024 * 1024) {
      setError(t('read.tooBig', { mb: MAX_FILE_MB }));
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const handleRead = async () => {
    setLoading('ocr');
    setError('');
    setTranslation('');
    try {
      const res = await extractText(file, docLang);
      setOcr(res);
      setText(res.text || '');
      if (!res.text) setError(t('read.noText'));
    } catch (e) {
      setError(e.message);
    }
    setLoading('');
  };

  const handleTranslate = async () => {
    setLoading('translate');
    setError('');
    try {
      const res = await translateText(text, docLang, targetLang);
      setTranslation(res.translated_text);
    } catch (e) {
      setError(e.message);
    }
    setLoading('');
  };

  return (
    <section className="panel">
      <h2>{t('read.title')}</h2>
      <p className="lead">{t('read.lead')}</p>

      <div className="row">
        <LanguageSelect id="doc-lang" label={t('read.docLang')} value={docLang} onChange={setDocLang} />
        <label className="field" htmlFor="doc-file">
          <span className="field-label">{t('read.photo')}</span>
          <input id="doc-file" type="file" accept={ALLOWED_TYPES.join(',')} onChange={handleFile} />
        </label>
      </div>

      {preview && <img className="preview" src={preview} alt={t('read.previewAlt')} />}

      <button className="btn" onClick={handleRead} disabled={!file || loading}>
        {loading === 'ocr' ? t('read.loading') : t('read.button')}
      </button>

      {error && <p className="error">{error}</p>}

      {ocr && text && (
        <div className="result">
          <h3>{t('read.found')}</h3>
          <ConfidenceBar value={ocr.confidence} />
          {ocr.confidence < LOW_CONFIDENCE && (
            <p className="warning">{t('read.lowWarn')}</p>
          )}
          <textarea
            className={`text-${docLang}`}
            rows={5}
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label={t('read.textAria')}
          />
          <AudioPlayer text={text} language={docLang} />

          <div className="row row-end">
            <LanguageSelect id="target-lang" label={t('translateTo')} value={targetLang} onChange={setTargetLang} exclude={docLang} />
            <button className="btn" onClick={handleTranslate} disabled={!text.trim() || loading}>
              {loading === 'translate' ? t('translate.loading') : t('translate.button')}
            </button>
          </div>

          {translation && (
            <div className="result-inner">
              <h3>{t('translation')}</h3>
              <p className={`output text-${targetLang}`}>{translation}</p>
              <AudioPlayer text={translation} language={targetLang} />
            </div>
          )}

          <FeedbackButtons feature="read_document" details={{ text, docLang, confidence: ocr.confidence }} />
        </div>
      )}
    </section>
  );
}
