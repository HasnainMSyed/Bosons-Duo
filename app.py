from flask import Flask
from flask_cors import CORS
from core.agent_manager import AgentManager

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "Hello, Flask Server is Running! 🚀"


@app.route("/api/test")
def test():

    prompt1, prompt2 = "", ""
    condition = False

    initial_topic = _
    last_response = initial_topic
    manager = AgentManager(prompt1, prompt2)
    files = []
    while condition:
        response1 = manager.run_turn(last_response)
        response2 = manager.run_turn(response1)
        last_response = response2

        # turn response1 and response2 into audio files

        # append files to files list

    return {"message": "This is a JSON response"}


if __name__ == "__main__":
    app.run(debug=True)
