import os

import speech_recognition as sr
from dotenv import load_dotenv
load_dotenv()
os.environ["hf_token"] = os.getenv("hf_token")
#import pyttsx3
#from pyAudioAnalysis import audioBasicIO, ShortTermFeatures
def get_speech_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Speak now!")
        try:
            audio = recognizer.listen(source)
            user_speech = recognizer.recognize_google(audio)
            print(f"You said: {user_speech}")
            return user_speech
        except sr.UnknownValueError:
            print("Sorry, I could not understand your speech. Please try again.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            return None


# def save_response_to_wav(response_text, file_name):
#     output_path = os.path.join(AUDIO_DIR, file_name)
#     inputs = tokenizer(response_text, return_tensors="pt")
#     with torch.no_grad():
#         audio = model(**inputs).waveform.squeeze().cpu().numpy()
#     sf.write(output_path, audio, samplerate=model.config.sampling_rate)
#     print(f"Generated audio saved to: {output_path}")
#     return output_path

#
# GRADIO_CLIENT = Client("lj1995/GPT-SoVITS-v2", hf_token="")
#
# def save_response_to_wav(response_text, file_name):
#     try:
#         output_path = os.path.join(AUDIO_DIR, file_name)
#         result = GRADIO_CLIENT.predict(
#             ref_wav_path=handle_file("C:/Users/parth/Downloads/medieval-gamer-voice-darkness-hunts-us-what-youx27ve-learned-stay-226596.mp3"),
#             prompt_text="",
#             prompt_language="English",
#             text=response_text,
#             text_language="English",
#             how_to_cut="Slice once every 4 sentences",
#             top_k=15,
#             top_p=1,
#             temperature=1,
#             ref_free=True,
#             speed=1,
#             if_freeze=False,
#             inp_refs=[],  # Empty list for optional references
#             api_name="/get_tts_wav"
#         )
#         shutil.copy(result, output_path)
#         print(f"Generated audio saved to: {output_path}")
#         return output_path
#     except Exception as e:
#         print(f"Error in TTS generation: {e}")
#         return None
