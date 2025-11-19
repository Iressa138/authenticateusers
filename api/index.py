from flask import Flask, jsonify

app = Flask(__name__)

ALLOWED_USERS = [
    "6337049A5066F60A",
    "DBD8B6CBA6FB98D8",
    "user_3"
]

@app.route("/api/giveaccess", methods=["GET"])
def give_access():
    """
    Returns a JSON object containing the list of allowed users.
    Format matches Unity's BackendList class:
    { "users": ["user_1", "user_2", ...] }
    """
    return jsonify({"users": ALLOWED_USERS})

if __name__ == "__main__":
    app.run(debug=True)
