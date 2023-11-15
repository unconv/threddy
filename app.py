#!/usr/bin/env python3

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import tempfile
import openai
import uuid
import os

import config
import db

app = Flask(__name__)

database_file = "database.json"
database = db.load(database_file)
settings = config.load("settings.json")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new_chat", methods=["POST"])
def new_chat():
    chat_id = str(uuid.uuid4())

    thread = openai.beta.threads.create()

    chat = {
        "id": chat_id,
        "thread_id": thread.id,
        "title": "Untitled chat",
    }

    database["conversations"][chat_id] = chat
    db.save(database_file, database)

    return render_template(
        "chat_button.html",
        chat=chat
    )

@app.route("/load_chat/<chat_id>")
def load_chat(chat_id):
    thread_id = database["conversations"][chat_id]["thread_id"]

    messages = openai.beta.threads.messages.list(
        thread_id=thread_id,
        order="desc",
    )

    message_list = []

    for message in messages.data:
        message_list.append({
            "role": message.role,
            "content": message.content[0].text.value
        })

    message_list = reversed(message_list)

    return render_template(
        "messages.html",
        messages=message_list,
        chat_id=chat_id
    )

@app.route("/conversations")
def conversations():
    chats = database["conversations"].values()
    return render_template("conversations.html", conversations=chats)

@app.route("/send_message", methods=["POST"])
def send_message():
    chat_id = request.form["chat_id"]
    file_ids = []

    if "file" in request.files:
        file = request.files["file"]
        if file.filename != "":
            temp_dir = tempfile.mkdtemp()

            filename = secure_filename(file.filename)
            file_path = os.path.join(temp_dir, filename)

            print(f"Saving to {file_path}")

            file.save(file_path)
            uploaded_file = openai.files.create(
                file=openai.file_from_path(file_path),
                purpose="assistants",
            )

            file_ids.append(uploaded_file.id)

    message = {
        "role": "user",
        "content": request.form["message"]
    }

    chat = database["conversations"][chat_id]

    openai.beta.threads.messages.create(
        thread_id=chat["thread_id"],
        role=message["role"],
        content=message["content"],
        file_ids=file_ids,
    )

    return render_template(
        "user_message.html",
        chat_id=chat_id,
        message=message
    )

@app.route("/get_response/<chat_id>")
def get_response(chat_id):
    chat = database["conversations"][chat_id]

    run = openai.beta.threads.runs.create(
        thread_id=chat["thread_id"],
        assistant_id=settings["assistant_id"],
    )

    while True:
        run = openai.beta.threads.runs.retrieve(
            run_id=run.id,
            thread_id=chat["thread_id"]
        )

        if run.status not in ["queued", "in_progress", "cancelling"]:
            break

    messages = openai.beta.threads.messages.list(
        thread_id=chat["thread_id"],
        order="desc",
        limit=1,
    )

    message = {
        "role": "assistant",
        "content": messages.data[0].content[0].text.value
    }

    return render_template(
        "assistant_message.html",
        message=message
    )

app.run(debug=True)
