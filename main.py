import os
from flask import Flask, request, jsonify, abort
from db import db
from models import User


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "SQLALCHEMY_DATABASE_URI",
        os.environ.get("DATABASE_URL", "postgresql://appuser:apppass@localhost:5432/users"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

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
        user = db.session.get(User, user_id)

        if user is None:
            abort(404)

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

    @app.route("/users/<uuid:user_id>", methods=["GET"])
    def get_user(user_id):
        user = db.session.get(User, user_id)

        if user is None:
            abort(404)

        return jsonify({
            "id": str(user.id),
            "name": user.name,
            "email": user.email
        }), 200

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True, port=5000)