import uuid


def generate_uuid() -> str:
    """Generate a unique identifier string."""
    return str(uuid.uuid4())
