import os
import wave
import base64
import openai
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()

# --- Configuration ---
BOSON_API_KEY = os.getenv("BOSON_API_KEY") # Get API Keys
BASE_URL = "https://hackathon.boson.ai/v1"

CLIENT = openai.Client(api_key=BOSON_API_KEY, base_url=BASE_URL)


def encode_audio_to_base64(file_path: str) -> Optional[str]:
    """Reads a local audio file and encodes it as a base64 string for API payload."""
    try:
        with open(file_path, "rb") as audio_file:
            # Higgs V2 documentation/examples suggest passing the reference as base64
            return base64.b64encode(audio_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Error: Audio reference file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error encoding audio file {file_path}: {e}")
        return None


# def generate_dialogue_audio(dialogue_text: str, audio_file_path: str) -> None:
#     if not BOSON_API_KEY or not BOSON_AUDIO_ENDPOINT:
#         print("Audio API key or endpoint not configured.")
#         return b""

#     response = CLIENT.audio.speech.create(
#         model="higgs-audio-generation-Hackathon",
#         voice="belinda",
#         input=dialogue_text,
#         response_format="pcm",
#     )

#     num_channels = 1
#     sample_width = 2
#     sample_rate = 24000

#     pcm_data = response.content

#     with wave.open(audio_file_path, "wb") as wav:
#         wav.setnchannels(num_channels)
#         wav.setsampwidth(sample_width)
#         wav.setframerate(sample_rate)
#         wav.writeframes(pcm_data)

def transcribe_audio(audio_path: str) -> str:
    try:
        file_format = audio_path.split(".")[-1].lower()
        if file_format not in ['wav', 'mp3', 'ogg', 'flac']:
             raise ValueError(f"Unsupported audio format: {file_format}")
        
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
            audio_base64 = encode_audio_to_base64(audio_path)
    
        messages_payload: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "Transcribe this audio file accurately."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_base64,
                            "format": file_format,
                        },
                    },
                ],
            },
        ]
                
        response = CLIENT.chat.completions.create(
                model="higgs-audio-understanding-Hackathon",
                messages=messages_payload,
                max_completion_tokens=6000,
                temperature=0.5
            )

        print(response.choices[0].message.content)

        return response.choices[0].message.content

    except openai.APIError as e:
        print(f"OpenAI API Error during transcription: {e}")
        return f"[Transcription API Error: {e}]"
    except FileNotFoundError:
        print(f"Error: Audio file not found at {audio_path}")
        return "[Transcription Error: File not found]"
    except Exception as e:
        print(f"An unexpected error occurred during transcription: {e}")
        return f"[Transcription Unexpected Error: {e}]"


def clone_audio(reference_path, reference_transcript, output_path, dialogue_text):
    system = "You are an AI assistant that converts the tone of a speech to be similar to that of a reference audio"
    resp = CLIENT.chat.completions.create(
        model="higgs-audio-generation-Hackathon",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": reference_transcript},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encode_audio_to_base64(reference_path),
                            "format": "wav",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": f"[charismatic] {dialogue_text}",
            },
        ],
        modalities=["text", "audio"],
    )

    audio_b64 = resp.choices[0].message.audio.data
    open(output_path, "wb").write(base64.b64decode(audio_b64))


if __name__ == "__main__":
    # generate_dialogue_audio(
    #     "Consider the vector field x. Verify the Stoke's theorem about the surface S, where S is the top half of this cylinder.",
    #     "audio_references/test.wav",
    # )
    reference_text = transcribe_audio("audio_references/davis_trimmed_quarter.wav")
    clone_audio(
        "audio_references/davis_trimmed_quarter.wav",
        # "it divides but works during the day at well, if you took steps to block direct sunlight or point it away from the sun",
        reference_text,
        "audio_references/test_clone.wav",
        # "The average on the question is a six out of ten. If you get a bunch of monkeys to do this, they will get five out of ten. So, so you guys are only slightly better than monkeys",
        "大家好 我是James Davis我我我我哦我哈哈哈哈一二三四五六七一加一等于二"
    )
