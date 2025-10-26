import gradio as gr
import os
from typing import Optional, Any

# --- Constants ---
ALLOWED_FILE_TYPES = [".docx", ".pdf", ".txt"]

# --- Gradio Interface Definition ---

with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as app:
    with gr.Tab("Topic Setup") as step1_tab:
        gr.Markdown("# 🤖 The AI Dialogist - Step 1: Setup Topic")
        gr.Markdown(
            "Enter the topic you want the AI agents to discuss and optionally upload a context document."
        )

        with gr.Row():  # Use Rows and Columns for layout control
            # Empty columns on the sides to push content to the center
            gr.Column(scale=1)

            with gr.Column(scale=2):  # Central column for inputs
                topic_input = gr.Textbox(
                    label="Debate Topic",
                    placeholder="e.g., The impact of AI on creative industries...",
                    lines=3,
                    elem_id="topic-input-box",  # Add ID for potential CSS styling
                )

                context_file_input = gr.File(
                    label="Optional: Upload Context File",
                    file_types=ALLOWED_FILE_TYPES,
                    type="filepath",  # Get the temporary filepath
                    elem_id="context-file-upload",
                )

                # Button to proceed to the next step (logic to be added later)
                button_to_configure_agents = gr.Button(
                    "Next: Configure Agents ➡️", variant="primary"
                )

            # Empty column on the right
            gr.Column(scale=1)

    with gr.Tab("Agent Setup") as step2_tab:
        gr.Markdown("# 🤖 The AI Dialogist - Step 2: Setup Agent")
        gr.Markdown("Configure the AI Agent")

        with gr.Row():  # Use Rows and Columns for layout control
            # Empty columns on the sides to push content to the center
            gr.Column(scale=1)

            with gr.Column(scale=2):  # Central column for inputs
                agent_1_description = gr.Textbox(
                    label="Describe Agent 1",
                    placeholder="e.g., You are an environmental authoritarian",
                    lines=3,
                    elem_id="topic-input-box",
                )

                agent_2_description = gr.Textbox(
                    label="Describe Agent 2",
                    placeholder="e.g., You are a person advocating for degrowth",
                    lines=3,
                    elem_id="topic-input-box",
                )

                button_to_start_debate = gr.Button("Start debate!", variant="primary")

            # Empty column on the right
            gr.Column(scale=1)

    # --- Event Handling (Placeholder) ---
    def process_step1(topic: str,  context_file: Optional[Any]) -> str:
        """Placeholder function for the 'Next' button."""
        print("Step 1 Data:")
        print(f"Topic: {topic}")
        if context_file:
            print(f"Context File Path: {context_file}")  # Gradio passes the temp path
            # Later: Add logic here to read/process the file
            # For now, just acknowledge it was received
            return f"Received Topic and File: {os.path.basename(context_file)}. Proceeding..."
        else:
            print("No context file uploaded.")
            return f"Received Topic: '{topic}'. Proceeding..."

    # Placeholder status display
    status_output = gr.Textbox(label="Status", interactive=False, visible=False)

    button_to_configure_agents.click(
        fn=process_step1,
        inputs=[topic_input, context_file_input],
        outputs=[status_output],  # For now, just show status
        # Later: This button will hide Step 1 UI and show Step 2 UI
    )

# --- Launch the Application ---
if __name__ == "__main__":
    app.launch(share=False)
