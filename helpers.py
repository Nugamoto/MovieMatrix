import re


def is_valid_username(name: str) -> bool:
    if not name:
        return False
    if not re.search(r"[a-zA-Z]", name):
        return False
    return True

def get_user_by_id(users: list, user_id: int):
    return next((user for user in users if user.id == user_id), None)