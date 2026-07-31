import json
import hashlib
import time


class DialogueManager:
    """Менеджер збереження та хешування діалогів."""

    def __init__(self):
        self.dialogues = {}  # node_id -> діалог

    def add_message(self, peer_id: bytes, text: str, packet_data: bytes):
        """Додає повідомлення в діалог."""
        if peer_id not in self.dialogues:
            self.dialogues[peer_id] = {
                "block_hash": None,
                "block_size": 0,
                "word_count": 0,
                "message_count": 0,
                "messages": []
            }

        dh = self.dialogues[peer_id]
        dh["messages"].append({
            "text": text,
            "timestamp": int(time.time()),
            "packet_hash": hashlib.sha256(packet_data).hexdigest()[:16]
        })
        dh["message_count"] += 1
        dh["word_count"] += len(text.split())

        # Оновлюємо хеш блоку
        block_data = json.dumps(dh["messages"], ensure_ascii=False).encode('utf-8')
        dh["block_hash"] = hashlib.sha256(block_data).hexdigest()[:16]
        dh["block_size"] = len(block_data)

    def get_stats(self, peer_id: bytes = None) -> dict:
        """Повертає статистику діалогів."""
        if peer_id:
            dh = self.dialogues.get(peer_id)
            return {
                "block_hash": dh["block_hash"],
                "block_size": dh["block_size"],
                "word_count": dh["word_count"],
                "message_count": dh["message_count"]
            } if dh else {}

        return {
            pid.hex()[:8]: {
                "block_hash": dh["block_hash"],
                "block_size": dh["block_size"],
                "word_count": dh["word_count"],
                "message_count": dh["message_count"]
            }
            for pid, dh in self.dialogues.items()
        }