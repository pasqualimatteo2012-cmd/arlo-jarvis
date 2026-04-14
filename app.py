from flask import Flask, send_from_directory, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

database_url = os.environ.get("DATABASE_URL", "sqlite:///jarvis.db")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "").strip()
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:latest")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def build_messages(user_msg: str):
    history = Message.query.order_by(Message.timestamp.asc()).limit(12).all()

    messages = [
        {
            "role": "system",
            "content": (
                "Ti chiami Jarvis. Sei un assistente personale locale. "
                "Rispondi in italiano in modo chiaro, utile e naturale. "
                "L'utente sta costruendo una web app Jarvis con Flask, database, cronologia e interfaccia grafica."
            )
        }
    ]

    for m in history:
        role = "user" if m.sender == "user" else "assistant"
        messages.append({"role": role, "content": m.content})

    messages.append({"role": "user", "content": user_msg})
    return messages


@app.route('/')
def home():
    return send_from_directory('static', 'index.html')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"response": "Scrivi un messaggio."})

    if OLLAMA_URL:
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": build_messages(user_msg),
                "stream": False
            }
            r = requests.post(OLLAMA_URL, json=payload, timeout=120)
            r.raise_for_status()
            result = r.json()
            response = result["message"]["content"].strip()
        except Exception as e:
            response = f"AI temporaneamente non disponibile: {e}"
    else:
        response = "Sito online correttamente. La parte AI locale non è configurata su questo server."

    db.session.add(Message(sender="user", content=user_msg))
    db.session.add(Message(sender="jarvis", content=response))
    db.session.commit()

    return jsonify({"response": response})


@app.route('/history')
def history():
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', messages=messages)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    print(f"Jarvis avviato su http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
