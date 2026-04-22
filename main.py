import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from db import db
from models import User
from auth import require_auth


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "SQLALCHEMY_DATABASE_URI",
        os.environ.get("DATABASE_URL", "postgresql://appuser:apppass@localhost:5432/users"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    
    # Enable CORS for Vercel frontend
    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",  # Development
                "https://*.vercel.app"     # Vercel deployment
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    @app.route("/users", methods=["POST"])
    @require_auth
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
    @require_auth
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

    @app.route("/users/email/<email>", methods=["GET"])
    def get_user_by_email(email):
        """Get user by email address"""
        user = User.query.filter_by(email=email).first()

        if user is None:
            abort(404)

        return jsonify({
            "id": str(user.id),
            "name": user.name,
            "email": user.email
        }), 200

    @app.route("/users/sync", methods=["POST"])
    @require_auth
    def sync_user():
        """Sync user from Auth0 token to database (create if not exists)"""
        import sys
        # Get user info from JWT payload
        user_email = request.token_payload.get("email")
        user_name = request.token_payload.get("name")
        user_sub = request.token_payload.get("sub")
        
        print(f"[SYNC_USER] Token payload keys: {list(request.token_payload.keys())}", file=sys.stderr, flush=True)
        print(f"[SYNC_USER] Email: {user_email}, Name: {user_name}, Sub: {user_sub}", file=sys.stderr, flush=True)
        
        if not user_sub:
            print(f"[SYNC_USER] Missing sub. Full payload: {request.token_payload}", file=sys.stderr, flush=True)
            return jsonify({"error": "Sub not found in token"}), 400
        
        # If no email is provided, derive it from sub (e.g., "google-oauth2|12345" -> "google-oauth2-12345@auth0.local")
        if not user_email:
            user_email = f"{user_sub.replace('|', '-')}@auth0.local"
            print(f"[SYNC_USER] Derived email from sub: {user_email}", file=sys.stderr, flush=True)
        
        # If no name is provided, use part of the sub
        if not user_name:
            user_name = user_sub.split('|')[-1] if '|' in user_sub else user_sub
            print(f"[SYNC_USER] Derived name from sub: {user_name}", file=sys.stderr, flush=True)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=user_email).first()
        if existing_user:
            print(f"[SYNC_USER] User already exists: {existing_user.id}", file=sys.stderr, flush=True)
            return jsonify({
                "id": str(existing_user.id),
                "name": existing_user.name,
                "email": existing_user.email,
                "created": False
            }), 200
        
        # Create new user
        try:
            new_user = User(
                name=user_name,
                email=user_email
            )
            db.session.add(new_user)
            db.session.commit()
            print(f"[SYNC_USER] User created: {new_user.id}", file=sys.stderr, flush=True)
            
            return jsonify({
                "id": str(new_user.id),
                "name": new_user.name,
                "email": new_user.email,
                "created": True
            }), 201
        except Exception as e:
            db.session.rollback()
            print(f"[SYNC_USER] Error creating user: {str(e)}", file=sys.stderr, flush=True)
            return jsonify({"error": str(e)}), 500

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=True, port=5000)