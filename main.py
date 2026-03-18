import os
import time
from flask import Flask, request, jsonify
from db import db
from models import User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://appuser:apppass@localhost:5432/users"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    retries = 10
    while retries > 0:
        try:
            db.create_all()
            print("Database connected and tables created!")
            break
        except Exception as e:
            retries -= 1
            print(f"Database not ready, retrying in 3s... ({retries} retries left)")
            time.sleep(3)
    if retries == 0:
        print("Could not connect to database after multiple retries")
        raise SystemExit(1)

@app.route("/users", methods=["POST"])
def create_user():
    data = request.json

    user = User(
        name=data["name"],
        email=data["email"]
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": str(user.id),
        "name": user.name,
        "email": user.email
    }), 201


@app.route("/users/<uuid:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    return "", 204

@app.route("/users", methods=["GET"])
def list_users():
    users = User.query.all()

    return [
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email
        }
        for user in users
    ], 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)


@app.route("/users/<uuid:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)

    return jsonify({
        "id": str(user.id),
        "name": user.name,
        "email": user.email
    }), 200