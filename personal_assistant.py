import os
import requests
import json
import time
import sys
import ctypes
from dotenv import load_dotenv
from threading import Thread, Lock
import regex as re

# [PA EMOTION] Import emotion classifier functions
from Utils.emoClassier import predict_emotion, generate_emotion_payload_from_probabilities

# [PA AUDIO] Import Audio2Face utility
from Utils.a2f_utils import send_audio_to_audio2face, load_usd_file, activate_stream_livelink, set_stream_livelink_settings, set_audio_looping

# Import universal audio processing and input helper functions
from Utils.audio_processing_utils import process_response_text_generic, get_user_input

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain.agents import tool, AgentExecutor
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages

load_dotenv()
# Set the Groq API key

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Directories and Files
AUDIO_DIR = r"./responses_output"
USER_PREFS_FILE = "PA_Utils/user_prefs.json"
ERROR_LOG_FILE = "PA_Utils/error_log.txt"
CHAT_HISTORY_FILE = "PA_Utils/chat_history.json"
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CHAT_HISTORY_FILE), exist_ok=True)

NEWS_SERVICE_URL = "http://localhost:5000/news"

# Global emotion tracking variables
current_emotion = "neutral"
emotion_lock = Lock()
emotion_tracking_active = True

def load_user_prefs():
    if os.path.exists(USER_PREFS_FILE):
        with open(USER_PREFS_FILE, 'r') as f:
            return json.load(f)
    return {"favorite_music_genre": "", "preferred_city": "London", "interests": []}

def save_user_prefs(prefs):
    with open(USER_PREFS_FILE, 'w') as f:
        json.dump(prefs, f, indent=4)

user_prefs = load_user_prefs()

def log_error(error_msg):
    with open(ERROR_LOG_FILE, 'a') as f:
        f.write(f"{time.ctime()}: {error_msg}\n")

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_chat_history(chat_history):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(chat_history, f, indent=4)

# VLC initialization
vlc_path = r"C:\Program Files\VideoLAN\VLC"
os.environ["PATH"] += os.pathsep + vlc_path
os.environ["VLC_PLUGIN_PATH"] = os.path.join(vlc_path, "plugins")
dll_path = os.path.join(vlc_path, "libvlc.dll")
if os.path.exists(dll_path):
    try:
        ctypes.CDLL(dll_path)
        print("✅ VLC successfully loaded!")
    except Exception as e:
        print(f"❌ Error loading VLC: {e}")
        log_error(f"Error loading VLC: {e}")
        sys.exit(1)
else:
    print(f"❌ VLC library not found at {dll_path}! Check your VLC installation path.")
    sys.exit(1)

load_dotenv(dotenv_path="pass.env")
email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_PASS")
smtp_host = "smtp.gmail.com"

A2F_BASE_URL = "http://localhost:8011"

# Global music player instance used by all music-related tools.
music_player = None

# ------------------------- Helper Functions -------------------------

def get_location():
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_error(f"Error fetching location: {e}")
        return {"city": user_prefs.get("preferred_city", "London"), "country": "UK"}

def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        log_error(f"Error fetching weather: {e}")
        return "Unable to fetch weather data"

def get_news(query):
    try:
        response = requests.get(f"{NEWS_SERVICE_URL}?query={query}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "success" and data["articles"]:
            articles = data["articles"][:3]
            news_summary = f"Here’s the latest on {query}:\n"
            for i, article in enumerate(articles, 1):
                news_summary += f"{i}. {article['title']} from {article['source']}.\n"
            return news_summary.strip()
        else:
            return f"Sorry, no news found on '{query}'."
    except Exception as e:
        log_error(f"Error fetching news: {e}")
        return f"Unable to fetch news for '{query}'."

def download_music(song_name):
    print(f"🔍 Searching for: {song_name}")
    base_dir = r"Music"
    safe_song_name = "".join(c if c.isalnum() else "_" for c in song_name.lower())
    file_name = f"{safe_song_name}"
    file_path = os.path.join(base_dir, f"{file_name}.mp3")
    print(f"DEBUG: Expected file path: {file_path}")

    if os.path.exists(file_path):
        print(f"🎵 Song already downloaded at: {file_path}")
        return file_path

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '64',
        }],
        'outtmpl': os.path.join(base_dir, file_name),
        'quiet': False,
        'default_search': 'ytsearch1',
        'progress_hooks': [
            lambda d: print(f"Download progress: {d.get('status', 'Unknown')} - {d.get('filename', '')}") if d.get('status') else None
        ],
    }
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{song_name}"])
        if not os.path.exists(file_path):
            alternative_path = os.path.join(base_dir, f"{file_name}.mp3.mp3")
            if os.path.exists(alternative_path):
                os.rename(alternative_path, file_path)
                print(f"Renamed {alternative_path} to {file_path}")
            else:
                raise FileNotFoundError(f"Downloaded file not found at {file_path} or {alternative_path}")
        print(f"✅ Downloaded to: {file_path}")
        return file_path
    except Exception as e:
        print(f"❌ Error downloading music: {e}")
        log_error(f"Error downloading music: {e}")
        raise

