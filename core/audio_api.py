import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
BOSON_API_KEY = os.getenv("BOSON_API_KEY")
# Assuming the hackathon provides a dedicated endpoint for Higgs Audio V2
BOSON_AUDIO_ENDPOINT = os.getenv("BOSON_AUDIO_ENDPOINT")

# --- Helper Function to read audio file and convert to base64 ---
def encode_audio_to_base64(file_path: str) -> str:
    """Reads a local audio file and encodes it as a base64 string for API payload."""
    try:
        with open(file_path, "rb") as audio_file:
            # Higgs V2 documentation/examples suggest passing the reference as base64
            return base64.b64encode(audio_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: Audio reference file not found at {file_path}")
        return ""

def generate_dialogue_audio(
    dialogue_text: str, 
    speaker_a_ref_path: str, 
    speaker_b_ref_path: str
) -> bytes:
    """
    Generates multi-speaker audio by calling the Higgs Audio V2 API.
    
    The dialogue_text must be formatted with speaker tags (e.g., "Agent A: Hello. Agent B: Hi.")
    """
    
    if not BOSON_API_KEY or not BOSON_AUDIO_ENDPOINT:
        print("Audio API key or endpoint not configured.")
        return b""

    # 1. Encode the audio references for cloning
    ref_audio_a_b64 = encode_audio_to_base64(speaker_a_ref_path)
    ref_audio_b_b64 = encode_audio_to_base64(speaker_b_ref_path)
    
    if not ref_audio_a_b64 or not ref_audio_b_b64:
        return b""

    # 2. Construct the API payload
    # The search results and Higgs V2 examples show a structured input for multi-speaker.
    payload = {
        "text": dialogue_text,
        "mode": "multi_speaker_dialogue", # Specific mode for conversation
        "speakers": {
            # Map the text tags (e.g., "Agent A") to the voice reference data
            "Agent A": {"reference_audio_base64": ref_audio_a_b64},
            "Agent B": {"reference_audio_base64": ref_audio_b_b64},
        },
        "audio_config": {"output_format": "mp3", "sample_rate": 24000}
    }
    
    headers = {
        "Authorization": f"Bearer {BOSON_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # 3. Call the external Higgs Audio API
        response = requests.post(BOSON_AUDIO_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        
        # 4. Assume the API returns the audio data (e.g., base64 encoded MP3)
        audio_data_b64 = response.json().get("audio_content")
        if audio_data_b64:
            return base64.b64decode(audio_data_b64)
        
        return b"" # Return empty bytes on failure

    except requests.exceptions.RequestException as e:
        print(f"Audio API ERROR: Could not generate audio. Details: {e}")
        return b""