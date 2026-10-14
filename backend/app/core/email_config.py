def send_email(to_email: str, subject: str, body: str) -> bool:
    print("\n" + "=" * 45)
    print("[DEMO EMAIL NOTIFICATION]")
    print("=" * 45)
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("Status: Simulated successfully — no real email sent")
    print("-" * 45)
    print(body)
    print("=" * 45 + "\n")
    return True
