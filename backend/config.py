import os

class Config:
    DEBUG = True
    UPLOAD_FOLDER = 'uploads/'
    OUTPUT_FOLDER = 'outputs/'
    MODEL_FOLDER = 'data/models/'
    FAQ_FOLDER = 'data/faqs/'

    OCR_LANGUAGES = ['bn', 'ta', 'en']
    GTTS_LANGUAGES = ['en', 'bn', 'ta']
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB