import pyttsx3

def alert_nurse(value, vital_type, severity="Low", patient_name="Unknown Patient"):
    """Alerts nurse about abnormal vital signs via print and TTS, includes patient name."""
    message = f"Alert! Patient {patient_name}'s {vital_type} is abnormal.  Value: {value}, Severity: {severity}." #Reformat messge
    print(message)

    # Text-to-Speech
    tts = pyttsx3.init()
    tts.say(message)
    tts.runAndWait()