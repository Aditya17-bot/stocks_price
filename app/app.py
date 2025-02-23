from flask import Flask, render_template, request, jsonify
import yfinance as yf
from datetime import datetime
import signal
import sys

app = Flask(__name__)

def signal_handler(sig, frame):
    print('Shutting down the server...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler) 