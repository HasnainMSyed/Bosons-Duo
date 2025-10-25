import os
import wave
import base64
import openai
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()

CHARACATER_JAMES_DAVIS = "james_davis"
CHARACTER_TO_REFERENCE_MAP = {
    "james_davis": (
        (
            "After that I went on to graduate school at the Institute for Aerospace Studies "
            "where I completed two masters and a PhD. My research area is in materials for fusion reactors. "
            "This is an area I got interested in when I was actually an undergraduate student and I spent two summers "
            "working up at UTIAS in the research lab which I now run. And this whole time I've been looking at various "
            "aspects of how very high temperature plasmas in a fusion reactor interact with the materials that are "
            "intended to keep the plasma from escaping."
        ),
        "audio_references/davis_trimmed.wav",
    )
}

DEFAULT_VOICE_EN_MAN = "en_man"
DEFAULT_VOICE_MABEL = "mabel"

BOSON_API_KEY = os.getenv("BOSON_API_KEY")
BOSON_AUDIO_ENDPOINT = os.getenv("BOSON_AUDIO_ENDPOINT")

CLIENT = openai.Client(
    api_key=BOSON_API_KEY, base_url=BOSON_AUDIO_ENDPOINT, max_retries=2, timeout=30
)


def encode_audio_to_base64(file_path: str) -> str:
    try:
        with open(file_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Error: Audio reference file not found at {file_path}")
        return ""


def adjust_audio_speed(path: str, speed_factor: float):
    with wave.open(path, "rb") as wav:
        params = wav.getparams()
        frames = wav.readframes(params.nframes)

    with wave.open(path, "wb") as out_wav:
        out_wav.setnchannels(params.nchannels)
        out_wav.setsampwidth(params.sampwidth)
        out_wav.setframerate(int(params.framerate * speed_factor))
        out_wav.writeframes(frames)


def generate_dialogue_audio(
    dialogue_text: str,
    audio_file_path: str,
    voice: str,
    audio_speed_factor: float = 1.0,
) -> None:
    if not BOSON_API_KEY or not BOSON_AUDIO_ENDPOINT:
        print("Audio API key or endpoint not configured.")
        return b""

    response = CLIENT.audio.speech.create(
        model="higgs-audio-generation-Hackathon",
        voice=voice,
        input=dialogue_text,
        response_format="pcm",
    )

    num_channels = 1
    sample_width = 2
    sample_rate = 24000

    pcm_data = response.content

    with wave.open(audio_file_path, "wb") as wav:
        wav.setnchannels(num_channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_data)

    adjust_audio_speed(audio_file_path, audio_speed_factor)


def transcribe_audio(audio_path: str) -> str:
    audio_base64 = encode_audio_to_base64(audio_path)
    file_format = audio_path.split(".")[-1]

    response = CLIENT.chat.completions.create(
        model="higgs-audio-understanding-Hackathon",
        messages=[
            {"role": "system", "content": "Transcribe the COMPLETE audio for me."},
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
        ],
        max_completion_tokens=6000,
    )

    return response.choices[0].message.content


def clone_audio(reference_name, output_path, dialogue_text):
    system = "You are an AI assistant that converts the tone of a speech to be similar to that of a reference audio"
    resp = CLIENT.chat.completions.create(
        model="higgs-audio-generation-Hackathon",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": CHARACTER_TO_REFERENCE_MAP[reference_name][0]},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encode_audio_to_base64(
                                CHARACTER_TO_REFERENCE_MAP[reference_name][1]
                            ),
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
        top_p=0.95,
        stream=False,
        extra_body={"top_k": 50},
    )

    audio_b64 = resp.choices[0].message.audio.data
    open(output_path, "wb").write(base64.b64decode(audio_b64))


if __name__ == "__main__":
    generate_dialogue_audio(
        "Hello everyone, I am James Davis, the instructor for MAT195 Calculus. We will skipp all sections related to biology because biologists are so bad at math that they think multiplication and division are the same thing",
        "audio_references/audio_out.wav",
        DEFAULT_VOICE_MABEL,
        audio_speed_factor=1.1,
    )
    # clone_audio(
    #     CHARACATER_JAMES_DAVIS,
    #     "audio_references/test_clone.wav",
    #     "Hello everyone, I am James Davis, the instructor for MAT195 Calculus. We will skipp all sections related to biology because biologists are soooooo bad at math that they think multiplication and division are the same thing",
    # )
