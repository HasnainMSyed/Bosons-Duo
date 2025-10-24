from core.llm_api import LLMAgent
from typing import List

class AgentManager:
    """Manages the two conversational agents and runs the dialogue."""
    
    # Define Agent Personas to showcase emotional range and distinct voices
    PERSONA_A = "You are Agent A, a witty, enthusiastic, and optimistic tech analyst. You speak with high energy, focusing on creative solutions and future potential. You are starting the discussion."
    PERSONA_B = "You are Agent B, a cautious, logical, and skeptical finance analyst. You speak with a calm, measured, and objective tone, focusing on cost and risks."
    
    def __init__(self):
        # Initialize the two distinct agents
        self.agent_a = LLMAgent(name="Agent A (Optimist)", persona=self.PERSONA_A)
        self.agent_b = LLMAgent(name="Agent B (Skeptic)", persona=self.PERSONA_B)
        
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