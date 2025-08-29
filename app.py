from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import random
import os
import redis
import json
from string import ascii_uppercase
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "a_default_secret_key_for_development")

# Connect to Redis
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(redis_url)
socketio = SocketIO(app, message_queue=redis_url)

def generate_unique_code(length):
    while True:
        code = "".join(random.choices(ascii_uppercase, k=length))

        # Check if the room code already exists in Redis
        if not redis_client.exists(f"room:{code}"):
            break

    return code

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)

        room=code
        if create:
            room = generate_unique_code(4)
            redis_client.hset(f"room:{room}", "members", 0)
        elif not redis_client.exists(f"room:{room}"):
            return render_template("home.html", error="Room does not exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or not redis_client.exists(f"room:{room}"):
        return redirect(url_for("home"))

    raw_messages = redis_client.lrange(f"room:{room}:messages", 0, -1)
    messages = [json.loads(m) for m in raw_messages]
    return render_template("room.html", code=room, messages=messages)

@socketio.on("message")
def message(data):
    room = session.get("room")
    if not redis_client.exists(f"room:{room}"):
        return

    content = {
        "type": "message",
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    # Store message in Redis list and keep only the last 100 messages
    redis_client.rpush(f"room:{room}:messages", json.dumps(content))
    redis_client.ltrim(f"room:{room}:messages", -100, -1)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("typing")
def typing():
    """Broadcasts to other users that a user is typing."""
    room = session.get("room")
    name = session.get("name")
    if room and name:
        emit("user_typing", {"name": name}, to=room, skip_sid=request.sid)

@socketio.on("stop_typing")
def stop_typing():
    """Broadcasts to other users that a user has stopped typing."""
    room = session.get("room")
    name = session.get("name")
    if room and name:
        emit("user_stop_typing", {"name": name}, to=room, skip_sid=request.sid)

@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if not redis_client.exists(f"room:{room}"):
        leave_room(room)
        return

    join_room(room)
    status_msg = {"type": "status", "msg": f"{name} has entered the room"}
    emit("status", {"msg": f"{name} has entered the room"}, to=room)
    
    # Update member count and store status message
    redis_client.hincrby(f"room:{room}", "members", 1)
    redis_client.rpush(f"room:{room}:messages", json.dumps(status_msg))
    redis_client.ltrim(f"room:{room}:messages", -100, -1)
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if not room or not name:
        return

    if redis_client.exists(f"room:{room}"):
        status_msg = {"type": "status", "msg": f"{name} has left the room"}
        emit("status", {"msg": f"{name} has left the room"}, to=room)
        redis_client.rpush(f"room:{room}:messages", json.dumps(status_msg))
        redis_client.ltrim(f"room:{room}:messages", -100, -1)

        # Decrement members and delete room if it's empty
        new_member_count = redis_client.hincrby(f"room:{room}", "members", -1)
        if new_member_count <= 0:
            redis_client.delete(f"room:{room}", f"room:{room}:messages")
            print(f"Room {room} deleted.")

    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
