from flask import Flask, send_from_directory, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

database_url = os.environ.get("DATABASE_URL", "sqlite:///jarvis.db")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def local_logic(user_msg: str):
    low = user_msg.lower()

    if "ciao" in low:
        return "Ciao. Sono Jarvis. Il sito è online e funziono senza dover avviare PowerShell."
    elif "chi sei" in low:
        return "Sono Jarvis, il tuo assistente web."
    elif "ti ricordi" in low or "memoria" in low or "cronologia" in low:
        return "Posso salvare la cronologia nel sito e mostrarla nella sezione dedicata."
    elif "progetto" in low or "obiettivo" in low or "obbiettivo" in low:
        return "Il nostro progetto è creare una web app Jarvis bella, online, con cronologia e in futuro con AI completa."
    elif "online" in low:
        return "Sì, il sito è online su Render e puoi aprirlo senza PowerShell."
    elif "powershell" in low:
        return "No, per aprire il sito online non devi usare PowerShell. Quello serviva solo per svilupparlo in locale."
    else:
        return "Sono online e funziono. Per ora uso una logica locale semplice, ma il sito è accessibile senza accendere PowerShell."


@app.route('/')
def home():
    return send_from_directory('static', 'index.html')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"response": "Scrivi un messaggio."})

    response = local_logic(user_msg)

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
