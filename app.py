from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return 'Advanced Quiz Bot Running with MTProto 🔥'
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))