# Music control functions used by the music tools.
def play_music_file(file_path):
    global music_player
    import vlc
    if not os.path.exists(file_path):
        return "❌ File not found!"
    if music_player is not None:
        music_player.stop()
    music_player = vlc.MediaPlayer(file_path)
    music_player.play()
    time.sleep(1)  # Brief wait to allow playback to start
    if music_player.is_playing():
        return "Playing now."
    else:
        return "Error: Playback failed."

def pause_music_func():
    global music_player
    if music_player is not None and music_player.is_playing():
        music_player.pause()
        return "Music paused."
    return "No music is playing to pause."

def resume_music_func():
    global music_player
    if music_player is not None:
        music_player.play()
        return "Music resumed."
    return "No music to resume."

def stop_music_func():
    global music_player
    if music_player is not None:
        music_player.stop()
        return "Music stopped."
    return "No music is playing."

def play_again_func():
    global music_player
    if music_player is not None:
        music_player.stop()
        music_player.play()
        return "Replaying the current track."
    return "No track available to replay."

def send_email_with_attachments(to_email, subject, body_content, attachments=[]):
    try:
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"] = email_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body_content)
        for file_path in attachments:
            with open(file_path, "rb") as file:
                file_data = file.read()
                file_name = os.path.basename(file_path)
                msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)
        import smtplib
        with smtplib.SMTP_SSL(smtp_host, 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        return f"Email sent successfully to {to_email}."
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        log_error(f"Error sending email: {e}")
        return f"Error sending email: {str(e)}"

def continuous_emotion_detection():
    global current_emotion, emotion_tracking_active
    from fer import FER
    detector = FER(mtcnn=True)
    import cv2
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam for continuous tracking.")
        log_error("Could not open webcam for continuous tracking.")
        return

    while emotion_tracking_active:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Could not read frame. Retrying...")
            time.sleep(1)
            continue

        try:
            result = detector.detect_emotions(frame)
            if result and len(result) > 0:
                emotions = result[0]["emotions"]
                dominant_emotion = max(emotions, key=emotions.get)
                with emotion_lock:
                    current_emotion = dominant_emotion
                print(f"Current emotion: {current_emotion} ({emotions[dominant_emotion]:.2f})")
            else:
                with emotion_lock:
                    current_emotion = "neutral"
                print("No face detected. Assuming neutral emotion.")
        except Exception as e:
            print(f"❌ Error in continuous emotion detection: {e}")
            log_error(f"Error in continuous emotion detection: {e}")
            with emotion_lock:
                current_emotion = "neutral"

        time.sleep(1)

    cap.release()
    print("Emotion tracking stopped.")

# ------------------ Two-Phase Audio Processing for Personal Assistant ------------------
def process_response_text_pa(response_text: str, default_delay: float = 1.0):
    process_response_text_generic(
        response_text=response_text,
        prefix="PA_response_segment",
        a2f_base_url=A2F_BASE_URL,
        audio_dir=AUDIO_DIR,
        send_audio_func=send_audio_to_audio2face,
        predict_emotion_func=predict_emotion,
        generate_payload_func=generate_emotion_payload_from_probabilities,
        default_delay=default_delay
    )

# ------------------------- Tool Definitions -------------------------

@tool
def weather_tool(input: str = "") -> str:
    """Provides current weather information."""
    try:
        loc = get_location()
        city = loc.get("city", user_prefs.get("preferred_city", "London"))
        weather_info = get_weather(city)
        return f"The weather in {city}, {loc.get('country')} is {weather_info}."
    except Exception as e:
        log_error(f"Error in weather_tool: {e}")
        return "Unable to retrieve weather information at the moment."

@tool
def news_tool(input: str = "") -> str:
    """Provides the latest news for a given topic."""
    topic = input.strip() if input.strip() != "" else "latest"
    try:
        return get_news(topic)
    except Exception as e:
        log_error(f"Error in news_tool: {e}")
        return "Unable to fetch news at the moment."

@tool
def music_play_tool(input: str = "") -> str:
    """
    Downloads and plays a requested song.
    Expects input as the song name.
    """
    song_name = input.strip()
    if song_name == "":
        return "Please specify a song name to play."
    try:
        file_path = download_music(song_name)
        result = play_music_file(file_path)
        return f"Playing '{song_name}' now. {result}"
    except Exception as e:
        log_error(f"Error in music_play_tool: {e}")
        return f"Error playing music: {e}"

@tool
def music_pause_tool(input: str = "") -> str:
    """Pauses the currently playing song."""
    try:
        return pause_music_func()
    except Exception as e:
        log_error(f"Error in music_pause_tool: {e}")
        return f"Error pausing music: {e}"

@tool
def music_resume_tool(input: str = "") -> str:
    """Resumes the paused song."""
    try:
        return resume_music_func()
    except Exception as e:
        log_error(f"Error in music_resume_tool: {e}")
        return f"Error resuming music: {e}"

@tool
def music_stop_tool(input: str = "") -> str:
    """Stops the currently playing song."""
    try:
        return stop_music_func()
    except Exception as e:
        log_error(f"Error in music_stop_tool: {e}")
        return f"Error stopping music: {e}"

@tool
def music_playagain_tool(input: str = "") -> str:
    """Replays the current track from the beginning."""
    try:
        return play_again_func()
    except Exception as e:
        log_error(f"Error in music_playagain_tool: {e}")
        return f"Error replaying music: {e}"

@tool
def email_tool(input: str = "") -> str:
    """
    Sends an email. Expects input in the format:
    recipient:email_address; subject:Your Subject; message:Your message here.
    """
    try:
        parts = [part.strip() for part in input.split(";")]
        details = {}
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                details[key.strip().lower()] = value.strip()
        recipient = details.get("recipient")
        subject = details.get("subject", "No Subject")
        message = details.get("message", "")
        if not recipient or not message:
            return "Please provide both recipient and message details in the correct format."
        result = send_email_with_attachments(recipient, subject, message, attachments=[])
        return result
    except Exception as e:
        log_error(f"Error in email_tool: {e}")
        return f"Error sending email: {e}"

# ------------------------- Agent Creation -------------------------
def create_pa_agent() -> AgentExecutor:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=500,
        timeout=30,
        max_retries=2,
    )
    # Bind all tools including the new music control tools.
    llm_with_tools = llm.bind_tools([
        weather_tool,
        news_tool,
        music_play_tool,
        music_pause_tool,
        music_resume_tool,
        music_stop_tool,
        music_playagain_tool,
        email_tool
    ])
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a friendly personal assistant capable of providing weather updates, the latest news, controlling music playback (play, pause, resume, stop, replay), and sending emails. "
         "Respond clearly and concisely, and make use of the available tools as needed."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
            "chat_history": lambda x: x["chat_history"],
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[
            weather_tool,
            news_tool,
            music_play_tool,
            music_pause_tool,
            music_resume_tool,
            music_stop_tool,
            music_playagain_tool,
            email_tool
        ],
        verbose=True
    )
    return agent_executor

