from flask import Flask, redirect
from threading import Thread

app = Flask('')


@app.route('/')
def home():
  return '''Spectral Alive!'''


def run():
  app.run(host='0.0.0.0', port=777)


def keep_alive():
  t = Thread(target=run)
  t.start()
