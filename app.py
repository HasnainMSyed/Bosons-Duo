import base64
import os
import io
from flask_cors import CORS
from flask import Flask, request, jsonify, send_file
from core.audio_api import generate_dialogue_audio
from core.agent_manager import AgentManager
from core.file_processor import process_file_to_text
from core.audio_utils import combine_audio_files

DEFAULT_VOICE_EN_MAN = "en_man"
DEFAULT_VOICE_MABEL = "mabel"

app = Flask(__name__)
CORS(app)

manager = None
initial_topic = ""
last_response = ""
audio_file_paths = []

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
    global manager, initial_topic, last_response, global_context, audio_file_paths # Include global_context
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
        audio_file_paths = [] 
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

    # --- Audio Generation (Generate Unique Files) ---
    # Generate unique filenames based on the current turn number for permanent storage
    turn_count = len(audio_file_paths) // 2 
    
    file_a_path = os.path.join("audio_references", f"turn_{turn_count+1}_A.wav")
    file_b_path = os.path.join("audio_references", f"turn_{turn_count+1}_B.wav")
    
    generate_dialogue_audio(response1, "audio_references/a.wav", DEFAULT_VOICE_MABEL, audio_speed_factor=1.1)
    generate_dialogue_audio(response2, "audio_references/b.wav", DEFAULT_VOICE_EN_MAN, audio_speed_factor=1.1)

    audio_file_paths.append(file_a_path)
    audio_file_paths.append(file_b_path)

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

@app.route("/api/export", methods=["GET"])
def export_debate_audio():
    """Combines all turn audio files and returns the master WAV file for download."""
    global audio_file_paths
    
    if not audio_file_paths:
        return jsonify({"error": "No debate audio has been generated yet."}), 404

    # Define the final combined filename
    combined_filename = "full_debate_podcast.wav"
    combined_filepath = os.path.join("audio_references", combined_filename)

    # 1. Combine the audio files
    combined_path = combine_audio_files(audio_file_paths, combined_filepath)
    
    if not combined_path:
        return jsonify({"error": "Failed to combine audio files."}), 500

    # 2. Serve the file to the client
    try:
        # send_file is a Flask function that serves a file from the server
        return send_file(combined_path, mimetype='audio/wav', as_attachment=True, download_name=combined_filename)
    except Exception as e:
        print(f"Error serving export file: {e}")
        return jsonify({"error": "Server error serving file."}), 500
    
if __name__ == "__main__":
    # Ensure the directory for saving temporary audio/context files exists
    os.makedirs("audio_references", exist_ok=True)
    app.run(debug=True)
