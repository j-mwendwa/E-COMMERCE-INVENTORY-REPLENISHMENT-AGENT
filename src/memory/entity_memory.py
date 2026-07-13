import json

from cryptography.fernet import Fernet, InvalidToken

from src.config import ROOT_DIR, settings

MEMORY_DIR = ROOT_DIR / "data" / "memory"
ENCRYPTED_PREFIX = "ENCRYPTED_V1:"


class EntityMemory:
    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.path = MEMORY_DIR / f"{thread_id}.json"
        self._cipher: Fernet | None = None
        key = settings.memory_encryption_key
        if key:
            self._cipher = Fernet(key.encode() if isinstance(key, str) else key)
        self._facts: dict[str, str] = {}
        self._load()

    def remember(self, key: str, value: str) -> None:
        self._facts[key] = value
        self._save()

    def update(self, facts: dict[str, str]) -> None:
        self._facts.update(facts)
        self._save()

    def all(self) -> dict[str, str]:
        return dict(self._facts)

    def clear(self) -> None:
        self._facts = {}
        self._save()

    def _load(self) -> None:
        if not self.path.exists():
            self._facts = {}
            return
        raw = self.path.read_text()
        if self._cipher and raw.startswith(ENCRYPTED_PREFIX):
            try:
                raw = self._cipher.decrypt(raw[len(ENCRYPTED_PREFIX):].encode()).decode()
            except InvalidToken as err:
                raise ValueError("Memory decryption failed: invalid key or corrupted data") from err
        self._facts = json.loads(raw)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(self._facts, indent=2)
        if self._cipher:
            encrypted = self._cipher.encrypt(raw.encode()).decode()
            self.path.write_text(ENCRYPTED_PREFIX + encrypted)
        else:
            self.path.write_text(raw)
