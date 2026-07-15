import unicodedata

def normalize_name(name: str) -> str:
    """Instantly reduces any player name variation to a clean search key."""
    if not isinstance(name, str): 
        return ""
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower().strip()