
import os
import re
from flask import Flask, request, jsonify, render_template
from Utils import a2f_utils
from Utils.a2f_utils import load_usd_file, activate_stream_livelink, set_stream_livelink_settings, set_audio_looping, send_audio_to_audio2face, set_audio2face_root_path # Added set_audio2face_root_path import
from CRA_Utils import database
import sqlite3
from cafe_receptionist import show_menu, create_cafe_kiosk_agent, process_response_text
from personal_assistant import create_pa_agent
from nurse_agent import create_nurse_agent, process_response_text_nurse
from Utils.audio_processing_utils import process_response_text_generic
from Utils.emoClassier import predict_emotion, generate_emotion_payload_from_probabilities
from dotenv import load_dotenv

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
CURRENT_USER_ID = None
INPUT_MODE = "text"

DB_PATH = os.path.join(os.path.dirname(__file__), "DB", "database.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) # Ensure DB directory exists
database.get_connection = lambda: sqlite3.connect(DB_PATH, check_same_thread=False)
database.initialize_database()

# Global variables to manage conversation flow.
conversation_state = "awaiting_mobile"  # States: awaiting_mobile, awaiting_user_details, awaiting_order
mobile_number = None
# Use separate chat histories for each agent type if running concurrently or switching
chat_history_cafe = []
chat_history_pa = []
chat_history_nurse = []

# Define Audio Directory Consistently (using forward slashes recommended)
AUDIO_DIR = os.path.abspath("./responses_output").replace("\\", "/")
os.makedirs(AUDIO_DIR, exist_ok=True)
# Set the AUDIO_DIR in a2f_utils if it relies on it (or pass it)
a2f_utils.AUDIO_DIR = AUDIO_DIR

app = Flask(__name__, template_folder=".", static_folder="assets", static_url_path="/assets")

# ------------------ Routes ------------------

@app.route("/")
def home():
    return render_template("./assets/html/index.html")

@app.route("/agents")
def agents():
    return render_template("./assets/html/agents.html")

@app.route("/ar")
def index():
    global chat_history_cafe # Reset cafe history on accessing the page
    chat_history_cafe = []
    return render_template("./assets/html/agenticReciptionist.html")

@app.route("/pa")
def personal_assistant():
    global chat_history_pa # Reset PA history
    chat_history_pa = []
    return render_template("./assets/html/pa.html")

@app.route("/agenticNurse")
def agentic_nurse():
    global chat_history_nurse # Reset Nurse history
    chat_history_nurse = []
    return render_template("./assets/html/agenticNurse.html")

# Start of the Cafe Agent
agent_executor = create_cafe_kiosk_agent()

@app.route("/welcome", methods=["GET"])
def welcome():
    global conversation_state, chat_history_cafe
    conversation_state = "awaiting_mobile" # Reset state on welcome
    chat_history_cafe = []
    welcome_message = "Welcome to Cafe {Placeholder}! Please provide your mobile number."
    process_response_text_generic(
        response_text=welcome_message,
        prefix="welcome_segment",
        a2f_base_url=a2f_utils.A2F_BASE_URL, 
        audio_dir=AUDIO_DIR,
        send_audio_func=send_audio_to_audio2face,
        predict_emotion_func=predict_emotion,
        generate_payload_func=generate_emotion_payload_from_probabilities
    )
    return jsonify({"response": welcome_message})

@app.route("/chat", methods=["POST"])
def chat():
    global conversation_state, CURRENT_USER_ID, mobile_number, chat_history_cafe
    data = request.get_json()
    user_input = data.get("user_input", "").strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    if conversation_state == "awaiting_mobile":
        mobile_number = user_input
        user = database.get_user_by_phone(mobile_number)
        if user:
            CURRENT_USER_ID = user[1]
            conversation_state = "awaiting_order"
            response_text = f"Welcome back, {user[2]}! What would you like today?<br/>{show_menu.invoke('')}"
        else:
            conversation_state = "awaiting_user_details"
            response_text = ("It seems you're a new user. Please provide your details "
                             "in the format: first_name,last_name,email")
        # Process response for TTS/A2F
        process_response_text(response_text) # Use cafe_receptionist's process function
        return jsonify({"response": response_text})

    elif conversation_state == "awaiting_user_details":
        try:
            first_name, last_name, email = [s.strip() for s in user_input.split(",")]
        except Exception:
            response_text = "Invalid format. Please provide details in the format: first_name,last_name,email"
            process_response_text(response_text)
            return jsonify({"response": response_text})
        CURRENT_USER_ID = database.get_next_user_id()
        database.add_user(CURRENT_USER_ID, first_name, last_name, email, mobile_number)
        conversation_state = "awaiting_order"
        response_text = f"User registered successfully, welcome {first_name}! What would you like today?<br/>{show_menu.invoke('')}"
        process_response_text(response_text)
        return jsonify({"response": response_text})

    elif conversation_state == "awaiting_order":
        from langchain_core.messages import HumanMessage, AIMessage
        if user_input.lower().startswith("yes,"):
            from cafe_receptionist import confirm_order
            import cafe_receptionist
            cafe_receptionist.CURRENT_USER_ID = CURRENT_USER_ID

            result_text = confirm_order(user_input)
            process_response_text(result_text) # Process confirmation/error message
            chat_history_cafe.extend([HumanMessage(content=user_input), AIMessage(content=result_text)])
            return jsonify({"response": result_text})
        else:
            # Ensure chat history is passed correctly
            result = agent_executor.invoke({"input": user_input, "chat_history": chat_history_cafe})
            response_text = result["output"]
            process_response_text(response_text) # Process agent's response
            # Split the response into segments for display if needed, emotion check is inside process_response_text
            segments = re.split(r'(?<=[.!?])\s+', response_text)
            segments = [seg for seg in segments if seg.strip()]
            # Update chat history *after* successful invocation and processing
            chat_history_cafe.extend([HumanMessage(content=user_input), AIMessage(content=response_text)])
            display_response = "<br/>".join(segments) # Use segmented for display if preferred
            return jsonify({"response": display_response}) # Send segmented or full back
    else:
        response_text = "Unexpected conversation state."
        process_response_text(response_text) # Process error message
        return jsonify({"response": response_text})

@app.route("/chef_dashboard")
def chef_dashboard():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM PurchaseHistory")
    purchase_history = cursor.fetchall()
    conn.close()
    return render_template("./assets/html/chef_dashboard.html", users=users, purchase_history=purchase_history)

# Start of the PA Agent
pa_agent = create_pa_agent()

@app.route("/welcome_pa", methods=["GET"])
def welcome_pa():
    global chat_history_pa
    chat_history_pa = [] # Reset PA history on welcome
    welcome_message = "Hello! Welcome to the MetaHuman experience. I’m your assistant. I can help with weather, music, emails, news, or just chat. I’ll watch your mood and adjust if you seem unhappy!"
    process_response_text_generic(
        response_text=welcome_message,
        prefix="welcome_pa_segment",
        a2f_base_url=a2f_utils.A2F_BASE_URL,
        audio_dir=AUDIO_DIR,
        send_audio_func=send_audio_to_audio2face,
        predict_emotion_func=predict_emotion,
        generate_payload_func=generate_emotion_payload_from_probabilities
    )
    return jsonify({"response": welcome_message})

@app.route("/chat_pa", methods=["POST"])
def chat_pa():
    global chat_history_pa
    data = request.get_json()
    user_input = data.get("user_input", "").strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # Use the PA agent to process the input
    result = pa_agent.invoke({"input": user_input, "chat_history": chat_history_pa})
    response_text = result["output"]
    from langchain_core.messages import HumanMessage, AIMessage
    chat_history_pa.extend([HumanMessage(content=user_input), AIMessage(content=response_text)])

    # Use the PA specific processing function if it exists, otherwise use generic
    # Assuming personal_assistant.py has process_response_text_pa that calls generic
    from personal_assistant import process_response_text_pa
    process_response_text_pa(response_text)

    # Emotion logging is now inside process_response_text_generic called by process_response_text_pa
    # segments = re.split(r'(?<=[.!?])\s+', response_text)
    # segments = [seg for seg in segments if seg.strip()]
    # for i, segment in enumerate(segments, start=1):
    #     prob, emotion_label = predict_emotion(segment)
    #     print(f"[PA] Segment {i}: \"{segment}\" - Emotion: {emotion_label} with probabilities: {prob}") # Already printed inside generic func

    return jsonify({"response": response_text})

# Nurse Agent Routes
nurse_agent = create_nurse_agent()

@app.route("/welcome_na", methods=["GET"])
def welcome_na():
    global chat_history_nurse
    chat_history_nurse = [] # Reset nurse history on welcome
    welcome_message = "Hello I am your Nurse Assistant!I can assist you in providing patient data,medicine stock CRUD  operations,or my insights in patient diagnostics. Happy to answer your query!"
    process_response_text_generic(
        response_text=welcome_message,
        prefix="welcome_na_segment",
        a2f_base_url=a2f_utils.A2F_BASE_URL,
        audio_dir=AUDIO_DIR,
        send_audio_func=send_audio_to_audio2face,
        predict_emotion_func=predict_emotion,
        generate_payload_func=generate_emotion_payload_from_probabilities
    )
    return jsonify({"response": welcome_message})

@app.route("/chat_na", methods=["POST"])
def chat_na():
    global chat_history_nurse
    data = request.get_json()
    user_input = data.get("user_input", "").strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # Use the Nurse agent to process the input
    result = nurse_agent.invoke({"input": user_input, "chat_history": chat_history_nurse})
    response_text = result["output"]

    # Process the response text using the nurse agent's segmentation function
    process_response_text_nurse(response_text)

    # Update nurse agent chat history using the correct format (list of dicts)
    # Check if chat_history_nurse was initialized correctly (should be a list)
    if not isinstance(chat_history_nurse, list):
        chat_history_nurse = [] # Re-initialize if it got corrupted
    chat_history_nurse.extend([{"role": "user", "content": user_input}, {"role": "assistant", "content": response_text}])

    return jsonify({"response": response_text})


# --- Initial A2F Setup ---
print("--- Attempting Initial Audio2Face Setup ---")
try:
    print("1. Loading USD file...")
    load_usd_file()
    print("2. Activating StreamLivelink...")
    activate_stream_livelink()
    print("3. Setting StreamLivelink settings (Enable Audio Stream)...")
    set_stream_livelink_settings()
    print("4. Setting Audio Looping to False...")
    set_audio_looping()
    # --- ADDED CALL TO SET ROOT PATH ---
    print(f"5. Setting Audio2Face Root Path to: {AUDIO_DIR}...")
    set_audio2face_root_path()
    # ------------------------------------
    print("--- Initial Audio2Face Setup Commands Sent ---")
    print("*** IMPORTANT: Ensure Audio2Face app is running and accessible at http://localhost:8011 ***")
except Exception as e:
    print(f"--- ERROR during Initial Audio2Face Setup: {e} ---")
    print("*** Audio2Face features may not work correctly. ***")
    print("*** Please ensure the Audio2Face application is running and accessible at http://localhost:8011 ***")
# --- End Initial A2F Setup ---


if __name__ == "__main__":
    # Note: `debug=True` causes the app to reload, running the setup block twice.
    # Set debug=False for production or when testing single setup execution.
    app.run(host="0.0.0.0", port=5000, debug=True)