import socket
import struct
import threading
import time

DISCOVERY_PORT = 9338
DISCOVERY_MULTICAST = "224.0.0.99"

class DiscoveryManager:
    def __init__(self, node_id, port, on_found_callback):
        self.node_id = node_id
        self.port = port
        self.on_found = on_found_callback  # callback(ip, port)
        self.sock = None
        self.running = False
        self.discovered = set()

    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.bind(("", DISCOVERY_PORT))
        except Exception:
            try:
                self.sock.bind(("0.0.0.0", DISCOVERY_PORT))
            except Exception:
                pass

        threading.Thread(target=self._listen, daemon=True).start()
        threading.Thread(target=self._announce_loop, daemon=True).start()
        threading.Thread(target=self._broadcast_query, daemon=True).start()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

    def _broadcast_query(self):
        time.sleep(2)
        query = self.node_id + self.port.to_bytes(4, 'big')
        targets = [("255.255.255.255", DISCOVERY_PORT), (DISCOVERY_MULTICAST, DISCOVERY_PORT)]
        for ip in self._get_local_ips():
            parts = ip.split('.')
            if len(parts) == 4:
                targets.append((f"{parts[0]}.{parts[1]}.{parts[2]}.255", DISCOVERY_PORT))
        for target in targets:
            try:
                self.sock.sendto(query, target)
            except Exception:
                pass

    def _listen(self):
        while self.running:
            try:
                self.sock.settimeout(1.0)
                try:
                    data, addr = self.sock.recvfrom(1024)
                except socket.timeout:
                    continue
                if len(data) < 20:
                    continue
                remote_id = data[:16]
                port = int.from_bytes(data[16:20], 'big')
                if remote_id == self.node_id:
                    continue
                if remote_id not in self.discovered:
                    self.discovered.add(remote_id)
                    self.on_found(addr[0], port)
                    response = self.node_id + self.port.to_bytes(4, 'big')
                    try:
                        self.sock.sendto(response, (addr[0], DISCOVERY_PORT))
                    except Exception:
                        pass
            except Exception:
                time.sleep(0.1)

    def _announce_loop(self):
        announcement = self.node_id + self.port.to_bytes(4, 'big')
        while self.running:
            try:
                self.sock.sendto(announcement, (DISCOVERY_MULTICAST, DISCOVERY_PORT))
                self.sock.sendto(announcement, ("255.255.255.255", DISCOVERY_PORT))
            except Exception:
                pass
            time.sleep(5)

    @staticmethod
    def _get_local_ips():
        ips = set()
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if not ip.startswith("127.") and ":" not in ip:
                    ips.add(ip)
        except Exception:
            pass
        return ips