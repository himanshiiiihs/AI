import re
import webbrowser
import pyttsx3
import datetime
import speech_recognition as sr
import openai
from config import apikey
from responses import predefined_responses
import os
from googleapiclient.discovery import build
from flask import Flask, request, jsonify, render_template

# Flask app setup
app = Flask(__name__)

# Google API and Custom Search Engine (CSE) setup
GOOGLE_API_KEY = 'AIzaSyBLnLWePnIahg2Qhz1f2Pj2K2FH9UHzC9A'
GOOGLE_CSE_ID = '144a23a7e8a1c4653'

chatStr = ""
listening_mode = False
chat_mode = False

def chat(query):
    global chatStr
    query = query.lower()

    if query.startswith(("google", "open")):
        search_query = query.replace("google", "", 1).replace("open", "", 1).strip()
        if search_query:
            if search_web(search_query):
                return f"Searching Google for '{search_query}'."
            else:
                return "Sorry, I couldn't find any results."

    if "play my favourite music" in query:
        musicPath = "https://www.youtube.com/watch?v=gJLVTKhTnog"
        say("Ok ma'am, wait.")
        webbrowser.open(musicPath)
        return "Playing your favorite music."

    if "open youtube" in query:
        Path = "https://www.youtube.com/"
        say("Ok ma'am, wait.")
        webbrowser.open(Path)
        return "Opening YouTube."

    if "the time" in query:
        current_time = datetime.datetime.now().strftime("%H hours and %M minutes")
        say(f"Ma'am, the time is {current_time}.")
        return f"Ma'am, the time is {current_time}."

    if query in predefined_responses:
        response_text = predefined_responses[query]
        chatStr += f"Himanshi: {query}\nNova: {response_text}\n"
        return response_text

    openai.api_key = apikey
    chatStr += f"Himanshi: {query}\nNova: "

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are Nova, an AI assistant created by Himanshi."}, {"role": "user", "content": query}],
            max_tokens=256,
            temperature=0.7,
        )
        response_text = response["choices"][0]["message"]["content"].strip()
        chatStr += f"{response_text}\n"
        return response_text
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, there was an error with the request."

def say(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.say(text)
    engine.runAndWait()

def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        try:
            print("Recognizing...")
            return r.recognize_google(audio, language="en-in")
        except sr.UnknownValueError:
            return "Sorry, I did not catch that."
        except sr.RequestError:
            return "Sorry, there was an error with the request."

def search_web(query):
    search_query = query.strip()
    if search_query:
        try:
            service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
            response = service.cse().list(q=search_query, cx=GOOGLE_CSE_ID).execute()
            if 'items' in response and response['items']:
                link = response['items'][0].get('link')
                say("Opening the first Google search result.")
                webbrowser.open(link)
                return True
            else:
                say("No results found.")
                return False
        except Exception as e:
            print(f"Error during Google search: {e}")
            say("There was an issue with the search request.")
            return False
    else:
        say("Please provide a search query.")
        return False

def listen_for_trigger():
    global listening_mode, chat_mode
    print("Listening for trigger...")
    while True:
        query = takeCommand().lower()
        if "nova listen" in query:
            say("Listening mode activated.")
            listening_mode = True
            break
        elif "nova chat" in query:
            say("Chat mode activated.")
            chat_mode = True
            break

def reset_modes():
    global listening_mode, chat_mode
    listening_mode = False
    chat_mode = False
    listen_for_trigger()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_route():
    user_query = request.form.get('query')
    speak = request.form.get('speak')
    if user_query:
        response = chat(user_query)
        if speak == "true" and response:
            say(response)
        return jsonify({"response": response})
    return jsonify({"response": "Sorry, I didn't understand your request."})

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print('Welcome to Nova A.I')
        say("Hello ma'am, I am Nova created by Himanshi. How may I assist you?")
        webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)
    listen_for_trigger()
    while True:
        if not listening_mode and not chat_mode:
            reset_modes()
        if chat_mode:
            query = input("Type your message: ").lower()
            if "ok thank you" in query or "nova quit" in query:
                say("Goodbye!")
                break
            elif "reset chat" in query:
                chatStr = ""
                reset_modes()
                continue
            else:
                response = chat(query)
                if response:
                    say(response)
                reset_modes()
        elif listening_mode:
            query = takeCommand().lower()
            if "ok thank you" in query or "nova quit" in query:
                say("Goodbye!")
                break
            response = chat(query)
            if response:
                say(response)
            reset_modes()