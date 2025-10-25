from .llm_api import LLMAgent
from typing import List

LLM_MODEL_NAME = "Qwen3-32B-non-thinking-Hackathon"

class AgentManager:
    """Manages the two conversational agents and runs the dialogue."""
    
    # Define Agent Personas to showcase emotional range and distinct voices
    PERSONA_A = "You are agent A, and you are an AI expert that is hopeful for its future and satisfied with its development."
    PERSONA_B = "You are agent B, and you are an AI expert that is concerned for humanity and the way AI grows."
    
    def __init__(self):
        # Initialize the two distinct agents
        self.agent_a = LLMAgent(name="Agent A (Optimist)", persona=self.PERSONA_A, model=LLM_MODEL_NAME)
        self.agent_b = LLMAgent(name="Agent B (Concerned)", persona=self.PERSONA_B, model=LLM_MODEL_NAME)
        
        # Track the current speaking agent
        self.current_speaker = self.agent_a
        self.dialogue_history: List[str] = [] # Stores text output for the UI/TTS
        
    def reset_dialogue(self):
        """Resets both agents' memories and the dialogue history."""
        self.agent_a.history = [{"role": "system", "content": self.PERSONA_A}]
        self.agent_b.history = [{"role": "system", "content": self.PERSONA_B}]
        self.dialogue_history = []
        self.current_speaker = self.agent_a

    def run_turn(self, prompt_text: str = "") -> str:
        """
        Runs one turn of the conversation.
        The prompt_text is the previous agent's output, or the user's initial prompt.
        """
        
        # Determine the listener (the other agent)
        listener = self.agent_b if self.current_speaker == self.agent_a else self.agent_a

        # The prompt for the current speaker is the previous speaker's output (or the user's input)
        turn_prompt = f"Previous Speaker said: {prompt_text}. Respond to them and continue the argument."

        # 1. Generate the response
        response_text = self.current_speaker.generate_response(turn_prompt)
        
        # 2. Store the result
        self.dialogue_history.append(response_text)
        
        # 3. Swap speaker for the next turn
        self.current_speaker = listener

        # The manager needs to return the *text* of the response so the UI can update
        # and so the audio API can be called.
        return response_text

    def get_full_dialogue_text(self) -> str:
        """Returns the entire dialogue text formatted for easy reading."""
        return "\n".join(self.dialogue_history)

if __name__ == "__main__":
    manager = AgentManager()
    
    # 2. Define the initial topic
    initial_topic = "The rapid development of AGI: Is it a net benefit or a catastrophic risk to human employment and creativity?"
    
    print("--- Starting Debate ---")
    print(f"Topic: {initial_topic}\n")

    # The debate starts with the manager giving the first agent (Agent A) the topic.
    last_response = initial_topic
    
    NUM_TURNS = 6 # Run 3 turns per agent (6 total responses)
    
    for i in range(NUM_TURNS):
        print(f"--- Turn {i + 1} ---")
        
        try:
            # Run one turn of the conversation
            response = manager.run_turn(last_response)
            
            # Print the response to the console
            print(response)
            
            # Update the last response to feed the next agent
            last_response = response
            
            # Simple delay to prevent overwhelming the API during the test
            import time
            time.sleep(2) 
            
        except Exception as e:
            print(f"Error during turn {i + 1}: {e}")
            break

    print("\n--- Debate Finished ---")
    print("\nFull Dialogue:")
    print(manager.get_full_dialogue_text())