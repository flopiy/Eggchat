class PeerManager:
    def __init__(self):
        self.peers = {}              # node_id -> (socket, addr)
        self._socket_to_node_id = {} # socket -> node_id

    def register(self, node_id, sock, addr):
        if node_id in self.peers:
            old_sock, _ = self.peers[node_id]
            if old_sock != sock:
                self._socket_to_node_id.pop(old_sock, None)
        self.peers[node_id] = (sock, addr)
        self._socket_to_node_id[sock] = node_id

    def remove_by_socket(self, sock):
        node_id = self._socket_to_node_id.pop(sock, None)
        if node_id and node_id in self.peers:
            del self.peers[node_id]
        return node_id

    def get_node_id(self, sock):
        return self._socket_to_node_id.get(sock)

    def get_socket(self, node_id):
        entry = self.peers.get(node_id)
        return entry[0] if entry else None

    def get_addr(self, node_id):
        entry = self.peers.get(node_id)
        return entry[1] if entry else None

    def list_peers(self):
        return [(nid.hex()[:8], addr) for nid, (_, addr) in self.peers.items()]

    def count(self):
        return len(self.peers)

    def all_sockets(self):
        return [sock for sock, _ in self.peers.values()]

    def all_node_ids(self):
        return list(self.peers.keys())

    def clear(self):
        self.peers.clear()
        self._socket_to_node_id.clear()