import { useEffect, useState } from 'react';
import { askFaq } from '../services/api';
import LanguageSelect from './LanguageSelect';
import AudioPlayer from './AudioPlayer';
import FeedbackButtons from './FeedbackButtons';
import { defaultsFor, useLang } from '../i18n/LanguageContext';

// Example questions that match an entry in the FAQ set
const EXAMPLES = {
  en: ['How do I apply for a digital ration card in West Bengal?', 'How do I update my mobile number in Aadhaar?'],
  bn: ['জন্ম সনদের জন্য কী কী কাগজ লাগে?', 'রেশন কার্ডের জন্য কীভাবে আবেদন করব?', 'স্বাস্থ্য সাথী কার্ড কীভাবে পাব?'],
  ta: ['பிறப்புச் சான்றிதழுக்கு என்ன ஆவணங்கள் தேவை?', 'ஆதாரில் மொபைல் எண்ணை எப்படி மாற்றுவது?'],
};

export default function Tab3_FAQBot() {
  const { t, uiLang } = useLang();
  const [language, setLanguage] = useState(() => defaultsFor(uiLang).faqLang);
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Ask in the interface language by default
  useEffect(() => {
    setLanguage(defaultsFor(uiLang).faqLang);
    setResult(null);
  }, [uiLang]);

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
      <h2>{t('faq.title')}</h2>
      <p className="lead">{t('faq.lead')}</p>

      <LanguageSelect id="faq-lang" label={t('faq.lang')} value={language} onChange={(v) => { setLanguage(v); setResult(null); }} />

      <textarea
        className={`text-${language}`}
        rows={3}
        placeholder={t('faq.placeholder')}
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
        <span className="hint">{t('faq.try')}</span>
        {EXAMPLES[language].map((q) => (
          <button key={q} className={`chip text-${language}`} onClick={() => handleAsk(q)}>{q}</button>
        ))}
      </div>

      <button className="btn" onClick={() => handleAsk()} disabled={!question.trim() || loading}>
        {loading ? t('faq.loading') : t('faq.ask')}
      </button>

      {error && <p className="error">{error}</p>}

      {result && result.matched && (
        <div className="result">
          {result.question && <p className="matched-q">{t('faq.closest', { q: result.question })}</p>}
          <p className={`output text-${language}`}>{result.answer}</p>
          <AudioPlayer text={result.answer} language={language} />
          <FeedbackButtons feature="faq" details={{ question, language }} />
        </div>
      )}

      {result && !result.matched && (
        <div className="result result-empty">
          <p>{t('faq.none')}</p>
        </div>
      )}
    </section>
  );
}
