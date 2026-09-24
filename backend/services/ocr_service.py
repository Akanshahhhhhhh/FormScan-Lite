import easyocr
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# EasyOCR reader for English + Bengali (Tamil excluded due to known library bug)
_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(['bn', 'en'])
    return _easyocr_reader


def extract_text_bengali(image_path):
    reader = get_easyocr_reader()
    results = reader.readtext(image_path)
    text = " ".join([res[1] for res in results])
    avg_confidence = (
        sum([res[2] for res in results]) / len(results) if results else 0.0
    )
    return {"text": text, "confidence": avg_confidence, "engine": "easyocr"}


def extract_text_tamil(image_path):
    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, lang='tam', output_type=pytesseract.Output.DICT)

    words = [w for w in data['text'] if w.strip()]
    confidences = [int(c) for c, w in zip(data['conf'], data['text']) if w.strip() and int(c) != -1]

    text = " ".join(words)
    avg_confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.0
    return {"text": text, "confidence": avg_confidence, "engine": "tesseract"}


def extract_text(image_path, language):
    """
    language: 'bn' for Bengali, 'ta' for Tamil, 'en' for English
    """
    if language == 'ta':
        return extract_text_tamil(image_path)
    elif language in ('bn', 'en'):
        return extract_text_bengali(image_path)
    else:
        raise ValueError(f"Unsupported language: {language}")