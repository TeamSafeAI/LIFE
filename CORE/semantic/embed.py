"""
Embedding service client. Talks to localhost:5050.
"""

import json
import math
import urllib.request
import urllib.error

EMBED_URL = 'http://127.0.0.1:5050/encode'


def encode(text):
    """Get 384-dim embedding from service. Returns list of floats or None if service down."""
    try:
        data = json.dumps({'text': text}).encode('utf-8')
        req = urllib.request.Request(EMBED_URL, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get('embedding')
    except (urllib.error.URLError, TimeoutError, Exception):
        return None


def cosine_similarity(a, b):
    """Cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)
