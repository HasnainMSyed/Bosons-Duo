import gradio as gr
import time
from core.agent_manager import AgentManager
from core.audio_api import generate_dialogue_audio
from typing import Tuple, List, Optional, Dict

# --- Global Variables & Constants ---
MAX_TURNS = 10 # Limit the number of turns in a debate

def limiter(max_turn: int, max_time: float, user_input: bool, self_stop: bool):
    pass

# --- UI Helper Functions ---

def start_debate(
    topic: str,
    voice_a_path: Optional[str],
    voice_b_path: Optional[str]
) -> Tuple[AgentManager, List[Tuple[Optional[str], Optional[str]]], str, Optional[str], Optional[str], gr.update, gr.update, gr.update, gr.update]:
    """
    Initializes a new debate when the 'Start Debate' button is clicked.
    Sets up the manager, runs the first turn, and updates the UI.
    """
    if not topic.strip():
        return None, [], "Error: Please provide a topic.", None, None, gr.update(), gr.update(), gr.update(), gr.update()
        
    if not voice_a_path or not voice_b_path:
        return None, [], "Error: Please upload both voice reference files.", None, None, gr.update(), gr.update(), gr.update(), gr.update()

    # 1. Initialize the Agent Manager
    manager = AgentManager()
    
    # 2. Run the first turn (Agent A starts)
    try:
        first_response = manager.run_turn(topic)
        
        # 3. Generate audio for the first turn (includes only Agent A's response)
        audio_bytes = generate_dialogue_audio(first_response, voice_a_path, voice_b_path)
        
        # 4. Prepare UI updates
        # Gradio chatbot format: List of [user_message, bot_message] tuples
        chat_history_display = [(topic, first_response)] 
        status_message = f"Turn 1 complete. Agent B's turn."
        audio_output_path = None
        
        if audio_bytes:
            # Save audio to a temporary file for Gradio to play
            audio_output_path = f"turn_{len(manager.dialogue_history)}.mp3"
            with open(audio_output_path, "wb") as f:
                f.write(audio_bytes)
                
        # Enable/disable buttons
        run_button_update = gr.update(interactive=True)
        stop_button_update = gr.update(interactive=True)
        start_button_update = gr.update(interactive=False) # Disable start until stop
        interrupt_button_update = gr.update(interactive=True)

        return manager, chat_history_display, status_message, audio_output_path, None, run_button_update, stop_button_update, start_button_update, interrupt_button_update

    except Exception as e:
        error_msg = f"Error starting debate: {e}"
        print(error_msg)
        return None, [], error_msg, None, None, gr.update(), gr.update(), gr.update(), gr.update()


def run_next_turn(
    manager: AgentManager,
    chat_history: List[Tuple[Optional[str], Optional[str]]],
    voice_a_path: str,
    voice_b_path: str
) -> Tuple[AgentManager, List[Tuple[Optional[str], Optional[str]]], str, Optional[str], Optional[str]]:
    """
    Runs the next turn of the debate and generates audio for the *latest* response.
    """
    if manager is None:
        return None, chat_history, "Error: Debate not started.", None, None
        
    if len(manager.dialogue_history) >= MAX_TURNS:
        return manager, chat_history, "Debate finished: Maximum turns reached.", None, None

    # Get the last response to feed to the current speaker
    last_response_text = manager.dialogue_history[-1] if manager.dialogue_history else "No previous response."
    
    try:
        # Run the next turn
        current_response = manager.run_turn(last_response_text)
        
        # Generate audio for ONLY the current response segment
        # We need to format the text specifically for single-turn audio generation if the API supports it,
        # otherwise, we might regenerate the whole dialogue which is inefficient.
        # Assuming generate_dialogue_audio can handle the full history and extracts the last part:
        full_dialogue_text_for_audio = manager.get_full_dialogue_text()
        audio_bytes = generate_dialogue_audio(full_dialogue_text_for_audio, voice_a_path, voice_b_path)

        # Update chat display - Append the new response
        # The prompt for the bot is the previous bot's message
        chat_history.append((None, current_response))

        status_message = f"Turn {len(manager.dialogue_history)} complete. {'Agent A' if manager.current_speaker == manager.agent_a else 'Agent B'}'s turn."
        audio_output_path = None
        
        if audio_bytes:
            # Save audio for this turn
            audio_output_path = f"turn_{len(manager.dialogue_history)}.mp3"
            with open(audio_output_path, "wb") as f:
                f.write(audio_bytes)

        return manager, chat_history, status_message, audio_output_path, None # Clear interrupt text

    except Exception as e:
        error_msg = f"Error during turn {len(manager.dialogue_history) + 1}: {e}"
        print(error_msg)
        return manager, chat_history, error_msg, None, None


