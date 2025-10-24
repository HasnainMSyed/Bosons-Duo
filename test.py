# Simple test.py in your root folder
from core.agent_manager import AgentManager

manager = AgentManager()
initial_prompt = "Let's debate the risks and rewards of large-scale solar power deployment."

# Run the first turn (Agent A starts)
response_a = manager.run_turn(initial_prompt)
print(response_a)

# Run the second turn (Agent B responds)
response_b = manager.run_turn(response_a)
print(response_b)