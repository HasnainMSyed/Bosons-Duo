import gradio as gr
import os
from typing import Optional, Any, Tuple, List

# --- Constants ---
ALLOWED_FILE_TYPES = [".docx", ".pdf", ".txt"]
# Placeholder agent names - these will come from configuration later
AGENT_A_NAME = "Agent A (Optimist)"
AGENT_B_NAME = "Agent B (Concerned)"

# --- Placeholder Backend Functions (Simulate Agent Logic) ---
# We'll replace these with actual calls to core/agent_manager.py later
def initialize_debate_backend(topic: str, context_file_path: Optional[str]) -> Tuple[str, str]:
    """Simulates initializing the debate and getting the first turn."""
    print(f"Backend: Initializing debate on '{topic}'")
    if context_file_path:
        print(f"Backend: Using context file '{os.path.basename(context_file_path)}'")
        # Add actual file reading logic here later
    first_speaker = AGENT_A_NAME
    first_message = f"Okay, let's discuss '{topic}'. As an optimist, I see great potential..."
    return first_speaker, first_message

def get_next_turn_backend(current_speaker: str, last_message: str) -> Tuple[str, str]:
    """Simulates getting the next agent's response."""
    print(f"Backend: Getting response to '{last_message[:50]}...'")
    if current_speaker == AGENT_A_NAME:
        next_speaker = AGENT_B_NAME
        next_message = f"While I understand your optimism ({AGENT_A_NAME}), we must consider the risks..."
    else:
        next_speaker = AGENT_A_NAME
        next_message = f"That's a valid concern ({AGENT_B_NAME}), but innovation requires bold steps..."
    return next_speaker, next_message

# --- Gradio UI Logic ---

def show_debate_interface(topic: str, context_file: Optional[Any]) -> Tuple[gr.update, gr.update, gr.update, gr.update, gr.update, gr.update, str]:
    """
    Callback for the 'Next: Configure Agents' button.
    Hides setup, shows debate UI, runs first turn, highlights speaker A.
    """
    print("Switching to Debate Interface...")
    
    # Store topic/file path if needed (using gr.State would be better for multi-turn)
    # For now, just pass topic to backend init
    context_file_path = context_file.name if context_file else None
    
    # --- Simulate Backend Initialization ---
    try:
        current_speaker, current_message = initialize_debate_backend(topic, context_file_path)
        
        # Determine initial highlighting
        agent_a_box_update = gr.update(value=f"**{AGENT_A_NAME} (Speaking...)**") # Highlight A
        agent_b_box_update = gr.update(value=f"{AGENT_B_NAME}")                 # Unhighlight B
        
        # Prepare updates
        hide_setup = gr.update(visible=False)
        show_debate = gr.update(visible=True)
        update_main_text = gr.update(value=f"**{current_speaker}:**\n\n{current_message}")
        
        return hide_setup, show_debate, agent_a_box_update, agent_b_box_update, update_main_text, current_speaker, "" # Return current speaker name for state

    except Exception as e:
        print(f"Error initializing debate: {e}")
        # Keep setup visible, show error (we need a status box in setup UI)
        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), "", f"Error: {e}"


def run_next_turn_interface(current_speaker_name: str, last_message_display: str) -> Tuple[gr.update, gr.update, gr.update, str]:
    """
    Callback for the 'Next Turn' button in the debate interface.
    Gets next turn, updates highlighting, updates main text.
    """
    print(f"Running next turn. Current speaker was: {current_speaker_name}")
    
    # Extract last message content (remove speaker prefix if present)
    last_message_content = last_message_display.split("\n\n", 1)[-1] if "\n\n" in last_message_display else last_message_display

    # --- Simulate Backend Call ---
    try:
        next_speaker, next_message = get_next_turn_backend(current_speaker_name, last_message_content)

        # Update highlighting
        if next_speaker == AGENT_A_NAME:
            agent_a_box_update = gr.update(value=f"**{AGENT_A_NAME} (Speaking...)**")
            agent_b_box_update = gr.update(value=f"{AGENT_B_NAME}")
        else:
            agent_a_box_update = gr.update(value=f"{AGENT_A_NAME}")
            agent_b_box_update = gr.update(value=f"**{AGENT_B_NAME} (Speaking...)**")
            
        update_main_text = gr.update(value=f"**{next_speaker}:**\n\n{next_message}")
        
        # Return updates including the name of the *new* current speaker
        return agent_a_box_update, agent_b_box_update, update_main_text, next_speaker

    except Exception as e:
         print(f"Error getting next turn: {e}")
         # Keep highlighting as is, show error in main text? Or add a status box
         return gr.update(), gr.update(), gr.update(value=f"Error: {e}"), current_speaker_name # Keep speaker state