def main():
    print("Starting Personal Assistant...")
    emotion_thread = Thread(target=continuous_emotion_detection, daemon=True)
    emotion_thread.start()

    try:
        load_usd_file()
        activate_stream_livelink()
        set_stream_livelink_settings()
        set_audio_looping()
    except Exception as e:
        print(f"[PA] API setup failed: {e}")
        log_error(f"API setup failed: {e}")

    pa_agent = create_pa_agent()
    chat_history = []

    welcome_message = (
        "Hello! Welcome to your Personal Assistant. I can provide weather updates, the latest news, control music playback (play, pause, resume, stop, replay), and send emails. "
        "How may I assist you today?"
    )
    print("[PA] Assistant:", welcome_message)
    process_response_text_pa(welcome_message)

    while True:
        user_input = get_user_input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("[PA] Exiting Personal Assistant. Goodbye!")
            break
        try:
            result = pa_agent.invoke({"input": user_input, "chat_history": chat_history})
            response_text = result["output"]
            print("[PA] Raw Response:", response_text)
            process_response_text_pa(response_text)
            segments = re.split(r'(?<=[.!?])\s+', response_text)
            segments = [seg for seg in segments if seg.strip() != ""]
            for i, segment in enumerate(segments, start=1):
                prob, emotion_label = predict_emotion(segment)
                print(f"[PA] Segment {i}: \"{segment}\" - Emotion: {emotion_label} with probabilities: {prob}")
            chat_history.extend(
                [{"role": "user", "content": user_input}, {"role": "assistant", "content": response_text}]
            )
        except Exception as e:
            print(f"[PA] Error during agent execution: {e}")
            log_error(f"Error during PA agent execution: {e}")

if __name__ == "__main__":
    main()
