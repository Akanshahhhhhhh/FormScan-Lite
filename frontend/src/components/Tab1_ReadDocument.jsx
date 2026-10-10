import { useEffect, useState } from 'react';
import { extractText, translateText } from '../services/api';
import { ALLOWED_TYPES, LOW_CONFIDENCE, MAX_FILE_MB } from '../utils/constants';
import LanguageSelect from './LanguageSelect';
import ConfidenceBar from './ConfidenceBar';
import AudioPlayer from './AudioPlayer';
import FeedbackButtons from './FeedbackButtons';

export default function Tab1_ReadDocument() {
  const [docLang, setDocLang] = useState('bn');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [ocr, setOcr] = useState(null);         // { text, confidence }
  const [text, setText] = useState('');         // editable OCR text
  const [targetLang, setTargetLang] = useState('en');
  const [translation, setTranslation] = useState('');
  const [loading, setLoading] = useState('');   // '' | 'ocr' | 'translate'
  const [error, setError] = useState('');

  // Free the preview URL when the file changes
  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

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
      setError('Choose a JPG, PNG or WEBP image.');
      return;
    }
    if (f.size > MAX_FILE_MB * 1024 * 1024) {
      setError(`This image is larger than ${MAX_FILE_MB} MB. Choose a smaller one.`);
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
      if (!res.text) setError('No text was found. Try a clearer, well-lit photo.');
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
      <h2>Read a document</h2>
      <p className="lead">Upload a photo of a form or notice. We read the text, translate it and read it aloud.</p>

      <div className="row">
        <LanguageSelect id="doc-lang" label="Language of the document" value={docLang} onChange={setDocLang} />
        <label className="field" htmlFor="doc-file">
          <span className="field-label">Photo of the document</span>
          <input id="doc-file" type="file" accept={ALLOWED_TYPES.join(',')} onChange={handleFile} />
        </label>
      </div>

      {preview && <img className="preview" src={preview} alt="Uploaded document" />}

      <button className="btn" onClick={handleRead} disabled={!file || loading}>
        {loading === 'ocr' ? 'Reading text…' : 'Read text'}
      </button>

      {error && <p className="error">{error}</p>}

      {ocr && text && (
        <div className="result">
          <h3>Text found</h3>
          <ConfidenceBar value={ocr.confidence} />
          {ocr.confidence < LOW_CONFIDENCE && (
            <p className="warning">Some words may be wrong. Correct them below before translating.</p>
          )}
          <textarea
            className={`text-${docLang}`}
            rows={5}
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label="Extracted text, editable"
          />
          <AudioPlayer text={text} language={docLang} />

          <div className="row row-end">
            <LanguageSelect id="target-lang" label="Translate to" value={targetLang} onChange={setTargetLang} exclude={docLang} />
            <button className="btn" onClick={handleTranslate} disabled={!text.trim() || loading}>
              {loading === 'translate' ? 'Translating…' : 'Translate'}
            </button>
          </div>

          {translation && (
            <div className="result-inner">
              <h3>Translation</h3>
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
