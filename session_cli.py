import os
import time
import json
import threading
import pexpect
import uuid
from flask import Flask, session, request, jsonify, render_template
#from flask_cors import CORS

import sys

sys.stdout.reconfigure(line_buffering=True)  # Python 3.7+

app = Flask(__name__)
#app.secret_key="simplesecretkey"
app.config["SECRET_KEY"] ="simplesecretkey"
#CORS(app,supports_credentials=True)  # This enables CORS for all routes by default

SESSION_TIMEOUT = 600  # 10 minutes
CHECK_INTERVAL = 60  # Cleanup every 60 seconds
SESSION_FILE = "sessions.json"  # Save sessions to this file

maxima_sessions = {}  # Stores Maxima processes and metadata

def save_sessions():
    """Saves active sessions to a JSON file."""
    with open(SESSION_FILE, "w") as f:
        json.dump(
            {
                sid: {
                    "last_active": data["last_active"],
                    "history": data["history"],
                    "outputs": data["outputs"],  # Save command outputs too
                }
                for sid, data in maxima_sessions.items()
            },
            f,
        )

def load_sessions():
    """Loads sessions from a JSON file (if available)."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            try:
                data = json.load(f)
                for sid, metadata in data.items():
                    maxima_sessions[sid] = {
                        "process": pexpect.spawn("maxima", encoding='utf-8', timeout=10),
                        "last_active": metadata["last_active"],
                        "history": metadata.get("history", []),
                        "outputs": metadata.get("outputs", []),  # Load command outputs
                    }
                    maxima_proc = maxima_sessions[sid]["process"]
                    print("Before------>:", maxima_proc.before)
                    maxima_sessions[sid]["process"].expect(r"\(%i[0-9]+\)")
            except json.JSONDecodeError:
                pass  # Ignore corrupted files

def cleanup_sessions():
    """Runs periodically to remove inactive sessions."""
    while True:
        time.sleep(CHECK_INTERVAL)
        now = time.time()
        to_remove = []

        for session_id, data in maxima_sessions.items():
            if now - data["last_active"] > SESSION_TIMEOUT:
                print(f"Terminating inactive session: {session_id}")
                data["process"].terminate()
                to_remove.append(session_id)

        for session_id in to_remove:
            del maxima_sessions[session_id]

        save_sessions()  # Save updated session state

# Load sessions on startup
load_sessions()

# Start cleanup thread
threading.Thread(target=cleanup_sessions, daemon=True).start()

def send_command(proc, command):
    command = command.rstrip(";") + ";"
    proc.sendline(command)
    proc.expect(r"\(%o[0-9]+\).*")
    return proc.before + proc.after

@app.route("/start", methods=["GET"])
def start_maxima():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    session_id = session["session_id"]

    if session_id not in maxima_sessions:
        maxima_sessions[session_id] = {
            "process": pexpect.spawn("maxima", encoding='utf-8', timeout=10),
            "last_active": time.time(),
            "history": [],
            "outputs": [],  # Initialize output storage
        }
        maxima_proc = maxima_sessions[session_id]["process"]
        maxima_sessions[session_id]["process"].expect(r"\(%i[0-9]+\)")
        save_sessions()  # Save after starting a session

    return jsonify({"message": "Maxima session started", "session_id": session_id})

@app.route("/get", methods=["GET"])
def pexecute():
    session_id = session.get("session_id")
    print("session id", session_id)
    if not session_id or session_id not in maxima_sessions:
        return jsonify({"error": "No active Maxima session"}), 400

    maxima_proc = maxima_sessions[session_id]["process"]
    command = request.args.get("command", "diff(x*x,x);")
    output = send_command(maxima_proc,command)
    print("OUTPUT", output)
    # Update session metadata
    maxima_sessions[session_id]["last_active"] = time.time()
    maxima_sessions[session_id]["history"].append(command)
    maxima_sessions[session_id]["outputs"].append(output)  # Save output
    
    save_sessions()  # Save after executing a command

    return jsonify({"output": output})

@app.route("/execute", methods=["POST", "OPTIONS"])
def execute():

    if request.method == 'OPTIONS':
        # Handle preflight request
        print("HANDLE PREFLIGHT REQUEST")
        response = Flask.response_class(status=204)  # No content
        response.headers["Access-Control-Allow-Origin"] = "*"  # Change to your frontend's URL
        response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response,200
        #return '', 200  # Respond with no content but 200 OK

    print("HANDLE POST!!!!!", session.get("session_id"))
    session_id = session.get("session_id")
    if not session_id or session_id not in maxima_sessions:
        return jsonify({"error": "No active Maxima session"}), 400

    maxima_proc = maxima_sessions[session_id]["process"]
    command = request.json.get("command", "")
    print(f"EXECUTE COMMAND = {command}")    
    output = send_command(maxima_proc,command)

    # Update session metadata
    maxima_sessions[session_id]["last_active"] = time.time()
    maxima_sessions[session_id]["history"].append(command)
    maxima_sessions[session_id]["outputs"].append(output)  # Save output
    
    save_sessions()  # Save after executing a command

    return jsonify({"output": output})

@app.route("/end", methods=["GET"])
def end_session():
    session_id = session.get("session_id")
    if session_id in maxima_sessions:
        maxima_sessions[session_id]["process"].terminate()
        del maxima_sessions[session_id]
        save_sessions()  # Save after ending a session

    session.pop("session_id", None)
    return jsonify({"message": "Maxima session ended"})

@app.route("/")
def home():
    return render_template("frontend.html")  # Flask looks in /templates/index.html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Fixed to port 5000

