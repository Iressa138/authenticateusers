from flask import Flask, jsonify, request

app = Flask(__name__)

authorized_users = ["332CEA12FB8C08AD"]

@app.route("/api/giveaccess", methods=["GET"])
def get_users():
    return jsonify({"users": authorized_users})

@app.route("/api/giveaccess", methods=["POST"])
def add_user():
    data = request.get_json()
    user_id = data.get("user_id")
    if user_id and user_id not in authorized_users:
        authorized_users.append(user_id)
    return jsonify({"users": authorized_users})

@app.route("/api/giveaccess", methods=["DELETE"])
def remove_user():
    data = request.get_json()
    user_id = data.get("user_id")
    if user_id in authorized_users:
        authorized_users.remove(user_id)
    return jsonify({"users": authorized_users})

if __name__ == "__main__":
    app.run()
