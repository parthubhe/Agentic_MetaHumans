import os
import time
import shutil  # added to remove directories if necessary
from gtts import gTTS
from pydub import AudioSegment
import requests
import json


def generate_audio_for_text(text: str, prefix: str, audio_dir: str, default_delay: float = 1.0) -> str:
    """
    Generates TTS audio (MP3) for the full text, speeds it up,
    converts it to WAV, and returns the WAV file path.
    """
    try:
        tts = gTTS(text, lang='en')
        mp3_filename = os.path.join(audio_dir, f"{prefix}.mp3")
        tts.save(mp3_filename)
        print(f"[{prefix}] Audio generated for the full text and saved as {mp3_filename}.")
    except Exception as e:
        print(f"[{prefix}] Error generating TTS audio: {e}")
        raise e

    try:
        sound = AudioSegment.from_file(mp3_filename, format="mp3")
        faster_sound = sound.speedup(playback_speed=1.25)
        # Overwrite the MP3 with the sped up version
        faster_sound.export(mp3_filename, format="mp3")
        print(f"[{prefix}] Audio sped up by 1.25x.")
    except Exception as e:
        print(f"[{prefix}] Error speeding up audio: {e}")

    try:
        wav_filename = os.path.join(audio_dir, f"{prefix}_fast.wav")
        sound = AudioSegment.from_file(mp3_filename, format="mp3")
        sound.export(wav_filename, format="wav")
        print(f"[{prefix}] Converted {mp3_filename} to {wav_filename}.")
    except Exception as e:
        print(f"[{prefix}] Error converting audio to WAV: {e}")
        raise e

    return wav_filename


def process_response_text_generic(response_text: str, prefix: str, a2f_base_url: str, audio_dir: str,
                                  send_audio_func, predict_emotion_func, generate_payload_func,
                                  default_delay: float = 1.0):
    """
    Processes the entire response text as one block.
    Steps:
      1. Generate TTS audio for the full text, speed it up, and convert it to WAV.
      2. Perform emotion classification on the entire response text.
      3. Generate and send the emotion payload.
      4. Send the entire audio via send_audio_func.
      5. Wait for the duration of the audio.
      6. Clear all files in the responses_output folder.
    """
    # Generate audio for the full response text
    try:
        wav_filename = generate_audio_for_text(response_text, prefix, audio_dir, default_delay)
    except Exception as e:
        print(f"[{prefix}] Error generating audio for full text: {e}")
        return

    # Emotion classification on the entire response text
    try:
        prob, emotion_label = predict_emotion_func(response_text)
        payload = generate_payload_func(prob)
        emotion_url = f"{a2f_base_url}/A2F/A2E/SetEmotionByName"
        print(f"[{prefix}] Sending emotion payload to {emotion_url}: {json.dumps(payload, indent=2)}")
        response_api = requests.post(emotion_url, json=payload, timeout=5)
        response_api.raise_for_status()
        print(f"[{prefix}] Emotion set for the full text.")
    except Exception as e:
        print(f"[{prefix}] Error in emotion classification or payload sending: {e}")

    # Send the entire audio
    try:
        send_audio_func(wav_filename, 1)
        print(f"[{prefix}] Audio sent successfully for the full text.")
    except Exception as e:
        print(f"[{prefix}] Error sending audio: {e}")

    # Wait for the duration of the audio to finish playback
    try:
        wav_audio = AudioSegment.from_wav(wav_filename)
        duration = len(wav_audio) / 1000.0
        print(f"[{prefix}] Waiting for {duration:.2f} seconds for audio playback.")
    except Exception as e:
        print(f"[{prefix}] Could not determine duration for audio: {e}")
        duration = default_delay

    time.sleep(duration)

    # Clear all files in the responses_output folder after processing the response
    responses_output_dir = "responses_output"
    if os.path.exists(responses_output_dir):
        for filename in os.listdir(responses_output_dir):
            file_path = os.path.join(responses_output_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Deleted directory and its contents: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")


def get_speech_input(prompt_text: str = "You: ", retries: int = 3) -> str:
    """
    Captures speech input using the microphone and returns the transcribed text.
    Added retry mechanism for network errors.
    """
    import speech_recognition as sr
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
        return get_speech_input(prompt_text, retries)
    except sr.RequestError as e:
        if retries > 0:
            print(f"Network error in speech recognition ({e}); retrying...")
            return get_speech_input(prompt_text, retries - 1)
        else:
            print("Speech recognition failed after multiple retries.")
            return ""


def get_user_input(prompt_text: str) -> str:
    if globals().get("INPUT_MODE", "text") == "voice":
        return get_speech_input(prompt_text)
    else:
        return input(prompt_text)
