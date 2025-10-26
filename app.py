from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Hello, Flask Server is Running! 🚀"


@app.route("/api/test")
def test():
    return {"message": "This is a JSON response"}


if __name__ == "__main__":
    app.run(debug=True)
