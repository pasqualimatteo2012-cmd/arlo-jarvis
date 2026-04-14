from flask import Flask, send_from_directory, request, jsonify
from datetime import datetime
import os

app = Flask(__name__, static_folder='static')

MEMORY_FILE = "memory/2026-04-13.md"

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get("message", "").lower()

    if "ciao" in user_msg:
        response = "Ciao. Sono Jarvis. Dimmi pure."
    elif "ti ricordi" in user_msg or "progetto" in user_msg:
        response = "Per ora ricordo solo quello che salviamo nel file di memoria. Non sono ancora collegato a una vera intelligenza artificiale."
    elif "chi sei" in user_msg:
        response = "Sono Jarvis, il tuo assistente locale."
    else:
        response = "Ho ricevuto il tuo messaggio, ma devo ancora essere collegato a un motore AI vero."

    save_memory(user_msg, response)

    return jsonify({"response": response})

def save_memory(user, bot):
    os.makedirs("memory", exist_ok=True)

    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}]\n")
        f.write(f"USER: {user}\n")
        f.write(f"BOT: {bot}\n")

if __name__ == "__main__":
    print("Avvio Flask...")
    app.run(host="127.0.0.1", port=5000, debug=True)

