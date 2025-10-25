import gradio as gr
import time
import os
# Import necessary functions/classes from core modules
from core.agent_manager import AgentManager
from core.audio_api import generate_cloned_speech # Use the correct function
# Potentially add a utility for combining audio later: from core.utils import combine_audio_files
from typing import Tuple, List, Optional, Dict, Any

# --- Global Constants ---
MAX_TURNS_DEFAULT = 5
AUDIO_DIR = "generated_audio" # Folder to store temporary audio files
os.makedirs(AUDIO_DIR, exist_ok=True) # Ensure directory exists

# --- Available Personas and Tones (Customize as needed) ---
AVAILABLE_PERSONAS = {
    "Agent A (Optimist)": "You are Agent A, an AI expert hopeful for its future and satisfied with its development. Your goal is to champion progress.",
    "Agent B (Concerned)": "You are Agent B, an AI expert concerned for humanity and AI's growth. Your goal is to highlight ethical risks.",
    "Neutral Analyst": "You are a neutral analyst, providing balanced viewpoints based on facts and potential outcomes.",
    "Creative Storyteller": "You are a creative storyteller, exploring the topic through imaginative scenarios and narratives.",
    "Historical Scholar": "You are a historical scholar, contextualizing the topic with past events and long-term perspectives."
}
AVAILABLE_TONES = ["[neutral]", "[friendly]", "[enthusiastic]", "[skeptical]", "[calm]", "[formal]", "[assertive]", "[concerned]"]


# --- Callback Functions (Implementations based on flowchart logic) ---

