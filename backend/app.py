from flask import Flask
from flask_cors import CORS
import logging
import os

from config import Config

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, filename='logs/app.log')

if __name__ == '__main__':
    app.run(debug=True, port=5000)