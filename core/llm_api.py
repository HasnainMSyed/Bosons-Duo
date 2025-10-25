import os
from dotenv import load_dotenv
import openai
from typing import List, Dict, Optional
from openai.types.chat import ChatCompletionMessageParam

load_dotenv() 

BOSON_API_KEY = os.getenv("BOSON_API_KEY")
LLM_MODEL_NAME = "Qwen3-32B-non-thinking-Hackathon" 
BASE_URL = "https://hackathon.boson.ai/v1"

# 1. API Key Check
if not BOSON_API_KEY:
    # Log an error but do not exit, allowing the rest of the application to run (graceful failure)
    print("FATAL ERROR: BOSON_API_KEY not found. LLM functionality is disabled.")
    CLIENT = None
else:
    # 2. Initialize the OpenAI-compatible client once globally
    CLIENT = openai.Client(
        api_key=BOSON_API_KEY,
        base_url=BASE_URL 
    )

class LLMAgent:
    """
    Represents a single conversational agent with a defined persona, 
    memory (history), and the capability to generate responses 
    via the Boson LLM API.
    """
    
    def __init__(self, name: str, persona: str, model: str):
        self.name = name
        self.model = model
        self.persona = persona
        
        # History stores the ChatML format required by the API: 
        # [{"role": "system", "content": persona}, {"role": "user", "content": "..."}]
        self.history: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.persona}
        ]
        
    def generate_response(self, prompt: str, max_tokens: int = 250) -> str:
        if CLIENT is None:
            return f"[{self.name}]: ERROR - LLM client is not initialized due to missing API key."

        # 1. Add the new incoming prompt/context from the user or other agent to history
        # We model the previous agent's output as the "user" role to drive the conversation
        self.history.append({"role": "user", "content": prompt})
        
        try:
            # 2. Make the API call using the full history as context
            response = CLIENT.chat.completions.create(
                model=self.model,
                messages=self.history,  # Passing the list of messages for history/context
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            # 3: Safe Content Extraction and Tool Check ---
            
            message_content = response.choices[0].message.content
            
            # Check if content is None (often happens if a tool call is made or response is blocked)
            if message_content is None:
                # Check for tool calls (if model is designed to use them)
                tool_calls = response.choices[0].message.tool_calls
                if tool_calls:
                    # If the model is using a tool, we report the action instead of crashing.
                    text_response = f"DECISION: {self.name} is calling a tool. Output content is None."
                else:
                    # If content is None and no tool call, the response was likely empty or blocked.
                    text_response = "The model returned an empty response. Response may be blocked."
            else:
                # Content exists, so we safely strip the whitespace
                text_response = message_content.strip()
            
            # 4. Add the model's reply (as the 'assistant') back into the history for continuity
            self.history.append({"role": "assistant", "content": text_response})
            
            # Return the agent's name and the text content for the UI
            return f"{self.name}: {text_response}"

        except openai.APIError as e:
            # Revert the last user prompt to keep history clean on failure
            self.history.pop() 
            print(f"API CALL FAILED for {self.name}: {e}")
            return f"[{self.name}]: API ERROR: {e}"
        except Exception as e:
            self.history.pop() 
            print(f"An unexpected error occurred for {self.name}: {e}")
            return f"[{self.name}]: UNEXPECTED ERROR: {e}"

# Note: The original test call logic is removed from this file, as it is 
# now encapsulated in the LLMAgent class and will be driven by the AgentManager.
