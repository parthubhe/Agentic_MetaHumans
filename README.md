# Agentic_MetaHumans Framework

 


## Overview

This project provides a framework for creating interactive 3D agentic AI avatars using Unreal Engine's MetaHumans. It integrates real-time lip-sync animation via Nvidia Audio2Face, dynamic emotional expression driven by a custom text-based emotion classifier, and conversational capabilities powered by LangChain agents.

The goal is to create more immersive and engaging human-AI interactions compared to traditional text-based chatbots by giving the AI a visual, expressive persona. The framework currently showcases three distinct agents: a Cafe Receptionist, a Personal Assistant, and a Nurse Assistant, demonstrating potential applications across various domains.


[![Watch Demo Video](https://img.shields.io/badge/Watch-Demo%20Video-red)](https://youtu.be/L3iMVHcjaXM)



## Features

*   **3D Avatar Integration:** Designed for use with Unreal Engine MetaHumans (requires separate UE setup).
*   **Real-time Lip-Sync:** Utilizes Nvidia Audio2Face REST API for generating lip-sync animations from synthesized speech.
*   **Dynamic Emotional Expression:** Features a custom-trained RoBERTa-based emotion classifier (using RoBERTa) that analyzes agent responses and drives MetaHuman facial expressions via Audio2Face.
*   **Agentic AI Framework:** Leverages LangChain to create modular agents with specific tools and capabilities.
*   **Multiple Agent Examples:**
    *   **Cafe Receptionist:** Manages cafe interactions, takes orders, provides menu info, interacts with a database.
    *   **Personal Assistant:** Handles tasks like weather updates, news fetching, music playback (via VLC), sending emails, and basic chat. Includes user facial emotion recognition (via FER) to potentially adapt responses (though adaptation logic might need further implementation).
    *   **Nurse Assistant:** Simulates a healthcare assistant role, providing sensor data, patient info, managing medication stock (via file persistence), triggering alerts, and displaying dashboards (via Matplotlib).
*   **Flask Backend:** Central web server managing agent interactions, audio processing, and communication with Audio2Face.
*   **Web Frontend:** Simple HTML/CSS/JS interfaces for interacting with each agent.
*   **Text-to-Speech (TTS):** Uses gTTS for generating agent voice responses.[We had implemented GPT-SOVITS,F5TTS, etc from Huggingface Spaces but due to latency issues(>40s per response), we chose gTTS. using these open-source pre-trained models was not a viable option since there was a lack of VRAM to run all thing together.]
*   **Audio Processing Pipeline:** Segments text, generates TTS, speeds up audio (PyDub), converts to WAV, and manages timed playback synchronized with A2F animation.
*   **Voice Input:** Supports user interaction via microphone using SpeechRecognition.
*   **Tool Integration:** Demonstrates LangChain agent tool usage for various functionalities (API calls, DB access, file I/O, media control).

## Technology Stack

*   **Backend:** Python, Flask
*   **AI/LLM:** LangChain, LangChain-Groq (Llama 3.3 70B via Groq API)
*   **Emotion Classification:** PyTorch, Transformers (RoBERTa), Scikit-learn (for metrics)
*   **3D Animation/Lip-Sync:** Nvidia Audio2Face (Requires separate installation and running instance)
*   **3D Avatars:** Unreal Engine MetaHumans (Requires separate setup)
*   **Audio:** gTTS (TTS), PyDub (Audio manipulation), Mutagen (MP3 duration), SpeechRecognition (STT), python-vlc (Music playback)
*   **Database (Cafe Agent):** SQLite
*   **Utilities:** Requests, python-dotenv, yt-dlp (Music download), Gradio-Client (A2F Utils)
*   **Frontend:** HTML, CSS, JavaScript, Bootstrap (via CDN or local assets)

## Architecture/Workflow (Conceptual)


![WhatsApp Image 2025-03-28 at 02 00 31_cfa5095d](https://github.com/user-attachments/assets/6ae49463-2ee1-44f0-a565-1966f57812e8)

 


## Setup and Installation

**1. Prerequisites:**

*   **Python:** 3.9+ recommended.
*   **pip:** Python package installer.
*   **Git:** For cloning the repository.
*   **Nvidia Audio2Face:** Install and run the Audio2Face application. Ensure it's accessible via its REST API (default: `http://localhost:8011`).
*   **Unreal Engine & MetaHuman:** A configured Unreal Engine project with a MetaHuman character set up and connected to Audio2Face via LiveLink. The specific USD path in `a2f_utils.py` (`mark_solved_arkit.usd`) might need adjustment based on your setup.
*   **VLC Media Player:** Required for the Personal Assistant's music playback feature. Make sure it's installed and the path in `personal_assistant.py` (`C:\Program Files\VideoLAN\VLC`) matches your installation, or update the script/add VLC to your system's PATH.
*   **FFmpeg:** Required by `pydub` for audio processing and `yt-dlp` for audio conversion. Install it and ensure it's in your system's PATH.
*   **(Optional) CUDA:** For GPU acceleration with PyTorch/Transformers (if your hardware supports it).

**2. Clone Repository:**
   ```bash```
   ```git clone https://github.com/your-username/your-repo-name.git```
   ```cd your-repo-name```

 
**3. Create Virtual Environment (Recommended):**
```python -m venv venv```
# On Windows
```venv\Scripts\activate```
# On macOS/Linux
```source venv/bin/activate```


**4. Install Dependencies:**
```pip install -r requirements.txt```

Note: Download ffmpeg and add it to your enviorment variables.

 
**5. Environment Variables:**
Groq API Key: The Groq API key is currently hardcoded in db_main.py and personal_assistant.py. It's highly recommended to move this to an environment variable. Create a .env file in the root directory:
 .env
```GROQ_API_KEY=gsk_YourGroqApiKeyHere```

Note: Also add root paths for the AUDIO_DIR,RoBERTa,model.bin,usd file in the .env to avoid hardcoding all the paths.

 
 pass.env
EMAIL_USER=your_gmail_address@gmail.com
EMAIL_PASS=your_gmail_app_password
Note: Use an App Password if using Gmail with 2FA enabled.


**6. Download Frontend Assets:**
```python download_assets.py```

This script downloads necessary CSS/JS libraries specified in assets from Bootstrap.

**7. Emotion Classifier Model:**
The pre-trained emotion classification model (model.bin) and the RoBERTa tokenizer files are expected to be in specific local paths (e.g., D:\Metahuman Chatbot\...) as per emoClassier.py.
You need to either:
Download/obtain the model.bin file and place it in the expected path, the model.bin and the Jupyter Notebook can be found in the MultiLabelClassifier folder, OR
Modify the paths in emoClassier.py to point to where you store the model and tokenizer files, OR
Retrain the classifier(.ipynb file) on the desired amount of epochs and get the model.bin.
 
The RoBERTa tokenizer/model files can be downloaded automatically by Transformers if the local path doesn't exist and you change AutoModel.from_pretrained(r"D:\...") to AutoModel.from_pretrained("roberta-base") (requires internet connection on first run).

  
**8. Database Initialization:**
The SQLite database (DB/database.db) is created automatically when you run db_main.py for the first time due to the database.initialize_database() call. The DB directory will also be created if it doesn't exist.

 
## Audio2Face & Unreal Engine Setup:

*   Start the Nvidia Audio2Face application (e.g., run the `audio2face_headless.bat` file in your Omniverse installation directory).
*   Start your Unreal Engine project with the MetaHuman character loaded.
*   Ensure that the **LiveLink** and **PixelStreaming** plugins are enabled for the UE project.
*   Set up a **LiveLink** connection between the MetaHuman Blueprint (e.g., `BP_Payton`) and Audio2Face within the Unreal Engine Editor.
*   Ensure **LiveLink is active in Audio2Face** and shows a connection to your Unreal Engine MetaHuman.
*   Verify the **USD path** in `a2f_utils.py` (`load_usd_file` function) points to the correct MetaHuman USD file within your A2F setup (e.g., `mark_solved_arkit.usd`).
*   Verify the **Audio2Face Base URL** in `a2f_utils.py` (`A2F_BASE_URL`) matches your A2F instance (usually `http://localhost:8011`).

## Running the Application

*   Ensure **Audio2Face** and **Unreal Engine** (with the MetaHuman scene and LiveLink connection active) are running.
*   Activate your Python virtual environment (if you created one).
*   Start the **Pixel Streaming server** from your Unreal Engine project's packaged build or run configuration. Press **"Stream Full Level Editor"** (or similar, depending on your setup) to enable the UE screen to be captured by the `<iframe>` tag on the web page.
*   Start the **Flask backend server** from the project root directory:
    ```bash
    python db_main.py
    ```
*   Open your web browser and navigate to `http://localhost:5000`.
*   Click **"Get Started"** to see the agent selection page (`http://localhost:5000/agents`).
*   Select an agent (e.g., Cafe Receptionist, Personal Assistant, Nurse Assistant) to start interacting.

The Flask console will show agent activity, tool usage (if `verbose=True`), and potentially errors. The `responses_output` directory will temporarily store generated audio segments before they are deleted.

## Agent Details

*   **Cafe Receptionist (`cafe_receptionist.py`, `/ar`):**
    *   Simulates a cafe kiosk assistant.
    *   Handles user identification (via mobile number, stores in SQLite DB).
    *   Provides the menu (`show_menu` tool).
    *   Recommends items based on preferences (`recommend_item` tool).
    *   Confirms orders and provides a (placeholder) payment link (`confirm_order` tool).
    *   Uses `CRA_Utils/database.py` for data persistence.
*   **Personal Assistant (`personal_assistant.py`, `/pa`):**
    *   Acts as a general-purpose assistant.
    *   Tools: Weather, News (via local service assumed at `http://localhost:5000/news` - **ensure this service is running if needed**), Email sending (SMTP), Music playback/control (VLC, yt-dlp for downloads).
    *   Features continuous user facial emotion detection using `fer` and webcam (runs in a separate thread). The detected emotion (`current_emotion`) is available but might need further integration into the agent's response logic.
    *   Uses `.env` and `pass.env` for credentials. Logs errors to `PA_Utils/error_log.txt`.
*   **Nurse Assistant (`nurse_agent.py`, `/agenticNurse`):**
    *   Simulates a healthcare assistant.
    *   Tools: Reads simulated sensor data (heart rate, SpO2, temp), fetches patient info (from `patients.txt`), triggers nurse alerts (TTS via `pyttsx3`), manages medication stock (add/reduce in `medication_stock.txt`), displays dashboards (Matplotlib popups).
    *   Uses utilities from the `NA_Utils` directory.

## Emotion Classifier (`emoClassier.py`)

*   Uses a pre-trained RoBERTa model fine-tuned for multi-label emotion classification.
*   We have provided a .ipynb notebook (`MCC_NLTK.ipynb`),which contains the code to train the emotion classifier model which is trained on the GoEmotions dataset,  mapped to Ekman's basic emotions (Anger, Fear, Joy, Sadness, Surprise). The final model uses 5 output classes[which are later mapped to the 10 setEmotion nodes in Audio2Face.
*   You can always modify this classification model to your liking and more epochs for a better accuracy.
*   The `predict_emotion` function takes text and returns probabilities for the 5 classes (Anger, Fear, Joy, Sadness, Surprise).
*   `generate_emotion_payload_from_probabilities` maps these probabilities to an Audio2Face-compatible emotion dictionary to drive facial expressions.

## Audio2Face Integration (`a2f_utils.py`, `audio_processing_utils.py`)

*   `a2f_utils.py` sends commands to the A2F REST API to load the character, manage LiveLink, and play audio tracks for lip-sync. It also handles MP3-to-WAV conversion using `pydub`. **Crucially, it sets the A2F player's root path to the project's `responses_output` directory.**
*   `audio_processing_utils.py` orchestrates the text-to-animation pipeline:
    1.  Splits the agent's response into sentences/segments.
    2.  **(Parallel Phase)** For each segment: generates TTS audio (gTTS), speeds it up slightly, converts to WAV.
    3.  **(Sequential Phase)** For each segment (in order):
        *   Predicts emotion using `emoClassier.py`.
        *   Generates and sends the emotion payload to A2F.
        *   Sends the WAV audio path to A2F for lip-sync playback.
        *   Calculates audio duration (Mutagen/PyDub) and waits for playback to finish.
        *   Deletes the temporary audio file.

## Configuration

*   **API Keys:** See `Environment Variables` section above. Move hardcoded keys to `.env`.
*   **Audio2Face URL:** `A2F_BASE_URL` in `a2f_utils.py` (default `http://localhost:8011`).
*   **File Paths:** Check paths for VLC, model files (`emoClassier.py`), USD files (`a2f_utils.py`), and data files (`NA_Utils`, `CRA_Utils`, `PA_Utils`). Relative paths are generally better, but absolute paths might be needed for external tools like VLC or A2F if not in the system PATH.
*   **Audio Output:** `AUDIO_DIR` defined in several files, consistently points to `./responses_output`.

## Troubleshooting

*   **Audio2Face Connection Errors:** Ensure the A2F application is running and accessible at the configured `A2F_BASE_URL`. Check firewall settings.
*   **LiveLink Issues:** Verify the LiveLink plugin is enabled in UE, the connection is active in both UE and A2F, and the correct MetaHuman Blueprint/Subject Name is targeted.
*   **Pixel Streaming Issues:** Ensure the Pixel Streaming plugin is enabled, the server is running, and the frontend `<iframe>` points to the correct server address (likely `http://127.0.0.1` or `http://localhost` by default). Check firewall ports if connecting remotely.
*   **VLC Errors (PA):** Verify VLC is installed correctly and the path in `personal_assistant.py` is accurate or VLC is in the system PATH.
*   **FFmpeg Errors:** Ensure FFmpeg is installed and in the system PATH. `pydub` and `yt-dlp` rely on it.
*   **Model Not Found:** Ensure `model.bin` and RoBERTa tokenizer files are correctly placed or paths in `emoClassier.py` are updated.
*   **Dependency Issues:** Double-check installation from `requirements.txt` in the correct virtual environment. `fer` can be tricky.

 

## Acknowledgements

*   Nvidia Audio2Face
*   Unreal Engine MetaHumans
*   LangChain
*   Hugging Face Transformers
*   PyTorch
*   Flask
*   Groq
*   Libraries listed in `requirements.txt`.
 