def configure_and_start(
    topic: str,
    voice_a_file: Any, # Gradio File object
    transcript_a: str,
    voice_b_file: Any, # Gradio File object
    transcript_b: str,
    max_turns: int,
    persona_a_name: str, # Name selected from dropdown
    persona_b_name: str, # Name selected from dropdown
    tone_a: str,
    tone_b: str
) -> Tuple[
    gr.State, gr.State, gr.State, gr.State, gr.State, # States: manager, audio_files, turn, path_a, path_b
    gr.update, gr.update, # UI Visibility: settings, debate
    gr.update, gr.update, gr.update, # Debate UI: chat, audio, status
    gr.update, gr.update, gr.update # Buttons: next_turn, stop, interrupt
]:
    """
    Handles 'Configure & Start Debate' button click.
    Validates, initializes manager, runs turn 1, generates audio, updates UI visibility and content.
    """
    print("configure_and_start called...")
    # 1. Validation
    error_msg = None
    if not topic.strip(): error_msg = "Topic cannot be empty."
    elif not voice_a_file or not voice_b_file: error_msg = "Both voice samples must be uploaded."
    elif not transcript_a.strip() or not transcript_b.strip(): error_msg = "Both voice transcripts must be provided."
    elif not persona_a_name or not persona_b_name: error_msg = "Both agent personas must be selected."
    elif persona_a_name == persona_b_name: error_msg = "Agents must have different personas."

    if error_msg:
        print(f"Validation Error: {error_msg}")
        # Return state keeping settings visible, show error
        return ( None, [], 0, None, None, # States remain empty/default
                 gr.update(visible=True), gr.update(visible=False), # Keep settings visible
                 [], None, error_msg, # Clear chat/audio, show error status
                 gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False) ) # Keep buttons disabled

    # Save uploaded files temporarily (Gradio provides file objects with a .name attribute for temp path)
    voice_a_path = voice_a_file.name
    voice_b_path = voice_b_file.name
    print(f"Voice A path: {voice_a_path}")
    print(f"Voice B path: {voice_b_path}")

    # 2. Initialize Manager with selected personas
    try:
        persona_a_prompt = AVAILABLE_PERSONAS.get(persona_a_name, AgentManager.PERSONA_A) # Fallback to default
        persona_b_prompt = AVAILABLE_PERSONAS.get(persona_b_name, AgentManager.PERSONA_B) # Fallback to default
        
        # Modify AgentManager if needed to accept personas in __init__ or have a set_personas method
        # For now, we assume it uses defaults or we modify it outside this file
        manager = AgentManager()
        # Potentially: manager.set_personas(persona_a_prompt, persona_b_prompt)
        print("AgentManager initialized.")

        # 3. Run First Turn (Agent A starts)
        print("Running first turn...")
        first_prompt = f"Start the debate on the topic: '{topic}'"
        # The run_turn function in AgentManager needs to handle passing the topic correctly
        # Assuming run_turn now handles the initial prompt appropriately
        first_response_text = manager.run_turn(first_prompt) # Agent A speaks
        print(f"First response: {first_response_text}")
        
        # Extract content for TTS
        first_response_content = first_response_text.split(":", 1)[1].strip() if ":" in first_response_text else first_response_text


        # 4. Generate Audio for First Turn using Agent A's voice and selected tone
        current_turn = 1
        output_audio_filename = os.path.join(AUDIO_DIR, f"turn_{current_turn}.wav") # Use wav or mp3
        print(f"Generating audio for turn {current_turn} using voice A...")
        success = generate_cloned_speech(
            reference_audio_path=voice_a_path,
            reference_transcript=transcript_a,
            text_to_speak=first_response_content,
            output_audio_path=output_audio_filename,
            tone_instruction=tone_a # Use selected tone for Agent A
        )
        print(f"Audio generation success: {success}")

        # 5. Prepare UI Updates
        chat_history_display = [(f"Topic: {topic}", first_response_text)]
        status_message = f"Turn {current_turn}: {persona_a_name} spoke. Waiting for next turn..."
        audio_output_path = output_audio_filename if success else None
        audio_files = [audio_output_path] if audio_output_path else []

        # Return updates to switch UI visibility and populate initial state
        return (
            manager, audio_files, current_turn, voice_a_path, voice_b_path, # State updates
            gr.update(visible=False), # Hide settings tabs
            gr.update(visible=True),  # Show debate interface
            chat_history_display,     # Update chatbot
            gr.update(value=audio_output_path, interactive=True if success else False), # Update audio player
            status_message,           # Update status
            gr.update(interactive=True), # Enable Next Turn button
            gr.update(interactive=True), # Enable Stop button
            gr.update(interactive=True)  # Enable Interrupt button
        )

    except Exception as e:
        print(f"Error during configure_and_start: {e}")
        import traceback
        traceback.print_exc()
        # Return error state
        return (
             None, [], 0, None, None, # Clear states
             gr.update(visible=True), gr.update(visible=False), # Keep settings visible
             [], None, f"Error starting debate: {e}", # Clear chat/audio, show error
             gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False) # Buttons disabled
        )


