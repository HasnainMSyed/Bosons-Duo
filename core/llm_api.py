# Assume that we will get the LLM API key

import os
import requests # Standard library for making HTTP requests
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

# --- Configuration ---
BOSON_API_KEY = os.getenv("BOSON_API_KEY")
BOSON_LLM_ENDPOINT = os.getenv("BOSON_LLM_ENDPOINT")

# --- Simplification ---
# We no longer need the complex `transformers.pipeline` object for the LLM.
# We just need a function to send a request to the provided endpoint.

class LLMAgent:
    """Represents a single conversational agent with memory and optional search."""
    
    def __init__(self, name: str, persona: str, use_search: bool = False):
        self.name = name
        self.persona = persona
        self.use_search = use_search  # New flag for grounding
        self.history: List[Dict[str, str]] = [{"role": "system", "content": self.persona}]
        
    def _perform_search_and_ground(self, topic: str) -> str:
        """
        Simulates an external search to ground the response.
        In a real scenario, this would use a dedicated Search API (like the Google Search tool).
        """
        if not self.use_search:
            return ""

        print(f"[{self.name}] Performing search for: {topic}...")
        
        # --- SIMULATING GOOGLE SEARCH ---
        # In a final application, this function would call the Google Search API
        # with the topic and format the results into a string.
        
        # Since we cannot call a live API outside the generation workflow, 
        # we will simulate the integration and rely on the LLM to process the grounding text
        
        # NOTE: For the hackathon demo, you would need to implement the actual 
        # API call here using `requests` to a provided search endpoint.
        
        # Placeholder search results:
        search_results = [
            "Source 1: A report from the IMF suggests global inflation will drop to 3.5% by mid-2026.",
            "Source 2: Recent labor data from the US shows 500k new jobs were added in Q3.",
            "Source 3: The debate over AI regulation centers on data privacy and model safety."
        ]
        
        grounding_text = "\n\n--- Search Results for Context ---\n" + "\n".join(search_results) + "\n-------------------------------\n"
        return grounding_text

    def generate_response(self, prompt: str, max_tokens: int = 250, search_query: Optional[str] = None) -> str:
        """Generates a text response for the agent, optionally using grounded search results."""
        
        if not BOSON_LLM_ENDPOINT or not BOSON_API_KEY:
            return f"[{self.name}]: LLM connection failed. API endpoint or key missing."
        
        # 1. Perform Search/Grounding if requested
        grounding_context = self._perform_search_and_ground(search_query or prompt)
        
        # 2. Add the combined prompt (context + turn prompt) to history
        full_user_prompt = grounding_context + prompt
        self.history.append({"role": "user", "content": full_user_prompt})
        
        headers = {
            "Authorization": f"Bearer {BOSON_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": self.history,
            "max_tokens": max_tokens,
            "temperature": 0.7 
            # In a real setup, we might add a `tools: ["google_search"]` property here
        }
        
        try:
            response = requests.post(BOSON_LLM_ENDPOINT, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            # Assuming a standard LLM chat completion response structure
            text_response = data['choices'][0]['message']['content'].strip() 
            
            # 3. Update history with the model's response
            self.history.append({"role": "assistant", "content": text_response})
            
            # For the UI, we return the Agent's name and its generated text
            return f"{self.name}: {text_response}"

        except requests.exceptions.RequestException as e:
            self.history.pop() 
            return f"[{self.name}]: API ERROR (LLM): {e}. Please check your key or endpoint."
