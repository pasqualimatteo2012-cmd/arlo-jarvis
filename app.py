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


class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def save_memory(key, value):
    item = Memory.query.filter_by(key=key).first()
    if item:
        item.value = value
    else:
        item = Memory(key=key, value=value)
        db.session.add(item)
    db.session.commit()


def get_memory(key):
    item = Memory.query.filter_by(key=key).first()
    return item.value if item else None


def recent_user_messages(limit=5):
    msgs = Message.query.filter_by(sender="user").order_by(Message.timestamp.desc()).limit(limit).all()
    return [m.content for m in reversed(msgs)]


def extract_memory(user_msg):
    low = user_msg.lower().strip()

    if low.startswith("mi chiamo "):
        name = user_msg[10:].strip()
        if name:
            save_memory("name", name)
            return f"Va bene, ricorderò che ti chiami {name}."

    if low.startswith("il nostro obiettivo è "):
        goal = user_msg[24:].strip()
        if goal:
            save_memory("goal", goal)
            return "Perfetto, ho salvato il nostro obiettivo."

    if low.startswith("il progetto è "):
        project = user_msg[14:].strip()
        if project:
            save_memory("project", project)
            return "Perfetto, ho salvato il progetto."

    if low.startswith("ricorda che "):
        note = user_msg[12:].strip()
        if note:
            old = get_memory("notes")
            new_notes = f"{old} | {note}" if old else note
            save_memory("notes", new_notes)
            return "Va bene, lo terrò a mente."

    return None


def local_logic(user_msg: str):
    low = user_msg.lower().strip()

    remembered = extract_memory(user_msg)
    if remembered:
        return remembered

    name = get_memory("name")
    goal = get_memory("goal")
    project = get_memory("project")
    notes = get_memory("notes")
    recent = recent_user_messages()

    if "ciao" in low or "salve" in low:
        if name:
            return f"Ciao {name}. Sono Jarvis. Il sito è online e funziono senza PowerShell."
        return "Ciao. Sono Jarvis. Il sito è online e funziono senza PowerShell."

    if "chi sei" in low:
        return "Sono Jarvis, il tuo assistente web con cronologia e memoria locale."

    if "come mi chiamo" in low:
        if name:
            return f"Ti chiami {name}."
        return "Non me l'hai ancora detto chiaramente. Scrivimi: mi chiamo ..."

    if "ti ricordi" in low and "obiettivo" in low:
        if goal:
            return f"Sì. Il nostro obiettivo è: {goal}"
        return "Non ho ancora salvato un obiettivo preciso. Scrivimi: il nostro obiettivo è ..."

    if "ti ricordi" in low and "progetto" in low:
        if project:
            return f"Sì. Il progetto è: {project}"
        return "Non ho ancora salvato il progetto in modo preciso. Scrivimi: il progetto è ..."

    if "ti ricordi" in low and ("cosa abbiamo detto" in low or "cosa ci siamo detti" in low):
        if recent:
            joined = " | ".join(recent[-3:])
            return f"Ricordo gli ultimi messaggi principali: {joined}"
        return "Per ora non ho ancora abbastanza cronologia da riassumere."

    if "cronologia" in low or "memoria" in low:
        response = "Posso salvare nome, obiettivo, progetto e note. Inoltre conservo la cronologia nella sezione dedicata."
        if notes:
            response += f" Note salvate: {notes}"
        return response

    if "online" in low:
        return "Sì, il sito è online e puoi aprirlo senza avviare PowerShell."

    if "powershell" in low:
        return "No, per usare il sito online non serve aprire PowerShell. Serviva solo per svilupparlo in locale."

    if "cosa sai fare" in low:
        return "Posso chattare, salvare cronologia, ricordare alcune informazioni chiave e restare online come sito."

    if "ai" in low or "intelligenza artificiale" in low:
        return "Per ora uso una logica locale avanzata, non un modello AI a pagamento. Però posso ricordare informazioni importanti e rispondere in modo più utile."

    if "progetto" in low:
        if project:
            return f"Il progetto attuale è: {project}"
        return "Stiamo costruendo una web app Jarvis online con cronologia, memoria e grafica migliorabile."

    if "obiettivo" in low or "obbiettivo" in low:
        if goal:
            return f"Il nostro obiettivo è: {goal}"
        return "Il nostro obiettivo generale è creare una web app Jarvis online, utile e più intelligente."

    return "Ho capito il messaggio. Posso ricordare meglio se mi scrivi frasi come: 'mi chiamo ...', 'il nostro obiettivo è ...', 'il progetto è ...', oppure 'ricorda che ...'"


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
