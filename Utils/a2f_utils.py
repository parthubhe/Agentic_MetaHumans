
import os
import requests
import shutil
from gradio_client import Client, handle_file
from pydub import AudioSegment
import json # Added for pretty printing JSON if needed


os.environ["GROQ_API_KEY"] = "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"

AUDIO_DIR = os.path.abspath("./responses_output").replace("\\", "/")
os.makedirs(AUDIO_DIR, exist_ok=True)


# NVIDIA Audio2Face API base URL
A2F_BASE_URL = "http://localhost:8011"


def load_usd_file():
    # Using the path from the original code - CONVERT TO FORWARD SLASHES
    usd_path = r"C:\Piyush_Professor\MHAgent\v1.3\FF_Recieptionist_Backend\mark_solved_arkit.usd".replace("\\", "/")
    payload = {"file_name": usd_path}
    url = f"{A2F_BASE_URL}/A2F/USD/Load"
    print(f"[A2F_UTILS] Sending payload to {url}: {json.dumps(payload, indent=2)}")
    try:
        response = requests.post(url, json=payload, timeout=10) # Added timeout
        response.raise_for_status()
        result = response.json()
        print("USD file loaded successfully:", result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error loading USD file '{usd_path}': {e}")
        return {"status": "Error", "message": str(e)}

def activate_stream_livelink():
    payload = {"node_path": "/World/audio2face/StreamLivelink", "value": True}
    url = f"{A2F_BASE_URL}/A2F/Exporter/ActivateStreamLivelink"
    print(f"[A2F_UTILS] Sending payload to {url}: {json.dumps(payload, indent=2)}")
    try:
        response = requests.post(url, json=payload, timeout=5) # Added timeout
        response.raise_for_status()
        result = response.json()
        print("Stream LiveLink activated successfully:", result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error activating Stream LiveLink: {e}")
        return {"status": "Error", "message": str(e)}

def set_stream_livelink_settings():
    payload = {
        "node_path": "/World/audio2face/StreamLivelink",
        "values": {"enable_audio_stream": True},
    }
    url = f"{A2F_BASE_URL}/A2F/Exporter/SetStreamLivelinkSettings"
    print(f"[A2F_UTILS] Sending payload to {url}: {json.dumps(payload, indent=2)}")
    try:
        response = requests.post(url, json=payload, timeout=5) # Added timeout
        response.raise_for_status()
        result = response.json()
        print("Audio stream enabled successfully:", result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error enabling audio stream: {e}")
        return {"status": "Error", "message": str(e)}

def set_audio_looping():
    payload = {"a2f_player": "/World/audio2face/Player", "loop_audio": False}
    url = f"{A2F_BASE_URL}/A2F/Player/SetLooping"
    print(f"[A2F_UTILS] Sending payload to {url}: {json.dumps(payload, indent=2)}")
    try:
        response = requests.post(url, json=payload, timeout=5) # Added timeout
        response.raise_for_status()
        result = response.json()
        print("Looping set to false:", result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error setting looping to false: {e}")
        return {"status": "Error", "message": str(e)}

def set_audio2face_root_path():
    """
    Sets the Audio2Face root path to the custom AUDIO_DIR.
    Uses the global AUDIO_DIR variable defined in this module (or overwritten by db_main).
    Ensures the path uses forward slashes.
    """
    global AUDIO_DIR # Ensure we're using the potentially updated global AUDIO_DIR
    # Ensure AUDIO_DIR uses forward slashes for the payload
    root_dir_payload_path = AUDIO_DIR.replace("\\", "/")

    set_root_path_payload = {
        "a2f_player": "/World/audio2face/Player",
        "dir_path": root_dir_payload_path,
    }
    url = f"{A2F_BASE_URL}/A2F/Player/SetRootPath"
    print(f"[A2F_UTILS] Sending payload to {url}: {json.dumps(set_root_path_payload, indent=2)}")
    try:
        response_root = requests.post(url, json=set_root_path_payload, timeout=5) # Added timeout
        response_root.raise_for_status()
        print("Audio2Face root path set successfully:", response_root.json())
        return response_root.json()
    except requests.exceptions.RequestException as e:
        print(f"Error while setting Audio2Face root path to '{root_dir_payload_path}': {e}")
        return {"status": "Error", "message": str(e)}

def convert_mp3_to_wav(mp3_file_path):
    """
    Converts an MP3 file to WAV format in the AUDIO_DIR and returns the absolute WAV file path.
    """
    global AUDIO_DIR # Use the global AUDIO_DIR
    try:
        # Create a WAV filename based on the MP3 name, ensure it's in AUDIO_DIR
        base_name = os.path.basename(mp3_file_path).rsplit(".", 1)[0]
        # Ensure .wav extension is added if missing
        if not base_name.lower().endswith('.wav'):
             wav_filename = f"{base_name}.wav"
        else:
             wav_filename = base_name # Already has .wav

        wav_file_path = os.path.join(AUDIO_DIR, wav_filename).replace("\\", "/")

        # Ensure the input MP3 path exists
        if not os.path.exists(mp3_file_path):
             raise FileNotFoundError(f"Input MP3 not found: {mp3_file_path}")

        print(f"Converting '{mp3_file_path}' to '{wav_file_path}'...")
        sound = AudioSegment.from_mp3(mp3_file_path)
        sound.export(wav_file_path, format="wav")
        print(f"Converted {os.path.basename(mp3_file_path)} to {os.path.basename(wav_file_path)}")

        # Verify the WAV file was created
        if not os.path.exists(wav_file_path):
             raise FileNotFoundError(f"Output WAV file not created: {wav_file_path}")

        return wav_file_path
    except FileNotFoundError as fnf:
        print(f"Error converting MP3 to WAV: {fnf}")
        return None
    except Exception as e:
        print(f"Error converting MP3 to WAV ('{mp3_file_path}'): {e}")
        # import traceback
        # traceback.print_exc() # Uncomment for detailed debug
        return None

def send_audio_to_audio2face(file_path_input, response_counter):
    """
    Sends an audio file (MP3 or WAV) to Audio2Face Player/SetTrack using its ABSOLUTE PATH.
    Converts MP3 to WAV if necessary.
    """
    global AUDIO_DIR # Use the global AUDIO_DIR
    try:
        # --- Determine the absolute path of the audio file to send ---
        # Check if the input path is already absolute
        if os.path.isabs(file_path_input):
            current_file_path = file_path_input
        else:
            # If relative, assume it's relative to AUDIO_DIR
            current_file_path = os.path.join(AUDIO_DIR, os.path.basename(file_path_input))

        # Normalize the path (clean up separators, etc.) and ensure forward slashes
        current_file_path = os.path.normpath(current_file_path).replace("\\", "/")

        # --- Ensure the file is WAV ---
        if current_file_path.lower().endswith(".mp3"):
            print(f"Input is MP3 ('{os.path.basename(current_file_path)}'), converting to WAV...")
            wav_file_to_send = convert_mp3_to_wav(current_file_path)
            if wav_file_to_send is None:
                raise Exception(f"MP3 to WAV conversion failed for: {current_file_path}")
        elif current_file_path.lower().endswith(".wav"):
            wav_file_to_send = current_file_path
        else:
            raise ValueError(f"Unsupported audio format: {current_file_path}. Only WAV or MP3 supported.")

        # --- Verify file exists before sending ---
        if not os.path.exists(wav_file_to_send):
            raise FileNotFoundError(f"Audio file not found at path: {wav_file_to_send}")

        # --- Prepare and send SetTrack payload ---
        # Use the ABSOLUTE path with forward slashes for the payload
        set_track_payload = {
            "a2f_player": "/World/audio2face/Player",
            "file_name": wav_file_to_send,  # <-- CHANGED: Use absolute path
            "time_range": [0, -1],
        }
        track_url = f"{A2F_BASE_URL}/A2F/Player/SetTrack"
        print(f"[A2F_UTILS] Sending payload to {track_url}: {json.dumps(set_track_payload, indent=2)}")
        response_track = requests.post(track_url, json=set_track_payload, timeout=10) # Increased timeout
        response_track.raise_for_status()
        print(f"SetTrack successful for: {os.path.basename(wav_file_to_send)}")

        # --- Prepare and send Play payload ---
        play_payload = {"a2f_player": "/World/audio2face/Player"}
        play_url = f"{A2F_BASE_URL}/A2F/Player/Play"
        print(f"[A2F_UTILS] Sending payload to {play_url}: {json.dumps(play_payload, indent=2)}")
        response_play = requests.post(play_url, json=play_payload, timeout=5)
        response_play.raise_for_status()
        print(f"Play command sent successfully for: {os.path.basename(wav_file_to_send)}")

        return {"status": "OK", "message": "Audio played successfully"}

    except FileNotFoundError as fnf_error:
        print(f"ERROR in send_audio_to_audio2face: {fnf_error}")
        return {"status": "Error", "message": str(fnf_error)}
    except ValueError as val_error:
        print(f"ERROR in send_audio_to_audio2face: {val_error}")
        return {"status": "Error", "message": str(val_error)}
    except requests.exceptions.RequestException as req_error:
         print(f"ERROR connecting to Audio2Face API ({req_error.request.url}): {req_error}")
         print("*** Please ensure Audio2Face application is running and accessible. ***")
         return {"status": "Error", "message": f"A2F Connection Error: {req_error}"}
    except Exception as e:
        print(f"UNEXPECTED ERROR in send_audio_to_audio2face: {e}")
        # import traceback
        # traceback.print_exc() # Uncomment for detailed debug
        return {"status": "Error", "message": str(e)}


def stop_audio2face_animation():
    # (Keep the print statements added previously)
    try:
        reset_time_payload = {
            "a2f_player": "/World/audio2face/Player",
            "time": 0
        }
        reset_url = f"{A2F_BASE_URL}/A2F/Player/SetTime"
        print(f"[A2F_UTILS] Sending payload to {reset_url}: {json.dumps(reset_time_payload, indent=2)}")
        reset_time_response = requests.post(reset_url, json=reset_time_payload, timeout=5)
        reset_time_response.raise_for_status()
        print("Animation time reset to 0:", reset_time_response.json())

        pause_payload = {"a2f_player": "/World/audio2face/Player"}
        pause_url = f"{A2F_BASE_URL}/A2F/Player/Pause"
        print(f"[A2F_UTILS] Sending payload to {pause_url}: {json.dumps(pause_payload, indent=2)}")
        pause_response = requests.post(pause_url, json=pause_payload, timeout=5)
        pause_response.raise_for_status()
        print("Animation paused successfully:", pause_response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error while stopping Audio2Face animation: {e}")