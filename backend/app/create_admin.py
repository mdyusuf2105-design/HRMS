
import getpass

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def main():
    name = input("Admin full name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password (hidden): ")

    if len(password) < 12:
        raise SystemExit("Use an admin password of at least 12 characters.")

    db: Session = SessionLocal()

    try:
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            raise SystemExit("That email already exists. No changes made.")

        admin = User(
            full_name=name,
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()
        print("Admin account created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
