import random
import time

def get_heart_rate():
    """
    Simulates heart rate sensor data.
    """
    return random.randint(50, 130)  # Simulated heart rate range

def get_spo2():
    """
    Simulates blood oxygen saturation sensor data.
    """
    return random.randint(90, 100)  # Simulated SpO2 range

def get_temperature():
    """
    Simulates body temperature sensor data (Fahrenheit).
    """
    return random.uniform(97.0, 102.0)  # Simulated temperature range

def stream_patient_data(callback):
    """
    Continuously sends heart rate, SpO2, and temperature data to the callback function.
    """
    heart_rate = get_heart_rate()
    spo2 = get_spo2()
    temperature = get_temperature()
    callback(heart_rate, spo2, temperature)  # Pass all readings