def run_next_turn_ui(
    manager: AgentManager,
    audio_files: List[str],
    current_turn: int,
    voice_a_ref: str, # Path stored in state
    voice_b_ref: str, # Path stored in state
    transcript_a: str,
    transcript_b: str,
    tone_a: str,
    tone_b: str,
    max_turns: int,
    chat_history: List # Current chatbot display history
) -> Tuple[
    gr.State, gr.State, gr.State, # manager, audio_files, current_turn
    gr.update, gr.update, gr.update, # chat, audio, status
    gr.update, gr.update # next_turn_button, stop_button
]:
    """Handles 'Run Next Turn' button click."""
    print("run_next_turn_ui called...")
    if not manager or not voice_a_ref or not voice_b_ref: # Check paths from state
        return manager, audio_files, current_turn, gr.update(value=chat_history), None, "Error: Debate not started or voice paths missing.", gr.update(), gr.update()

    # Check max turns (Note: current_turn is the number of turns *completed*)
    total_turns_allowed = max_turns * 2 # Each agent gets max_turns
    if current_turn >= total_turns_allowed:
        print("Max turns reached.")
        return manager, audio_files, current_turn, gr.update(value=chat_history), None, "Debate Finished: Max turns reached.", gr.update(interactive=False), gr.update(interactive=True)

    # Determine whose turn it is and which voice/transcript/tone to use
    is_agent_a_turn = (manager.current_speaker == manager.agent_a)
    ref_path = voice_a_ref if is_agent_a_turn else voice_b_ref
    ref_transcript = transcript_a if is_agent_a_turn else transcript_b
    selected_tone = tone_a if is_agent_a_turn else tone_b
    speaker_name = manager.agent_a.name # Get names from manager instance

    # Get the last response text to feed the current speaker
    # Ensure history is not empty and contains valid messages
    last_response_full = manager.dialogue_history[-1] if manager.dialogue_history else "This is the start of the debate."
    
    try:
        # Run the next turn's logic
        print(f"Running turn {current_turn + 1} for {speaker_name}...")
        # The prompt is constructed inside manager.run_turn based on the last response passed
        current_response_text = manager.run_turn(last_response_full)
        print(f"Response: {current_response_text}")

        # Extract content for TTS
        current_response_content = current_response_text.split(":", 1)[1].strip() if ":" in current_response_text else current_response_text

        # Generate audio for the current response
        next_turn_number = current_turn + 1
        output_audio_filename = os.path.join(AUDIO_DIR, f"turn_{next_turn_number}.wav")
        print(f"Generating audio for turn {next_turn_number}...")
        success = generate_cloned_speech(
            reference_audio_path=ref_path,
            reference_transcript=ref_transcript,
            text_to_speak=current_response_content,
            output_audio_path=output_audio_filename,
            tone_instruction=selected_tone
        )
        print(f"Audio generation success: {success}")

        # Update state and UI
        current_turn += 1
        audio_output_path = output_audio_filename if success else None
        if audio_output_path:
            audio_files.append(audio_output_path)

        # Append to Gradio chat history
        # Format: [[user_msg1, bot_msg1], [user_msg2, bot_msg2], ...]
        # For agent vs agent, we can show None for user or the previous agent's response
        chat_history.append([None, current_response_text])

        # Check if max turns reached *after* this turn
        if current_turn >= total_turns_allowed:
            status_message = "Debate Finished: Max turns reached."
            next_turn_interactive = False # Disable next turn button
        else:
             # Determine *next* speaker's name for status message
             next_speaker_name = manager.agent_b.name if is_agent_a_turn else manager.agent_a.name
             status_message = f"Turn {current_turn}: {speaker_name} spoke. Waiting for {next_speaker_name}..."
             next_turn_interactive = True

        return (
             manager, audio_files, current_turn, # State updates
             gr.update(value=chat_history),   # Update chat display
             gr.update(value=audio_output_path, interactive=True if success else False), # Update audio player
             status_message,                  # Update status message
             gr.update(interactive=next_turn_interactive), # Update next turn button interactivity
             gr.update() # Keep stop button as is
         )

    except Exception as e:
        print(f"Error during run_next_turn_ui: {e}")
        import traceback
        traceback.print_exc()
        # Keep state as is, show error message
        return manager, audio_files, current_turn, gr.update(value=chat_history), None, f"Error on turn {current_turn+1}: {e}", gr.update(), gr.update()


def stop_button_click() -> Tuple[gr.update, gr.update, gr.update]:
    """Reveals the stop confirmation."""
    print("Stop button clicked, showing confirmation...")
    # Hide debate controls, show confirmation
    # We hide the main debate interface elements individually for better control
    return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True) # Hide buttons, show confirm row


def confirm_stop_logic() -> Tuple[
    gr.State, gr.State, gr.State, gr.State, gr.State, # Clear states
    gr.update, gr.update, gr.update, # UI Visibility: settings, debate, confirm row
    gr.update, gr.update, gr.update, # UI Content: chat, audio, status
    gr.update, gr.update, gr.update # Buttons: next, stop, interrupt
]:
    """Resets everything and returns to settings tab."""
    print("Stop confirmed, resetting...")
    # Reset state and UI elements
    return (
        None, [], 0, None, None, # Clear states
        gr.update(visible=True),  # Show settings tabs/interface
        gr.update(visible=False), # Hide debate interface
        gr.update(visible=False), # Hide stop confirmation row
        [], None, "Debate stopped. Configure a new one.", # Clear chat, audio, status
        gr.update(interactive=False), # Disable next turn
        gr.update(interactive=False), # Disable stop
        gr.update(interactive=False)  # Disable interrupt
    )


