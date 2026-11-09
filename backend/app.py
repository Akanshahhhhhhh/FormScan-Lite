from flask import Flask
from flask_cors import CORS
import logging
import os
from routes.faq_routes import faq_bp

from config import Config
from routes.ocr_routes import ocr_bp
from routes.translate_routes import translate_bp
from routes.tts_routes import tts_bp
from routes.feedback_routes import feedback_bp
from routes.health_routes import health_bp
from routes.compat_routes import compat_bp

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
