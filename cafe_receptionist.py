import datetime
import random

from langchain_groq import ChatGroq
from langchain.agents import tool, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from Utils.emoClassier import predict_emotion, generate_emotion_payload_from_probabilities
from Utils.a2f_utils import send_audio_to_audio2face
import speech_recognition as sr
from CRA_Utils import database

# Global variable (will be updated by the Flask app)
CURRENT_USER_ID = None
A2F_BASE_URL = "http://localhost:8011"
AUDIO_DIR = r"./responses_output"

# Import the universal audio processing helper
from Utils.audio_processing_utils import process_response_text_generic

# ------------------ Cafe Receptionist Tools ------------------

@tool
def show_menu(input: str = "") -> str:
    """Returns the cafe menu."""
    menu = database.get_menu()
    menu_str = "Our menu:\n"
    for item in menu:
        menu_str += f"{item[0]}: {item[1]} - ₹{item[2]:.2f}\n"
    return menu_str

@tool
def recommend_item(preference: str) -> str:
    """
    Recommends a menu item based on keyword matching using a pre-defined map.
    Always includes the product ID.
    """
    menu_map = {
        1: {"name": "Coffee", "price": 2.99, "keywords": ["coffee", "bitter", "hot", "caffeine"]},
        2: {"name": "Tea", "price": 2.49, "keywords": ["tea", "herbal", "hot", "refreshing"]},
        3: {"name": "Sandwich", "price": 5.99, "keywords": ["sandwich", "savory", "spicy", "lunch", "sub"]},
        4: {"name": "Salad", "price": 4.99, "keywords": ["salad", "healthy", "fresh", "vegetable"]},
        5: {"name": "Cake", "price": 3.99, "keywords": ["cake", "sweet", "dessert", "chocolate"]}
    }
    pref_lower = preference.lower()
    for pid, item in menu_map.items():
        for keyword in item["keywords"]:
            if keyword in pref_lower:
                return (f"Based on your preference for something {pref_lower}, I recommend our {item['name']} "
                        f"(product ID: {pid}).If you would like to proceed with this order, please say 'yes,{pid}'.")
    return "Sorry, I couldn't find an item matching your preference. Please review the menu and specify your taste."

@tool
def confirm_order(input: str) -> str:
    """
    Confirms an order based on the input "yes,<product_id>".
    Returns an HTML-formatted response with a clickable payment link.
    """
    global CURRENT_USER_ID
    try:
        confirmation, prod_str = [s.strip() for s in input.split(",")]
        product_id = int(prod_str)
    except Exception:
        return "Invalid input format. Please respond in the format: yes,<product_id>."
    if confirmation.lower() != "yes":
        return "Order cancelled."
    if CURRENT_USER_ID is None:
        return "No user is set."
    seat_no = random.randint(1, 50)
    token_no = random.randint(100, 999)
    date_of_order = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM Products WHERE product_id = ?", (product_id,))
    result = cursor.fetchone()
    if result:
        price = result[0]
        database.add_order(CURRENT_USER_ID, date_of_order, product_id, price, seat_no, token_no)
        payment_link = "https://razorpay.me/@parthnivruttiubhe"
        return (f"Order placed! Your seat number is {seat_no} and your token number is {token_no}."
                f"Please pay ₹{price:.2f} using the following link:{payment_link}"
                "Your order will be confirmed once payment is received.")
    else:
        return "Sorry, the selected item is not available."

# ------------------ Helper Functions ------------------
# In this file, we now use the universal audio processing helper for processing responses.
def process_response_text(response_text: str, default_delay: float = 1.0):
    process_response_text_generic(
        response_text=response_text,
        prefix="CR_response_segment",
        a2f_base_url=A2F_BASE_URL,
        audio_dir=AUDIO_DIR,
        send_audio_func=send_audio_to_audio2face,
        predict_emotion_func=predict_emotion,
        generate_payload_func=generate_emotion_payload_from_probabilities,
        default_delay=default_delay
    )

def play_agent_message(message: str):
    """
    Displays the agent message and processes it for audio generation.
    """
    print("Agent:", message)
    process_response_text(message)

def get_voice_input(prompt_text: str = "You: ", retries: int = 3) -> str:
    """
    Captures voice input from the user and returns the transcribed text.
    Added retry mechanism for network errors.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(prompt_text)
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print("You said: " + text)
        return text
    except sr.UnknownValueError:
        print("Sorry, could not understand audio. Please try again.")
        return get_voice_input(prompt_text, retries)
    except sr.RequestError as e:
        if retries > 0:
            print(f"Network error in speech recognition ({e}); retrying...")
            return get_voice_input(prompt_text, retries - 1)
        else:
            print("Speech recognition failed after multiple retries.")
            return ""

def get_user_input(prompt_text: str) -> str:
    if globals().get("INPUT_MODE", "text") == "voice":
        return get_voice_input(prompt_text)
    else:
        return input(prompt_text)

def create_cafe_kiosk_agent() -> AgentExecutor:
    """
    Creates and returns the cafe kiosk agent with tools bound.
    """
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=500,
        timeout=30,
        max_retries=2,
    )
    llm_with_tools = llm.bind_tools([show_menu, recommend_item, confirm_order])
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful cafe kiosk assistant. When a customer describes their taste, "
            "analyze the input for keywords and respond with a plain text recommendation from the menu mapping, "
            "including the product ID in the format '(product ID: X)'. Do not automatically call any functions. "
            "Instead, instruct the customer to confirm their order by saying 'yes,<product_id>' if they wish to proceed. "
            "Always display the menu using show_menu when needed."
        ),
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
        tools=[show_menu, recommend_item, confirm_order],
        verbose=True
    )
    return agent_executor

def run_kiosk():
    """
    CLI mode for running the cafe kiosk agent.
    """
    global CURRENT_USER_ID, INPUT_MODE
    print("Select input mode: Enter 'T' for Text input or 'V' for Voice input.")
    mode_choice = input("Your choice (T/V): ").strip().lower()
    if mode_choice == "v":
        INPUT_MODE = "voice"
        print("Voice input selected.")
    else:
        INPUT_MODE = "text"
        print("Text input selected.")

    welcome_msg = "Welcome to Cafe Kiosk! Please provide your mobile number."
    play_agent_message(welcome_msg)
    mobile = get_user_input("Mobile number: ").strip()

    user = database.get_user_by_phone(mobile)
    if user:
        CURRENT_USER_ID = user[1]
        greet_msg = f"Welcome back, {user[2]}! What would you like today?"
        play_agent_message(greet_msg)
    else:
        play_agent_message(
            "It seems you're a new user. Please provide your details in the format: first_name,last_name,email")
        details = get_user_input("Your details (first_name,last_name,email): ").strip()
        try:
            first_name, last_name, email = [s.strip() for s in details.split(",")]
        except Exception:
            play_agent_message("Invalid format. Please restart and provide details in the correct format.")
            return
        CURRENT_USER_ID = database.get_next_user_id()
        database.add_user(CURRENT_USER_ID, first_name, last_name, email, mobile)
        play_agent_message(f"User registered successfully, welcome {first_name}!")

if __name__ == "__main__":
    run_kiosk()
