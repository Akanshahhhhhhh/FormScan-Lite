from flask import Flask
from flask_cors import CORS
import logging
import os
import threading
from routes.faq_routes import faq_bp

from config import Config
from routes.ocr_routes import ocr_bp
from routes.translate_routes import translate_bp
from routes.tts_routes import tts_bp
from routes.feedback_routes import feedback_bp
from routes.health_routes import health_bp
from routes.compat_routes import compat_bp
from routes.chat_routes import chat_bp

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
logging.basicConfig(level=logging.INFO, filename='logs/app.log')

app.register_blueprint(ocr_bp)
app.register_blueprint(translate_bp)
app.register_blueprint(tts_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(faq_bp)
app.register_blueprint(health_bp)
app.register_blueprint(compat_bp)
app.register_blueprint(chat_bp)


def warm_up_chatbot():
    """Load the embedding model once at startup, so the first real question
    is fast. This question matches no FAQ, so Gemini is not called."""
    try:
        from services import llm_service
        llm_service.answer_question('zzzz warm up', 'en')
        logging.info('Chatbot warm-up done')
    except Exception:
        logging.exception('Chatbot warm-up failed (the first question will be slow)')


if __name__ == '__main__':
    # Flask debug mode starts the app twice; only the real worker should warm up.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Thread(target=warm_up_chatbot, daemon=True).start()
    app.run(debug=True, port=5000)
