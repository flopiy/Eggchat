class LLG:
    def __init__(self):
        self.word_to_id = {}
        self.id_to_word = {}
        self.next_id = 1

    def encode(self, text: str) -> list:
        """Перетворює текст на список ID, створюючи нові ID для нових слів."""
        ids = []
        for word in text.split():
            if word not in self.word_to_id:
                self.word_to_id[word] = self.next_id
                self.id_to_word[self.next_id] = word
                self.next_id += 1
            ids.append(self.word_to_id[word])
        return ids

    def decode(self, ids: list) -> str:
        """Відновлює текст зі списку ID."""
        words = []
        for wid in ids:
            words.append(self.id_to_word.get(wid, f"<UNK({wid})>"))
        return " ".join(words)

    def add_word(self, word: str, forced_id: int):
        """
        Додає слово з примусовим ID (для синхронізації від відправника).
        Якщо ID вже існує з іншим словом – ігноруємо (у реальній системі потрібен
        механізм вирішення конфліктів, але для прототипу це нормально).
        """
        if forced_id in self.id_to_word:
            # Слово вже є, нічого не робимо
            return
        self.id_to_word[forced_id] = word
        self.word_to_id[word] = forced_id
        if forced_id >= self.next_id:
            self.next_id = forced_id + 1

    @property
    def size(self):
        """Кількість унікальних слів."""
        return len(self.word_to_id)

    def stats(self, original_text: str, encoded_ids: list) -> dict:
        """Статистика стиснення для конкретного повідомлення."""
        original_bytes = len(original_text.encode('utf-8'))
        encoded_bytes = len(encoded_ids) * 2  # 2 байти на ID
        saved = original_bytes - encoded_bytes
        percent = (saved / original_bytes * 100) if original_bytes > 0 else 0
        return {
            "original_bytes": original_bytes,
            "encoded_bytes": encoded_bytes,
            "saved_bytes": saved,
            "compression_ratio": f"{percent:.1f}%"
        }