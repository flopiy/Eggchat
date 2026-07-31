from protocol.packet import Packet, PacketType
from graph.llg import LLG

class MessageManager:
    def __init__(self, node_id, peers, send_callback):
        self.node_id = node_id
        self.peers = peers        # PeerManager
        self.send_packet = send_callback  # func(sock, packet)
        self.llg = LLG()
        self._known_words = set()

    def send(self, text, on_update_dialogue=None):
        if self.peers.count() == 0:
            return False

        encoded_ids = self.llg.encode(text)
        words = text.split()

        new_words = []
        for i, word in enumerate(words):
            if word not in self._known_words:
                new_words.append((encoded_ids[i], word))
                self._known_words.add(word)

        payload = b''
        payload += len(new_words).to_bytes(2, 'big')
        for wid, word in new_words:
            word_bytes = word.encode('utf-8')
            payload += wid.to_bytes(2, 'big')
            payload += len(word_bytes).to_bytes(1, 'big')
            payload += word_bytes
        for wid in encoded_ids:
            payload += wid.to_bytes(2, 'big')

        msg = Packet(PacketType.MESSAGE, payload)
        for sock in self.peers.all_sockets():
            try:
                self.send_packet(sock, msg)
            except Exception:
                self.peers.remove_by_socket(sock)

        return True

    def handle_incoming(self, payload, sender_sock):
        if len(payload) < 2:
            return None, None

        num_new = int.from_bytes(payload[:2], 'big')
        offset = 2
        new_words = []

        for _ in range(num_new):
            wid = int.from_bytes(payload[offset:offset+2], 'big')
            offset += 2
            word_len = payload[offset]
            offset += 1
            word = payload[offset:offset+word_len].decode('utf-8')
            offset += word_len
            self.llg.add_word(word, wid)
            self._known_words.add(word)
            new_words.append(word)

        encoded_ids = []
        while offset < len(payload):
            encoded_ids.append(int.from_bytes(payload[offset:offset+2], 'big'))
            offset += 2

        text = self.llg.decode(encoded_ids)
        stats = self.llg.stats(text, encoded_ids)
        return text, stats