def cancel_stop_logic() -> Tuple[gr.update, gr.update, gr.update]:
    """Hides the stop confirmation and returns to debate."""
    print("Stop cancelled, returning to debate...")
    # Hide confirmation, show debate controls
    return gr.update(visible=True), gr.update(visible=True), gr.update(visible=False) # Show buttons, hide confirm row


def handle_interrupt_ui(
    manager: AgentManager,
    audio_files: List[str],
    current_turn: int,
    voice_a_ref: str,
    voice_b_ref: str,
    transcript_a: str,
    transcript_b: str,
    tone_a: str,
    tone_b: str,
    chat_history: List,
    interrupt_text: str
) -> Tuple[
    gr.State, gr.State, gr.State, # manager, audio_files, current_turn
    gr.update, gr.update, gr.update, # chat, audio, status
    gr.update # interrupt input clear
]:
    """Handles user interruption."""
    print("handle_interrupt_ui called...")
    error_output = "" # To clear interrupt box even on error
    if not manager or not voice_a_ref or not voice_b_ref:
        return manager, audio_files, current_turn, gr.update(value=chat_history), None, "Error: Start debate first.", error_output
    if not interrupt_text.strip():
        return manager, audio_files, current_turn, gr.update(value=chat_history), None, "Status: Enter text to interrupt.", error_output

    # Determine whose turn it is to respond to the interrupt
    is_agent_a_turn = (manager.current_speaker == manager.agent_a)
    ref_path = voice_a_ref if is_agent_a_turn else voice_b_ref
    ref_transcript = transcript_a if is_agent_a_turn else transcript_b
    selected_tone = tone_a if is_agent_a_turn else tone_b
    speaker_name = manager.agent_a.name

    interrupt_prompt = f"USER INTERRUPTS: Please pause your current argument and address this point or question immediately: '{interrupt_text}'"

    try:
        print(f"Running interrupt response for {speaker_name}...")
        # Manager's run_turn handles context and gets response
        response_text = manager.run_turn(interrupt_prompt)
        print(f"Interrupt response: {response_text}")

        # Extract content for TTS
        response_content = response_text.split(":", 1)[1].strip() if ":" in response_text else response_text

        # Generate audio for the interrupt response
        # Note: Turn number doesn't advance here, use a unique filename
        output_audio_filename = os.path.join(AUDIO_DIR, f"interrupt_{current_turn}_{time.time()}.wav")
        print(f"Generating audio for interrupt response...")
        success = generate_cloned_speech(
            reference_audio_path=ref_path,
            reference_transcript=ref_transcript,
            text_to_speak=response_content,
            output_audio_path=output_audio_filename,
            tone_instruction=selected_tone # Apply correct tone
        )
        print(f"Audio generation success: {success}")

        # Update chat display showing the interruption and response
        chat_history.append([f"You: {interrupt_text}", response_text])

        # Determine next speaker name for status
        next_speaker_name = manager.agent_b.name if is_agent_a_turn else manager.agent_a.name
        status_message = f"Interruption processed. {speaker_name} responded. Waiting for {next_speaker_name}..."
        audio_output_path = output_audio_filename if success else None
        
        # Don't increment current_turn state here

        # Return state updates and UI updates
        return (
             manager, audio_files, current_turn, # State updates (turn unchanged)
             gr.update(value=chat_history),   # Update chat display
             gr.update(value=audio_output_path, interactive=True if success else False), # Update audio player
             status_message,                  # Update status message
             "" # Clear interrupt input box
         )

    except Exception as e:
        print(f"Error during handle_interrupt_ui: {e}")
        import traceback
        traceback.print_exc()
        # Return error state, keep interrupt text in box
        return manager, audio_files, current_turn, gr.update(value=chat_history), None, f"Error processing interrupt: {e}", interrupt_text


