from flask import Flask, send_from_directory, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from openai import OpenAI
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

database_url = os.environ.get("DATABASE_URL", "sqlite:///jarvis.db")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def build_prompt(user_msg: str):
    history = Message.query.order_by(Message.timestamp.asc()).limit(12).all()

    parts = [
        "Ti chiami Jarvis.",
        "Rispondi sempre in italiano.",
        "Sei utile, chiaro, naturale e ricordi il contesto recente.",
        "L'utente sta costruendo una web app Jarvis con backend Flask, database e cronologia.",
        "",
        "Cronologia recente:"
    ]

    for m in history:
        who = "Utente" if m.sender == "user" else "Jarvis"
        parts.append(f"{who}: {m.content}")

    parts.append("")
    parts.append(f"Utente: {user_msg}")

    return "\n".join(parts)


@app.route('/')
def home():
    return send_from_directory('static', 'index.html')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"response": "Scrivi un messaggio."})

    if client:
        try:
            response_obj = client.responses.create(
                model="gpt-5.4",
                input=build_prompt(user_msg)
            )
            response = response_obj.output_text.strip()
        except Exception as e:
            response = f"AI temporaneamente non disponibile: {e}"
    else:
        response = "Il sito è online, ma manca la chiave API dell'AI sul server."

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
    app.run(host="0.0.0.0", port=port, debug=True)
