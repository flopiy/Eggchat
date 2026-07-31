import os
import hashlib
import threading
from pathlib import Path
from protocol.packet import Packet, PacketType


class FileManager:
    """Менеджер передачі файлів через чанки."""

    def __init__(self, node_id, peers, send_callback):
        self.node_id = node_id
        self.peers = peers  # PeerManager
        self.send_packet = send_callback  # func(sock, packet)

        # Сховище
        self.data_dir = Path(f"data/{self.node_id.hex()[:16]}")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "blocks").mkdir(exist_ok=True)
        (self.data_dir / "files").mkdir(exist_ok=True)

        # Активні передачі
        self._pending_files = {}  # file_id -> {"name":..., "chunks":[], "received": set()}

    def send(self, filepath: str) -> bool:
        """Відправляє файл усім пірам."""
        if self.peers.count() == 0:
            return False

        filepath = filepath.strip('"').strip("'")
        filepath = Path(filepath)
        if not filepath.exists():
            filepath = Path.cwd() / filepath
            if not filepath.exists():
                return False

        file_id = os.urandom(16)
        file_name = filepath.name
        file_size = filepath.stat().st_size
        chunk_size = 65536  # 64 KB

        # Розбиваємо на чанки
        chunks = []
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                chunk_hash = hashlib.sha256(data).digest()
                chunks.append((chunk_hash, data))

        # FILE_ANNOUNCE
        payload = (
                file_id +
                len(file_name).to_bytes(2, 'big') + file_name.encode() +
                file_size.to_bytes(8, 'big') +
                len(chunks).to_bytes(4, 'big')
        )
        for chunk_hash, _ in chunks:
            payload += chunk_hash

        announce_pkt = Packet(PacketType.FILE_ANNOUNCE, payload)
        for sock in self.peers.all_sockets():
            try:
                self.send_packet(sock, announce_pkt)
            except Exception:
                self.peers.remove_by_socket(sock)

        # Відправляємо чанки
        for i, (chunk_hash, data) in enumerate(chunks):
            payload = (
                    file_id +
                    i.to_bytes(4, 'big') +
                    len(data).to_bytes(4, 'big') +
                    chunk_hash +
                    data
            )
            chunk_pkt = Packet(PacketType.FILE_CHUNK, payload)
            for sock in self.peers.all_sockets():
                try:
                    self.send_packet(sock, chunk_pkt)
                except Exception:
                    self.peers.remove_by_socket(sock)

        return True

    def handle_announce(self, payload) -> dict:
        """Обробляє FILE_ANNOUNCE, повертає метадані файлу."""
        file_id = payload[:16]
        name_len = int.from_bytes(payload[16:18], 'big')
        file_name = payload[18:18 + name_len].decode()
        file_size = int.from_bytes(payload[18 + name_len:26 + name_len], 'big')
        num_chunks = int.from_bytes(payload[26 + name_len:30 + name_len], 'big')

        chunk_hashes = []
        offset = 30 + name_len
        for _ in range(num_chunks):
            chunk_hashes.append(payload[offset:offset + 32])
            offset += 32

        self._pending_files[file_id] = {
            "name": file_name,
            "size": file_size,
            "chunks": chunk_hashes,
            "received": set()
        }

        return {
            "file_id": file_id.hex()[:8],
            "name": file_name,
            "size": file_size,
            "num_chunks": num_chunks
        }

    def handle_chunk(self, payload) -> dict:
        """Обробляє FILE_CHUNK, повертає статус."""
        file_id = payload[:16]
        chunk_index = int.from_bytes(payload[16:20], 'big')
        chunk_size = int.from_bytes(payload[20:24], 'big')
        chunk_hash = payload[24:56]
        data = payload[56:56 + chunk_size]

        if file_id not in self._pending_files:
            return None

        pfile = self._pending_files[file_id]

        # Перевіряємо хеш
        actual_hash = hashlib.sha256(data).digest()
        if actual_hash != chunk_hash:
            return None

        # Зберігаємо блок
        block_path = self.data_dir / "blocks" / chunk_hash.hex()
        with open(block_path, 'wb') as f:
            f.write(data)

        pfile["received"].add(chunk_index)

        # Перевіряємо, чи всі чанки отримано
        complete = len(pfile["received"]) == len(pfile["chunks"])

        result = {
            "chunk_index": chunk_index,
            "total": len(pfile["chunks"]),
            "complete": complete
        }

        if complete:
            result["file_path"] = str(self._reassemble(file_id))

        return result

    def _reassemble(self, file_id) -> Path:
        """Збирає файл із чанків."""
        pfile = self._pending_files.pop(file_id)
        file_path = self.data_dir / "files" / pfile["name"]

        with open(file_path, 'wb') as out:
            for chunk_hash in pfile["chunks"]:
                block_path = self.data_dir / "blocks" / chunk_hash.hex()
                with open(block_path, 'rb') as inp:
                    out.write(inp.read())

        return file_path