# --- Gradio Interface Definition (Using Tabs and Visibility Control) ---
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky")) as demo:
    gr.Markdown("# 🤖 The AI Dialogist - Mode 1: AI vs AI Debate")
    gr.Markdown("Configure the agents, start the debate, and listen to the conversation unfold.")

    # --- State Variables ---
    manager_state = gr.State() # Holds the AgentManager object
    audio_files_state = gr.State([]) # List of generated audio file paths for potential export
    current_turn_state = gr.State(0) # Track current turn number (completed turns)
    voice_a_ref_path_state = gr.State() # Store temp path of uploaded voice A
    voice_b_ref_path_state = gr.State() # Store temp path of uploaded voice B

    # --- UI Components ---
    # Settings Area (Uses Tabs, Initially visible)
    with gr.Column(visible=True) as settings_interface:
        with gr.Tabs() as settings_tabs:
            # --- Tab 1: Topic & Voices ---
            with gr.TabItem("1. Topic & Voices", id=0):
                gr.Markdown("### Define the Debate Core")
                topic_input = gr.Textbox(label="Debate Topic", placeholder="e.g., Should AI development be regulated?", lines=2)
                gr.Markdown("---")
                gr.Markdown("### Agent Voices & Transcripts")
                gr.Markdown("Upload a short (5-15 second) WAV audio sample for each agent and provide the **exact** text spoken in that sample.")
                with gr.Row():
                    with gr.Column():
                        voice_a_input = gr.File(label="Upload Voice Sample: Agent A (.wav recommended)", type="filepath")
                        transcript_a_input = gr.Textbox(label="Exact Transcript for Voice A Sample", lines=3, placeholder="Paste the text spoken in the audio file above...")
                    with gr.Column():
                        voice_b_input = gr.File(label="Upload Voice Sample: Agent B (.wav recommended)", type="filepath")
                        transcript_b_input = gr.Textbox(label="Exact Transcript for Voice B Sample", lines=3, placeholder="Paste the text spoken in the audio file above...")

            # --- Tab 2: Personas & Tones ---
            with gr.TabItem("2. Personas & Tones", id=1):
                gr.Markdown("### Define Agent Personalities and Speaking Styles")
                with gr.Row():
                    with gr.Column():
                        persona_a_select = gr.Dropdown(label="Select Persona for Agent A", choices=list(AVAILABLE_PERSONAS.keys()), value="Agent A (Optimist)")
                        tone_a_select = gr.Dropdown(label="Select Speaking Tone for Agent A", choices=AVAILABLE_TONES, value="[enthusiastic]")
                    with gr.Column():
                        persona_b_select = gr.Dropdown(label="Select Persona for Agent B", choices=list(AVAILABLE_PERSONAS.keys()), value="Agent B (Concerned)")
                        tone_b_select = gr.Dropdown(label="Select Speaking Tone for Agent B", choices=AVAILABLE_TONES, value="[concerned]")

            # --- Tab 3: Configuration & Run ---
            with gr.TabItem("3. Configure & Run", id=2):
                gr.Markdown("### Set Debate Parameters")
                max_turns_input = gr.Slider(label="Max Turns (Total for Both Agents)", minimum=2, maximum=20, value=MAX_TURNS_DEFAULT * 2, step=2)
                # auto_next_turn_input = gr.Checkbox(label="Automatically proceed to next turn?", value=False) # Keep manual for MVP
                gr.Markdown("---")
                configure_start_button = gr.Button("🚀 Configure & Start Debate", variant="primary", scale=2)


    # Debate Area (Initially Hidden)
    with gr.Column(visible=False) as debate_interface:
        gr.Markdown("## 💬 Debate in Progress...")
        current_status_display = gr.Textbox(label="Status", interactive=False, show_label=False, lines=1)

        chatbot_output = gr.Chatbot(label="Debate Transcript", height=500, show_label=False, avatar_images=(None, "🤖")) # Add a simple bot avatar
        audio_player = gr.Audio(label="Latest Turn Audio", type="filepath", interactive=False)

        with gr.Row():
             next_turn_button = gr.Button("▶️ Run Next Turn", interactive=False)
             stop_button = gr.Button("⏹️ Stop Debate", variant="stop", interactive=False)

        with gr.Accordion("⚙️ Interrupt / Steer Conversation", open=False):
             interrupt_input = gr.Textbox(label="Your Input / Question", placeholder="Type here to guide the discussion...", show_label=False, lines=2)
             interrupt_button = gr.Button("🗣️ Send Interrupt", interactive=False) # Initially disabled

        # Hidden confirmation row for Stop action
        with gr.Row(visible=False) as stop_confirm_row:
             gr.Markdown("❓ **Are you sure you want to stop the debate and return to setup?**")
             confirm_stop_button = gr.Button("✔️ Yes, Stop", variant="stop")
             cancel_stop_button = gr.Button("❌ No, Continue")

        # Final Export Area (Placeholder - Implement export later if time permits)
        # with gr.Column(visible=False) as export_area:
        #      gr.Markdown("## 🏁 Debate Finished")
        #      # Need function to combine files in audio_files_state
        #      export_button = gr.Button("Download Full Debate Audio (.wav)")
        #      final_audio_display = gr.File(label="Combined Audio")


    # --- Event Wiring ---

    # Configure & Start Button (Triggers the main logic)
    configure_start_button.click(
        fn=configure_and_start,
        inputs=[
            topic_input, voice_a_input, transcript_a_input, voice_b_input, transcript_b_input,
            max_turns_input, persona_a_select, persona_b_select, tone_a_select, tone_b_select
        ],
        outputs=[
            manager_state, audio_files_state, current_turn_state, voice_a_ref_path_state, voice_b_ref_path_state, # States
            settings_interface, debate_interface, # UI Visibility
            chatbot_output, audio_player, current_status_display, # Debate UI Content
            next_turn_button, stop_button, interrupt_button # Button Interactivity
        ]
    )

    # Next Turn Button
    next_turn_button.click(
        fn=run_next_turn_ui,
        inputs=[
            manager_state, audio_files_state, current_turn_state,
            voice_a_ref_path_state, voice_b_ref_path_state, # Use paths from state
            transcript_a_input, transcript_b_input, # Get transcripts from UI inputs
            tone_a_select, tone_b_select, # Get tones from UI inputs
            max_turns_input, chatbot_output
        ],
        outputs=[
            manager_state, audio_files_state, current_turn_state, # States
            chatbot_output, audio_player, current_status_display, # UI Content
            next_turn_button, stop_button # Button Interactivity
        ]
    )

    # Stop Button (Shows Confirmation)
    stop_button.click(
        fn=stop_button_click,
        inputs=[],
        # Hide the main interactive buttons and show the confirmation row
        outputs=[next_turn_button, stop_button, stop_confirm_row]
    )

    # Confirm Stop Button (Resets Everything)
    confirm_stop_button.click(
        fn=confirm_stop_logic,
        inputs=[],
        outputs=[
            manager_state, audio_files_state, current_turn_state, voice_a_ref_path_state, voice_b_ref_path_state, # States
            settings_interface, debate_interface, stop_confirm_row, # UI Visibility
            chatbot_output, audio_player, current_status_display, # UI Content Reset
            next_turn_button, stop_button, interrupt_button # Button Interactivity Reset
        ]
    )

    # Cancel Stop Button (Returns to Debate)
    cancel_stop_button.click(
        fn=cancel_stop_logic,
        inputs=[],
         # Show the main interactive buttons and hide the confirmation row
        outputs=[next_turn_button, stop_button, stop_confirm_row]
    )

    # Interrupt Button
    interrupt_button.click(
        fn=handle_interrupt_ui,
        inputs=[
            manager_state, audio_files_state, current_turn_state,
            voice_a_ref_path_state, voice_b_ref_path_state, # Use paths from state
            transcript_a_input, transcript_b_input, # Get transcripts from UI
            tone_a_select, tone_b_select, # Get tones from UI
            chatbot_output, interrupt_input
        ],
        outputs=[
            manager_state, audio_files_state, current_turn_state, # States
            chatbot_output, audio_player, current_status_display, # UI Content
            interrupt_input # Clear interrupt box
        ]
    )


# --- Launch the Application ---
if __name__ == "__main__":
    demo.launch(share=False) # Share=True gives a public link (use with caution)