# --- Gradio Interface Definition ---

# Use a dark theme
with gr.Blocks(theme=gr.themes.Base(primary_hue="blue"), mode="dark") as demo:
    
    # --- State ---
    # Store the name of the agent whose turn it is currently
    current_speaker_state = gr.State(value=AGENT_A_NAME) 

    # --- UI Section 1: Setup (Initially Visible) ---
    with gr.Column(visible=True) as setup_interface:
        gr.Markdown("# 🤖 The AI Dialogist - Step 1: Setup Topic")
        gr.Markdown("Enter the topic and optionally upload a context document.")

        with gr.Row():
            gr.Column(scale=1) # Left Spacer
            with gr.Column(scale=2): # Center Content
                topic_input = gr.Textbox(
                    label="Debate Topic",
                    placeholder="e.g., The impact of AI on creative industries...",
                    lines=3,
                )
                context_file_input = gr.File(
                    label="Optional: Upload Context File (.docx, .pdf, .txt)",
                    file_types=ALLOWED_FILE_TYPES,
                    type="filepath",
                )
                # Button to proceed to the next step
                setup_next_button = gr.Button("Next: Start Debate ➡️", variant="primary")
                setup_status_output = gr.Textbox(label="Status", interactive=False, visible=False) # For errors in this step
            gr.Column(scale=1) # Right Spacer

    # --- UI Section 2: Debate Interface (Initially Hidden) ---
    with gr.Column(visible=False) as debate_interface:
        gr.Markdown("# 💬 Debate Interface")
        
        # Top Quarter: Agent "Boxes" (Zoom Grid simulation)
        with gr.Row(equal_height=False): # Allow columns to size naturally
            with gr.Column(scale=1, min_width=150): # Agent A Box
                 # Use Textbox for easier background styling/updates if needed later
                agent_a_box = gr.Markdown(f"{AGENT_A_NAME}", elem_classes=["agent-box"]) 
                gr.Markdown(f"*{AGENT_A_NAME}*", elem_classes=["agent-name"])
            with gr.Column(scale=1, min_width=150): # Agent B Box
                agent_b_box = gr.Markdown(f"{AGENT_B_NAME}", elem_classes=["agent-box"])
                gr.Markdown(f"*{AGENT_B_NAME}*", elem_classes=["agent-name"])
            # Add more columns here later if supporting > 2 agents
            gr.Column(scale=2) # Spacer to push agent boxes left

        gr.Markdown("---") # Separator

        # Bottom Three Quarters: Main Output and Controls
        with gr.Column():
             # Large Textbox for current speaker's output
             main_output_display = gr.Textbox(
                 label="Current Speaker Output",
                 lines=15, # Make it tall
                 interactive=False,
                 show_label=False
             )
             with gr.Row():
                 # Controls below the main text
                 debate_next_turn_button = gr.Button("▶️ Next Turn")
                 debate_stop_button = gr.Button("⏹️ Stop Debate", variant="stop")
                 # Add interrupt elements here later

    # --- Event Handling ---
    
    # Button click for Step 1 -> Step 2 transition
    setup_next_button.click(
        fn=show_debate_interface,
        inputs=[topic_input, context_file_input],
        outputs=[
            setup_interface,      # Hide setup UI
            debate_interface,     # Show debate UI
            agent_a_box,          # Update Agent A highlight
            agent_b_box,          # Update Agent B highlight
            main_output_display,  # Show first turn text
            current_speaker_state,# Update speaker state
            setup_status_output   # Show potential error from init
        ]
    )
    
    # Button click for advancing turns in the debate UI
    debate_next_turn_button.click(
        fn=run_next_turn_interface,
        inputs=[current_speaker_state, main_output_display], # Pass current speaker and last message
        outputs=[
            agent_a_box,          # Update Agent A highlight
            agent_b_box,          # Update Agent B highlight
            main_output_display,  # Show next turn text
            current_speaker_state # Update speaker state
        ]
    )
    
    # Placeholder for Stop button logic (would likely hide debate, show setup)
    # debate_stop_button.click(...)


# --- Launch the Application ---
if __name__ == "__main__":
    demo.launch(share=False)

