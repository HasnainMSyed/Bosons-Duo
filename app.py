import base64
from flask_cors import CORS
from flask import Flask, request, jsonify
from core.audio_api import generate_dialogue_audio
from core.agent_manager import AgentManager

DEFAULT_VOICE_EN_MAN = "en_man"
DEFAULT_VOICE_MABEL = "mabel"

app = Flask(__name__)
CORS(app)

manager = None
initial_topic = ""
last_response = ""

@app.route("/")
def home():
    return "Hello, Flask Server is Running! 🚀"


@app.route("/api/test", methods=["POST"])
def test():
    global manager, initial_topic, last_response
    data = request.get_json()

    prompt_1 = data['agent_1']
    prompt_2 = data['agent_2']

    end = data['end']

    if end:
        manager = None
        initial_topic = ""

    if manager is None:
        manager = AgentManager(prompt_1, prompt_2)
    
    if not initial_topic:
        initial_topic = data['topic_input']

    response1 = manager.run_turn(initial_topic)
    response2 = manager.run_turn(response1)
    last_response = response2

    print("Audio response obtained")

    # turn response1 and response2 into audio files
    generate_dialogue_audio(response1, "audio_references/a.wav", DEFAULT_VOICE_MABEL, audio_speed_factor=1.1)
    generate_dialogue_audio(response2, "audio_references/b.wav", DEFAULT_VOICE_EN_MAN, audio_speed_factor=1.1)

    print("Finished generating audio files")

    with open("audio_references/a.wav", "rb") as f:
        a_data = base64.b64encode(f.read()).decode("utf-8")
    with open("audio_references/b.wav", "rb") as f:
        b_data = base64.b64encode(f.read()).decode("utf-8")

    return jsonify({
        "response1": response1,
        "response2": response2,
        "a_audio": a_data,
        "b_audio": b_data
    })

if __name__ == "__main__":
    app.run(debug=True)
