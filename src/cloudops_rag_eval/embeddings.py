import hashlib
import math
import re

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "use",
    "with",
}
EXPANSIONS = {
    "artifact": ("model", "storage", "bucket"),
    "budget": ("billing", "cost", "spend"),
    "cheap": ("low", "cost", "budget"),
    "cloud": ("run", "gcp"),
    "cost": ("billing", "quota", "budget"),
    "deploy": ("deployment", "release", "cloud", "run"),
    "deployment": ("deploy", "release", "revision"),
    "kubernetes": ("unsupported", "clusters", "target"),
    "permission": ("access", "service", "account"),
    "quota": ("billing", "limit", "cost"),
    "rollback": ("restore", "previous", "revision"),
    "token": ("api", "authorization", "secret"),
    "troubleshoot": ("failure", "error", "startup"),
    "restarting": ("restart", "startup", "loop"),
    "restarts": ("restart", "startup", "loop"),
}


class HashingEmbeddingFunction:
    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in input]

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in expanded_tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            raw = int.from_bytes(digest, "big")
            index = raw % self.dimensions
            sign = 1.0 if raw & 1 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def expanded_tokens(text: str) -> list[str]:
    tokens = [token for token in TOKEN_RE.findall(text.lower()) if token not in STOP_WORDS]
    expanded: list[str] = []

    for token in tokens:
        expanded.append(token)
        expanded.extend(EXPANSIONS.get(token, ()))

    expanded.extend(f"{left}_{right}" for left, right in zip(tokens, tokens[1:], strict=False))
    return expanded
