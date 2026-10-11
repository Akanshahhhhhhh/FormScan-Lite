import { useState } from 'react';
import { askFaq } from '../services/api';
import LanguageSelect from './LanguageSelect';
import AudioPlayer from './AudioPlayer';
import FeedbackButtons from './FeedbackButtons';

const EXAMPLES = {
  en: ['What documents are required for a birth certificate?', 'When is the Gram Sabha held?'],
  bn: ['জন্ম সনদের জন্য কী কী কাগজ লাগে?'],
  ta: ['பிறப்புச் சான்றிதழுக்கு என்ன ஆவணங்கள் தேவை?'],
};

export default function Tab3_FAQBot() {
  const [language, setLanguage] = useState('en');
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAsk = async (q = question) => {
    if (!q.trim()) return;
    setQuestion(q);
    setLoading(true);
    setError('');
    setResult(null);
    try {
      setResult(await askFaq(q, language));
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  return (
    <section className="panel">
      <h2>Ask about a public service</h2>
      <p className="lead">Answers come from a fixed list of checked questions, so the assistant does not guess.</p>

      <LanguageSelect id="faq-lang" label="Your language" value={language} onChange={(v) => { setLanguage(v); setResult(null); }} />

      <textarea
        className={`text-${language}`}
        rows={3}
        placeholder="Type your question"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleAsk();
          }
        }}
      />

      <div className="examples">
        <span className="hint">Try:</span>
        {EXAMPLES[language].map((q) => (
          <button key={q} className={`chip text-${language}`} onClick={() => handleAsk(q)}>{q}</button>
        ))}
      </div>

      <button className="btn" onClick={() => handleAsk()} disabled={!question.trim() || loading}>
        {loading ? 'Searching…' : 'Ask'}
      </button>

      {error && <p className="error">{error}</p>}

      {result && result.matched && (
        <div className="result">
          {result.question && <p className="matched-q">Closest question: {result.question}</p>}
          <p className={`output text-${language}`}>{result.answer}</p>
          <AudioPlayer text={result.answer} language={language} />
          <FeedbackButtons feature="faq" details={{ question, language }} />
        </div>
      )}

      {result && !result.matched && (
        <div className="result result-empty">
          <p>No answer for this question yet. Try different words, or contact your local panchayat or municipality office.</p>
        </div>
      )}
    </section>
  );
}
