from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World adam!'

@app.route('/about')
def about():
    return 'adam test'
