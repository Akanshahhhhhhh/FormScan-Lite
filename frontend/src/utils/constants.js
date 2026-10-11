export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export const LANGUAGES = [
  { code: 'bn', name: 'Bengali', native: 'বাংলা' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
  { code: 'en', name: 'English', native: 'English' },
];

export const langName = (code) =>
  LANGUAGES.find((l) => l.code === code)?.name || code;

// OCR confidence below this is flagged for the user to check
export const LOW_CONFIDENCE = 0.6;
export const MAX_FILE_MB = 10;
export const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
