import axios from 'axios';
import { API_URL, USE_MOCK } from '../utils/constants';

// Long timeout: the first request loads the models and can be slow
const client = axios.create({ baseURL: API_URL, timeout: 120000 });

function friendlyError(err) {
  if (err.response) {
    return err.response.data?.error || `Server error (${err.response.status}).`;
  }
  if (err.code === 'ECONNABORTED') {
    return 'The server took too long to respond. Try again in a moment.';
  }
  return `Cannot reach the backend at ${API_URL}. Check that the Flask server is running.`;
}

async function call(request) {
  try {
    const res = await request();
    return res.data;
  } catch (err) {
    throw new Error(friendlyError(err));
  }
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/* ---------- Demo data (used when VITE_USE_MOCK=true) ---------- */
const MOCK_OCR = {
  bn: 'জন্ম সনদের জন্য আবেদন',
  ta: 'பிறப்புச் சான்றிதழ் விண்ணப்பம்',
  en: 'Application for birth certificate',
};

const MOCK_FAQ = {
  question: 'What documents are required for a birth certificate?',
  answer:
    'Hospital discharge or birth report, ID proof of both parents, and address proof. Apply at your local municipality or panchayat office.',
};

/* ---------- API functions ---------- */
export async function extractText(file, language) {
  if (USE_MOCK) {
    await wait(800);
    return { text: MOCK_OCR[language], confidence: 0.72, language };
  }
  const form = new FormData();
  form.append('image', file);
  form.append('language', language);
  return call(() => client.post('/api/ocr/extract', form));
}

export async function translateText(text, srcLang, tgtLang) {
  if (USE_MOCK) {
    await wait(700);
    return { translated_text: `[demo ${srcLang}→${tgtLang}] ${text}`, src_lang: srcLang, tgt_lang: tgtLang };
  }
  return call(() =>
    client.post('/api/translate/translate', { text, src_lang: srcLang, tgt_lang: tgtLang })
  );
}

export async function generateSpeech(text, language) {
  if (USE_MOCK) {
    await wait(500);
    return { audio_url: null };
  }
  return call(() => client.post('/api/tts/generate', { text, language }));
}

export async function askFaq(query, language) {
  if (USE_MOCK) {
    await wait(600);
    const q = query.toLowerCase();
    const hit = q.includes('birth') || q.includes('জন্ম') || q.includes('பிறப்பு');
    return hit
      ? { matched: true, ...MOCK_FAQ, confidence: 0.9 }
      : { matched: false, answer: null, confidence: 0 };
  }
  return call(() => client.post('/api/faq/ask', { query, language }));
}

export async function sendFeedback(feature, helpful, details = {}) {
  if (USE_MOCK) {
    await wait(200);
    return { status: 'ok' };
  }
  return call(() => client.post('/api/feedback', { feature, helpful, details }));
}

export async function checkHealth() {
  if (USE_MOCK) return { status: 'mock' };
  return call(() => client.get('/api/health'));
}

// Backend may return "/audio/x.mp3" (relative) or a full URL
export const resolveAudioUrl = (url) =>
  !url ? null : url.startsWith('http') ? url : `${API_URL}${url}`;
