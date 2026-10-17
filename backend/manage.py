"""
Admin/maintenance commands.

  python manage.py create-admin --email you@example.com
"""
import argparse
import getpass
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.db_models import User


def create_admin(email: str, password: str):
    email = email.strip().lower()
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters")
    if User.query.filter_by(email=email).first():
        raise SystemExit("A user with this email already exists")
    db.session.add(User(
        email=email, name="Admin", role="admin", onboarded=True,
        password_hash=generate_password_hash(password),
    ))
    db.session.commit()
    print(f"Admin created: {email}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create-admin", help="Create an admin account")
    p.add_argument("--email", required=True)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.cmd == "create-admin":
            create_admin(args.email, getpass.getpass("Admin password: "))


if __name__ == "__main__":
    main()