def stop_debate(manager: Optional[AgentManager]) -> Tuple[Optional[AgentManager], List, str, Optional[str], Optional[str], gr.update, gr.update, gr.update, gr.update]:
    """Resets the manager and clears the UI."""
    if manager:
        manager.reset_dialogue()
    
    # Reset UI elements
    run_button_update = gr.update(interactive=False)
    stop_button_update = gr.update(interactive=False)
    start_button_update = gr.update(interactive=True) # Re-enable start
    interrupt_button_update = gr.update(interactive=False)
    
    return None, [], "Debate stopped and reset. Enter a new topic.", None, None, run_button_update, stop_button_update, start_button_update, interrupt_button_update


def handle_interrupt(
    manager: AgentManager,
    chat_history: List[Tuple[Optional[str], Optional[str]]],
    interrupt_text: str,
    voice_a_path: str,
    voice_b_path: str
) -> Tuple[AgentManager, List[Tuple[Optional[str], Optional[str]]], str, Optional[str], Optional[str]]:
    """Handles user interruption, injecting the text as the next prompt."""
    if not manager:
        return None, chat_history, "Error: Start a debate first.", None, None
    if not interrupt_text.strip():
        return manager, chat_history, "Status: Enter text to interrupt.", None, None

    try:
        # Inject the user's interrupt text as the prompt for the current speaker
        interrupt_prompt = f"USER INTERRUPTS: Please address this point or question immediately: '{interrupt_text}'"
        
        # Run the turn with the interrupt prompt
        response_text = manager.run_turn(interrupt_prompt)
        
        # Generate audio for the response
        full_dialogue_text_for_audio = manager.get_full_dialogue_text()
        audio_bytes = generate_dialogue_audio(full_dialogue_text_for_audio, voice_a_path, voice_b_path)

        # Update chat display
        chat_history.append((f"You interrupted: {interrupt_text}", response_text))

        status_message = f"Interruption processed. Turn {len(manager.dialogue_history)} complete. {'Agent A' if manager.current_speaker == manager.agent_a else 'Agent B'}'s turn."
        audio_output_path = None
        
        if audio_bytes:
            audio_output_path = f"turn_{len(manager.dialogue_history)}.mp3"
            with open(audio_output_path, "wb") as f:
                f.write(audio_bytes)

        return manager, chat_history, status_message, audio_output_path, "" # Clear interrupt text box

    except Exception as e:
        error_msg = f"Error during interruption: {e}"
        print(error_msg)
        return manager, chat_history, error_msg, None, ""


# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 The AI Dialogist")
    gr.Markdown("A platform for two AI agents to discuss topics with cloned voices, powered by Boson AI.")

    # State variable to hold the AgentManager instance
    manager_state = gr.State() 

    with gr.Row():
        with gr.Column(scale=1):
            topic_input = gr.Textbox(label="Debate Topic", placeholder="Enter the topic for the agents to discuss...")
            voice_a_input = gr.File(label="Upload Voice Sample for Agent A (Optimist) (.wav/.mp3)")
            voice_b_input = gr.File(label="Upload Voice Sample for Agent B (Concerned) (.wav/.mp3)")
            start_button = gr.Button("🚀 Start Debate", variant="primary", interactive=True)
            run_button = gr.Button("▶️ Run Next Turn", interactive=False)
            stop_button = gr.Button("⏹️ Stop Debate", variant="stop", interactive=False)
            status_output = gr.Textbox(label="Status", interactive=False)
            
            with gr.Accordion("Interrupt Conversation", open=False):
                interrupt_input = gr.Textbox(label="Your Input / Question", placeholder="Enter text to steer the conversation...")
                interrupt_button = gr.Button("🗣️ Interrupt", interactive=False)
            
            audio_player = gr.Audio(label="Latest Turn Audio", type="filepath", interactive=False)


        with gr.Column(scale=2):
            chatbot_output = gr.Chatbot(label="Debate Transcript", height=600)
            
    # --- Event Handling ---
    start_button.click(
        fn=start_debate,
        inputs=[topic_input, voice_a_input, voice_b_input],
        outputs=[manager_state, chatbot_output, status_output, audio_player, interrupt_input, run_button, stop_button, start_button, interrupt_button]
    )
    
    run_button.click(
        fn=run_next_turn,
        inputs=[manager_state, chatbot_output, voice_a_input, voice_b_input],
        outputs=[manager_state, chatbot_output, status_output, audio_player, interrupt_input] # Pass interrupt_input to potentially clear it
    )
    
    stop_button.click(
        fn=stop_debate,
        inputs=[manager_state],
        outputs=[manager_state, chatbot_output, status_output, audio_player, interrupt_input, run_button, stop_button, start_button, interrupt_button]
    )

    interrupt_button.click(
        fn=handle_interrupt,
        inputs=[manager_state, chatbot_output, interrupt_input, voice_a_input, voice_b_input],
        outputs=[manager_state, chatbot_output, status_output, audio_player, interrupt_input] # Clear interrupt_input after sending
    )

# --- Launch the Application ---
if __name__ == "__main__":
    demo.launch(share=False) # Set share=True to get a public link (use carefully)