import os
import requests
# NVIDIA Audio2Face API base URL
A2F_BASE_URL = "http://localhost:8011"  # Replace with your server's URL


# ---------------------------
# Audio2Face, USD, Stream, and Player Functions
# ---------------------------
def check_api_status():
    try:
        response = requests.get(f"{A2F_BASE_URL}/status")
        response.raise_for_status()
        print("API Status:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error checking API status: {e}")