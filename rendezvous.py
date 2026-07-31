import socket
import threading
import json
from protocol.packet import Packet, PacketType

class Rendezvous:
    def __init__(self, host="0.0.0.0", port=7000):
        self.host = host
        self.port = port
        self.registry = {}
        self.server_socket = None
        self.running = False

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        print(f"[Rendezvous] Listening on {self.host}:{self.port}")
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                print(f"[Rendezvous] Connection from {addr}")
                threading.Thread(target=self._handle_client, args=(client_sock, addr), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"[Rendezvous] Accept error: {e}")

    def _handle_client(self, sock, addr):
        try:
            while self.running:
                length_bytes = self._recv_exact(sock, 4)
                if not length_bytes:
                    break
                length = int.from_bytes(length_bytes, 'big')
                data = self._recv_exact(sock, length)
                if not data:
                    break
                packet = Packet.unpack(data)

                if packet.pkt_type == PacketType.MESSAGE:
                    payload = packet.payload.decode('utf-8')
                    request = json.loads(payload)
                    cmd = request.get("cmd")

                    if cmd == "register":
                        node_id = request["node_id"]
                        node_port = request["port"]
                        self.registry[node_id] = (addr[0], node_port)
                        print(f"[Rendezvous] Registered {node_id[:8]} at {addr[0]}:{node_port}")
                        resp = Packet(PacketType.MESSAGE, b"OK")
                        self._send_packet(sock, resp)

                    elif cmd == "lookup":
                        target_id = request["target_id"]
                        info = self.registry.get(target_id)
                        if info:
                            resp_data = json.dumps({"addr": info[0], "port": info[1]})
                            resp = Packet(PacketType.MESSAGE, resp_data.encode())
                            print(f"[Rendezvous] Found {target_id[:8]} at {info[0]}:{info[1]}")
                        else:
                            resp = Packet(PacketType.MESSAGE, b"NOT_FOUND")
                        self._send_packet(sock, resp)

                    elif cmd == "list":
                        resp_data = json.dumps(list(self.registry.keys()))
                        resp = Packet(PacketType.MESSAGE, resp_data.encode())
                        self._send_packet(sock, resp)

        except Exception as e:
            print(f"[Rendezvous] Client error: {e}")
        finally:
            sock.close()

    def _send_packet(self, sock, packet):
        data = packet.pack()
        length = len(data)
        sock.sendall(length.to_bytes(4, 'big') + data)

    def _recv_exact(self, sock, length):
        data = b""
        while len(data) < length:
            try:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            except Exception:
                return None
        return data

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    rendezvous = Rendezvous()
    try:
        rendezvous.start()
    except KeyboardInterrupt:
        rendezvous.stop()