# Contains code that could reused if we need HuggingFace models

'''
import os
from dotenv import load_dotenv
from transformers import pipeline

# Environment name: boson-duo-env

load_dotenv()

HF_ACCESS_TOKEN = os.getenv("HF_Access_Token")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")

try:
    LLM_PIPELINE = pipeline(
        "text-generation", # Purpose is to generate text
        model=LLM_MODEL_NAME, # Use this model
        token=HF_ACCESS_TOKEN, # Use the HF token
        device=0 # device=0 for GPU, device=-1 for CPU
    )
except Exception as e:
    print(f"Error loading LLM Pipeline: {e}")
    # Fallback/Placeholder LLM (Useful if the model is too large or slow)
    LLM_PIPELINE = None

class LLMAgent():
    def __init__(self, name: str, persona: str):
        self.name = name
        self.persona = persona
        self.history = [{"role": "system", "content": self.persona}]

    def generate_response(self, prompt: str, max_tokens: int = 150) -> str:
        if LLM_PIPELINE is None:
            return f"[{self.name}]: LLM connection failed. Responding with placeholder text to the prompt: {prompt}"
        
        self.history.append({"role": "user", "content": prompt})

        try:
            response = LLM_PIPELINE(
                self.history,
                max_new_token=max_tokens,
                do_sample=True,
                temperature=0.7,
                return_full_text=False
            )

            text_response = response[0]['generated_text'].strip()

            self.history.append({"role": "assistant", "content": text_response})

            return f"{self.name}: {text_response}"

        except Exception as e:
            # Revert history for the failed turn
            self.history.pop() 
            return f"[{self.name}]: ERROR generating response: {e}"

'''