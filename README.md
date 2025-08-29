# Private Chat Upgraded

A real-time, anonymous, and private chat application built with Flask, Socket.IO, and Redis. Create temporary chat rooms to talk with others securely.

*(Consider adding a screenshot of your application here!)*

## Features

- **Anonymous Chat:** No login or personal information required, just pick a name.
- **Private Rooms:** Create a private room and share the unique 4-letter code.
- **Real-Time Communication:** Messages appear instantly thanks to WebSockets (Socket.IO).
- **Typing Indicators:** See when other users are typing.
- **Temporary & Secure:** Rooms and messages are deleted from the server as soon as the last person leaves.

## Tech Stack

- **Backend:** Flask, Flask-SocketIO
- **Database:** Redis (for message history and room management)
- **Frontend:** HTML, CSS, JavaScript
- **Deployment:** Gunicorn, Eventlet

## Running Locally

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ziaboy123/Private-Chat-Upgraded.git
    cd Private-Chat-Upgraded
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**
    Create a file named `.env` in the root directory and add the following. You will also need a local Redis server running.
    ```
    SECRET_KEY=a_very_long_and_random_secret_string
    REDIS_URL=redis://localhost:6379
    ```

4.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will be available at `http://127.0.0.1:5000`.
