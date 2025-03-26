import re
import webbrowser
import pyttsx3
import datetime
import speech_recognition as sr

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

    # Check if the query starts with "google" to initiate a web search
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
        hour = datetime.datetime.now().strftime("%H")
        min = datetime.datetime.now().strftime("%M")
        current_time = f"Ma'am, the time is {hour} hours and {min} minutes."
        say(current_time)
        return current_time

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

        # Check for code in the response and format it accordingly
        if "```" in response_text or "Here's the code" in response_text.lower():
            response_text = response_text.replace("```", "")
            response_text = f"<pre><code>{response_text}</code></pre>"

        chatStr += f"{response_text}\n"
        return response_text
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, there was an error with the request."

def say(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    # Select a female voice
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower():  # "Zira" is a common Windows female voice
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
            query = r.recognize_google(audio, language="en-in")
            print(f"User said: {query}")
            return query
        except sr.UnknownValueError:
            return "Sorry, I did not catch that."
        except sr.RequestError as e:
            return "Sorry, there was an error with the request."

def search_web(query):
    search_query = query.strip()
    
    if search_query:
        try:
            # Initialize the Google Custom Search API service
            service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
            
            # Make the API request with the search query
            response = service.cse().list(q=search_query, cx=GOOGLE_CSE_ID).execute()
            
            # Check if there are results
            if 'items' in response and len(response['items']) > 0:
                first_result = response['items'][0]
                link = first_result.get('link')
                
                # Open the first result in the web browser
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
    global listening_mode
    print("Listening for trigger...")
    while True:
        query = takeCommand().lower()
        if "nova listen" in query:
            say("Listening mode activated.")
            listening_mode = True
            break
        elif "nova chat" in query:
            say("Chat mode activated.")
            global chat_mode
            chat_mode = True
            break

def reset_modes():
    global listening_mode, chat_mode
    listening_mode = False
    chat_mode = False
    listen_for_trigger()

# Flask route to render HTML
@app.route('/')
def home():
    return render_template('index.html')

# Flask route to handle chat requests
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

            if "ok thank you" in query:
                say("Goodbye!")
                break

            if "play my favourite music" in query:
                musicPath = "https://www.youtube.com/watch?v=gJLVTKhTnog"
                say("Ok ma'am, wait.")
                webbrowser.open(musicPath)
                reset_modes()
                continue

            elif "open youtube" in query:
                Path = "https://www.youtube.com/"
                say("Ok ma'am, wait.")
                webbrowser.open(Path)
                reset_modes()
                continue

            elif "the time" in query:
                hour = datetime.datetime.now().strftime("%H")
                min = datetime.datetime.now().strftime("%M")
                say(f"Ma'am, the time is {hour} hours and {min} minutes.")
                reset_modes()
                continue

            elif "nova quit" in query:
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
