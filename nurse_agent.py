import os

from langchain.agents import tool, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages

from Utils.a2f_utils import send_audio_to_audio2face
from Utils.emoClassier import predict_emotion, generate_emotion_payload_from_probabilities

from NA_Utils import nurse_alert, sensor_listener, med_stock_dashboard, dashboard_display, med_stock_handler, \
    patient_data

# Import universal audio processing helper
from Utils.audio_processing_utils import process_response_text_generic

# Directory to store audio responses (same as other agents)
AUDIO_DIR = r"./responses_output"
os.makedirs(AUDIO_DIR, exist_ok=True)
A2F_BASE_URL = "http://localhost:8011"


# ------------------ Nurse Agent Tools ------------------

@tool
def sensor_data_tool(input: str = "") -> str:
    """
    Retrieves simulated sensor data: heart rate, SpO2, and temperature.
    """
    heart_rate = sensor_listener.get_heart_rate()
    spo2 = sensor_listener.get_spo2()
    temperature = sensor_listener.get_temperature()
    return f"Heart Rate: {heart_rate} BPM, SpO2: {spo2}%, Temperature: {temperature:.2f}°F"


@tool
def patient_info_tool(input: str = "") -> str:
    """
    Loads and returns patient information from the patient database.
    """
    patients = patient_data.load_patients()
    if not patients:
        return "No patient data available."
    response = "Patient Information:\n"
    for name, info in patients.items():
        response += f"{name}: Allergies: {', '.join(info['allergies']) if info['allergies'] else 'None'}, "
        response += f"Medications: {', '.join(info['medications']) if info['medications'] else 'None'}\n"
    return response


@tool
def nurse_alert_tool(input: str) -> str:
    """
    Triggers a nurse alert.
    Expects input in the format "vital_type,value,patient_name".
    """
    try:
        vital_type, value_str, patient_name = [s.strip() for s in input.split(",")]
        value = float(value_str)
    except Exception as e:
        return f"Invalid input format for nurse alert: {e}"
    # Only trigger alert if the query explicitly requests it.
    # (The agent chain should decide when to call this tool.)
    severity = "High" if value < 50 or value > 120 else "Low"
    nurse_alert.alert_nurse(value, vital_type, severity, patient_name)
    return f"Nurse alerted for {patient_name}'s {vital_type}."


@tool
def dashboard_tool(input: str = "") -> str:
    """
    Displays the nurse dashboard with patient vitals.
    """
    sample_patients = {
        "John Doe": {"heart_rate": [70, 72, 75], "spo2": [98, 97, 98], "temperature": [98.6, 98.7, 98.5]}
    }
    dashboard_display.display_dashboard(sample_patients)
    return "Patient dashboard displayed."


@tool
def med_stock_dashboard_tool(input: str = "") -> str:
    """
    Loads medication stock using med_stock_handler and displays a stock dashboard using med_stock_dashboard.
    """
    stock = med_stock_handler.load_medication_stock()
    if not stock:
        return "No medication stock data available."
    med_stock_dashboard.display_medication_stock_dashboard(stock)
    return "Medication stock dashboard displayed."


@tool
def update_medication_stock_tool(input: str) -> str:
    """
    Updates medication stock based on input.
    Expects input in the format: "action,name,quantity"
    where action is 'add' or 'reduce'.
    """
    try:
        action, name, quantity_str = [s.strip() for s in input.split(",")]
        quantity = int(quantity_str)
    except Exception as e:
        return f"Invalid input format for updating medication stock: {e}"

    stock = med_stock_handler.load_medication_stock()
    if action.lower() == "add":
        stock = med_stock_handler.add_medication_stock(stock, name, quantity)
        return f"Added {quantity} units to {name}. Current stock: {stock.get(name, 'N/A')}."
    elif action.lower() == "reduce":
        stock, error = med_stock_handler.reduce_medication_stock(stock, name, quantity)
        if error:
            return error
        else:
            return f"Reduced {quantity} units from {name}. Current stock: {stock.get(name, 'N/A')}."
    else:
        return "Action must be 'add' or 'reduce'."


# ------------------ Creating the Nurse Agent ------------------

def create_nurse_agent() -> AgentExecutor:
    """
    Creates and returns the nurse agent with bound tools.
    """
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=500,
        timeout=30,
        max_retries=2,
    )
    # Bind all necessary tools including medication stock management.
    llm_with_tools = llm.bind_tools([
        sensor_data_tool,
        patient_info_tool,
        nurse_alert_tool,
        dashboard_tool,
        med_stock_dashboard_tool,
        update_medication_stock_tool
    ])
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful nurse assistant. You can provide sensor data, patient information, manage medication stock, "
         "and display dashboards. Only invoke the nurse alert tool when an explicit patient alert is required. "
         "Segment your responses for audio processing."),
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
            sensor_data_tool,
            patient_info_tool,
            nurse_alert_tool,
            dashboard_tool,
            med_stock_dashboard_tool,
            update_medication_stock_tool
        ],
        verbose=True
    )
    return agent_executor


def process_response_text_nurse(response_text: str, default_delay: float = 1.0):
    process_response_text_generic(
        response_text=response_text,
        prefix="nurse_response_segment",
        a2f_base_url=A2F_BASE_URL,
        audio_dir=AUDIO_DIR,
        send_audio_func=send_audio_to_audio2face,
        predict_emotion_func=predict_emotion,
        generate_payload_func=generate_emotion_payload_from_probabilities,
        default_delay=default_delay
    )


if __name__ == "__main__":
    # Example usage (for testing purposes)
    sample_response = ("I can provide you with various tools to assist with patient care. "
                       "1. Sensor Data: I can retrieve simulated sensor data, including heart rate, SpO2, and temperature, using the sensor_data_tool function. "
                       "2. Patient Information: I can load and return patient information from the patient database using the patient_info_tool function. "
                       "3. Nurse Alert: I can trigger a nurse alert by using the nurse_alert_tool function, which expects input in the format 'vital_type,value,patient_name'. "
                       "4. Nurse Dashboard: I can display the nurse dashboard with patient vitals using the dashboard_tool function. "
                       "5. Medication Stock Dashboard: I can display medication stock levels. "
                       "6. Update Medication Stock: I can update medication stock. "
                       "Please let me know how I can assist you further.")
    process_response_text_nurse(sample_response)
