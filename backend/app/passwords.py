"""Password strength rules (pure Python, no framework needed)."""
import re
from typing import Optional

COMMON_PASSWORDS = {
    "password", "password1", "password12", "password123", "password1234", "passw0rd123", "1234567890",
    "12345678910", "123456789012", "qwertyuiop", "qwerty12345", "qwerty123456", "1q2w3e4r5t", "iloveyou123",
    "welcome123", "welcome1234", "admin12345", "administrator", "letmein123", "abcdefghij", "abcd123456",
    "medimate123", "medimate1234", "changeme123", "trustno1234", "monkey12345", "dragon12345",
}


def check_password_strength(password: str, email: Optional[str] = None) -> Optional[str]:
    """Return an error message, or None if the password is acceptable."""
    if len(password) < 10:
        return "Password must be at least 10 characters"
    if password.lower() in COMMON_PASSWORDS:
        return "That password is too common - choose something less guessable"
    if len(set(password)) < 4:
        return "Password is too repetitive"
    classes = sum(bool(re.search(p, password)) for p in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]"))
    if classes < 2 and len(password) < 14:
        return "Mix letters, numbers or symbols, or use a longer passphrase (14+ characters)"
    if email:
        local = email.split("@")[0].lower()
        if len(local) >= 4 and local in password.lower():
            return "Password should not contain your email name"
    return None
