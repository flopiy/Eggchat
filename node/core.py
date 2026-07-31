import os
import socket
import threading
import time
import traceback
from protocol.packet import Packet, PacketType
from node.peer_manager import PeerManager
from node.discovery_manager import DiscoveryManager
from node.message_manager import MessageManager
from node.file_manager import FileManager
from node.dialogue_manager import DialogueManager


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class Node:
    """Координатор вузла. Об'єднує всі менеджери."""

    def __init__(self, host="0.0.0.0", port=None, name=None, rendezvous_host=None, rendezvous_port=None):
        self.node_id = os.urandom(16)
        self.name = name or self.node_id.hex()[:8]
        self.local_ip = get_local_ip()
        self.port = port or self._find_free_port()
        self.bind_host = host if host not in ("0.0.0.0", "", None) else "0.0.0.0"
        self.running = False

        # Менеджери
        self.peers = PeerManager()
        self.messages = MessageManager(self.node_id, self.peers, self._send_packet)
        self.files = FileManager(self.node_id, self.peers, self._send_packet)
        self.dialogues = DialogueManager()
        self.discovery = DiscoveryManager(self.node_id, self.port, self._on_peer_found)

        # Rendezvous
        self.rendezvous_addr = None
        if rendezvous_host and rendezvous_port:
            self.rendezvous_addr = (rendezvous_host, rendezvous_port)

        self.server_socket = None

    def _find_free_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    # ====================== Запуск/зупинка ======================
    def start(self):
        self.running = True

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.bind_host, self.port))
        self.server_socket.listen(10)

        threading.Thread(target=self._accept_connections, daemon=True).start()
        self.discovery.start()

        if self.rendezvous_addr:
            threading.Thread(target=self._auto_register, daemon=True).start()

        print("=" * 60)
        print("  DCP Node Started")
        print("=" * 60)
        print(f"  Name      : {self.name}")
        print(f"  Node ID   : {self.node_id.hex()[:16]}")
        print(f"  Port      : {self.port}")
        print(f"  Local IP  : {self.local_ip}")
        print(f"  Discovery : ACTIVE")
        if self.rendezvous_addr:
            print(f"  Rendezvous: {self.rendezvous_addr[0]}:{self.rendezvous_addr[1]}")
        print("=" * 60)
        print()

    def stop(self):
        self.running = False
        self.discovery.stop()
        self.peers.clear()
        if self.server_socket:
            self.server_socket.close()
        print("Node stopped")

    def _auto_register(self):
        time.sleep(1)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(self.rendezvous_addr)
            import json
            request = {
                "cmd": "register",
                "node_id": self.node_id.hex(),
                "port": self.port
            }
            pkt = Packet(PacketType.MESSAGE, json.dumps(request).encode())
            self._send_packet(sock, pkt)
            sock.close()
        except Exception:
            pass

    # ====================== Мережеві методи ======================
    def _on_peer_found(self, ip, port):
        threading.Thread(target=self._connect_to, args=(ip, port), daemon=True).start()

    def _connect_to(self, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            sock.settimeout(None)
            init_pkt = Packet(PacketType.HANDSHAKE_INIT, self.node_id)
            self._send_packet(sock, init_pkt)
            threading.Thread(target=self._listen_connection, args=(sock,), daemon=True).start()
        except Exception:
            pass

    def _accept_connections(self):
        print(f"[Server] Listening on {self.bind_host}:{self.port}")
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    client_sock, addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                print(f"[Server] Connection from {addr[0]}:{addr[1]}")
                threading.Thread(target=self._handle_client, args=(client_sock, addr), daemon=True).start()
            except Exception:
                if self.running:
                    pass

    def _handle_client(self, sock, addr):
        try:
            while self.running:
                packet = self._recv_packet(sock)
                if not packet:
                    break
                self._process_packet(packet, sock, addr)
        except Exception:
            pass
        finally:
            self.peers.remove_by_socket(sock)
            sock.close()

    def _listen_connection(self, sock):
        try:
            while self.running:
                packet = self._recv_packet(sock)
                if not packet:
                    break
                self._process_packet(packet, sock, sock.getpeername())
        except Exception:
            pass
        finally:
            self.peers.remove_by_socket(sock)
            sock.close()

    def _process_packet(self, packet, sock, addr):
        try:
            ptype = packet.pkt_type

            if ptype == PacketType.HANDSHAKE_INIT:
                remote_id = packet.payload[:16]
                resp = Packet(PacketType.HANDSHAKE_RESPONSE, self.node_id)
                self._send_packet(sock, resp)
                self.peers.register(remote_id, sock, addr)
                print(f"✓ Peer connected: {remote_id.hex()[:8]} (total {self.peers.count()})")

            elif ptype == PacketType.HANDSHAKE_RESPONSE:
                remote_id = packet.payload[:16]
                self.peers.register(remote_id, sock, addr)
                print(f"✓ Peer connected: {remote_id.hex()[:8]} (total {self.peers.count()})")

            elif ptype == PacketType.MESSAGE:
                text, stats = self.messages.handle_incoming(packet.payload, sock)
                if text:
                    sender_id = self.peers.get_node_id(sock)
                    sender = sender_id.hex()[:8] if sender_id else "???"
                    print(f"\n┌─ Message from {sender}")
                    print(f"│  {text}")
                    print(
                        f"│  [Compression: {stats['original_bytes']}B → {stats['encoded_bytes']}B ({stats['compression_ratio']})]")
                    print(f"└─")
                    print("> ", end="", flush=True)

                    if sender_id:
                        self.dialogues.add_message(sender_id, text, packet.pack())

            elif ptype == PacketType.FILE_ANNOUNCE:
                info = self.files.handle_announce(packet.payload)
                if info:
                    print(f"← FILE: {info['name']} ({info['size']} bytes, {info['num_chunks']} chunks)")

            elif ptype == PacketType.FILE_CHUNK:
                result = self.files.handle_chunk(packet.payload)
                if result:
                    if result["complete"]:
                        print(f"✓ File saved: {result['file_path']}")

            elif ptype == PacketType.PING:
                pong = Packet(PacketType.PONG, b"")
                self._send_packet(sock, pong)

            elif ptype == PacketType.DISCONNECT:
                removed = self.peers.remove_by_socket(sock)
                if removed:
                    print(f"Peer disconnected: {removed.hex()[:8]}")

        except Exception as e:
            traceback.print_exc()

    # ====================== Публічні API ======================
    def send_message(self, text: str) -> bool:
        return self.messages.send(text)

    def send_file(self, filepath: str) -> bool:
        return self.files.send(filepath)

    def list_peers(self):
        return self.peers.list_peers()

    def get_stats(self):
        return {
            "unique_words": self.messages.llg.size,
            "total_words": self.messages.llg.next_id - 1
        }

    def get_llg_sample(self):
        items = list(self.messages.llg.word_to_id.items())[:10]
        return {word: wid for word, wid in items}

    def get_dialogue_hashes(self):
        return self.dialogues.get_stats()

    def _send_packet(self, sock, packet):
        data = packet.pack()
        sock.sendall(len(data).to_bytes(4, 'big') + data)

    def _recv_packet(self, sock):
        try:
            length_bytes = self._recv_exact(sock, 4)
            if not length_bytes:
                return None
            length = int.from_bytes(length_bytes, 'big')
            data = self._recv_exact(sock, length)
            return Packet.unpack(data) if data else None
        except Exception:
            return None

    def _recv_exact(self, sock, length):
        data = b""
        while len(data) < length:
            try:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            except socket.timeout:
                continue
            except Exception:
                return None
        return data