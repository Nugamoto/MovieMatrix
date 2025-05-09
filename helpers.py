import re


def is_valid_username(name: str) -> bool:
    if not name:
        return False
    if not re.search(r"[a-zA-Z]", name):
        return False
    return True
