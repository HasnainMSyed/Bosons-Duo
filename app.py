import base64
import os
import io
from flask_cors import CORS
from flask import Flask, request, jsonify
from core.audio_api import generate_dialogue_audio
from core.agent_manager import AgentManager
from core.file_processor import process_file_to_text

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

# --- New Endpoint: Setup (Receives Topic and File) ---
@app.route("/api/setup", methods=["POST"])
def setup_debate():
    global initial_topic, global_context
    data = request.get_json()
    
    initial_topic = data.get('topic', '').strip()
    file_content_b64 = data.get('file_content_base64')
    file_name = data.get('file_name')

    if not initial_topic:
        return jsonify({"error": "Topic is required"}), 400

    global_context = ""

    if file_content_b64 and file_name:
        try:
            # 1. Decode base64 and save to a temporary file
            file_bytes = base64.b64decode(file_content_b64)
            temp_file_path = os.path.join("audio_references", f"context_{file_name}")
            with open(temp_file_path, "wb") as f:
                f.write(file_bytes)
            
            # 2. Process the file content
            processed_text = process_file_to_text(temp_file_path)
            
            # 3. Store the processed text globally
            if "[ERROR:" in processed_text:
                return jsonify({"error": f"File processing failed: {processed_text}"}), 400
            
            global_context = processed_text
            os.remove(temp_file_path) # Clean up temp file
            print(f"Context loaded (length: {len(global_context)} chars)")

        except Exception as e:
            return jsonify({"error": f"Server failed to process file: {e}"}), 500

    return jsonify({"message": "Setup successful. Ready to debate."}), 200

# --- Modified Endpoint: Test (Starts Debate) ---
@app.route("/api/test", methods=["POST"])
def start_turn():
    global manager, initial_topic, last_response, global_context # Include global_context
    data = request.get_json()

    # --- Setup/Reset Logic ---
    prompt_1 = data['agent_1']
    prompt_2 = data['agent_2']
    end = data['end']

    if end:
        manager = None
        initial_topic = ""
        global_context = "" # <-- NEW: Reset context
        return jsonify({"message": "Debate session ended."}) # Return early if ending

    if manager is None:
        # Initialize AgentManager with stored topic and context
        context_prompt = f"Using the following context information: --- {global_context} ---, start the debate on the topic: {initial_topic}" if global_context else initial_topic
        
        # NOTE: AgentManager needs to be updated to accept the personas and context
        # For now, we pass prompt_1 and prompt_2 as the INITIAL prompt text for the debate,
        # but the ideal implementation would have AgentManager.__init__ accept the personas
        # and run_turn accept the context for the first turn.
        
        manager = AgentManager(prompt_1, prompt_2) # Assume AgentManager now takes personas
        last_response = context_prompt # Start the debate prompt
    
    # --- Turn Logic ---
    response1 = manager.run_turn(last_response)
    response2 = manager.run_turn(response1)
    last_response = response2

    # --- Audio Generation (Placeholder/Testing) ---
    # NOTE: You MUST update generate_dialogue_audio in core/audio_api.py 
    # to handle the full file path from the user uploads, not defaults.
    
    # Placeholder paths need to be updated to use the paths of the files uploaded 
    # by the user in the HTML form, or we use a temporary file structure.
    
    # For now, we assume a.wav and b.wav are temporary file names that generate_dialogue_audio writes to.
    
    generate_dialogue_audio(response1, "audio_references/a.wav", DEFAULT_VOICE_MABEL, audio_speed_factor=1.1)
    generate_dialogue_audio(response2, "audio_references/b.wav", DEFAULT_VOICE_EN_MAN, audio_speed_factor=1.1)

    # --- Return Data ---
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
    # Ensure the directory for saving temporary audio/context files exists
    os.makedirs("audio_references", exist_ok=True)
    app.run(debug=True)
