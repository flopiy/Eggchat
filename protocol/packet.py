import struct
import time
from enum import IntEnum

class PacketType(IntEnum):
    HANDSHAKE_INIT = 0x01
    HANDSHAKE_RESPONSE = 0x02
    HANDSHAKE_FINAL = 0x03
    MESSAGE = 0x10
    MESSAGE_ACK = 0x11
    FILE_ANNOUNCE = 0x20
    FILE_CHUNK = 0x21
    FILE_REQUEST = 0x22
    FILE_ACK = 0x23
    PING = 0x30
    PONG = 0x31
    FIND_NODE = 0x40
    FOUND_NODE = 0x41
    DISCONNECT = 0xFF

HEADER_FORMAT = "!BBH Q I"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_PAYLOAD = 65535

class Packet:
    def __init__(self, pkt_type, payload=b"", flags=0, sequence=None):
        self.version = 1
        self.pkt_type = pkt_type
        self.flags = flags
        self.sequence = sequence if sequence is not None else int(time.time() * 1_000_000)
        self.payload = payload
        self.payload_size = len(payload)

    def pack(self) -> bytes:
        header = struct.pack(HEADER_FORMAT,
                             self.version,
                             int(self.pkt_type),
                             self.flags,
                             self.sequence,
                             self.payload_size)
        return header + self.payload

    @classmethod
    def unpack(cls, data: bytes) -> "Packet":
        if len(data) < HEADER_SIZE:
            raise ValueError("Packet too short")
        header = data[:HEADER_SIZE]
        version, pkt_type, flags, sequence, payload_size = struct.unpack(HEADER_FORMAT, header)
        if payload_size > MAX_PAYLOAD or len(data) < HEADER_SIZE + payload_size:
            raise ValueError("Invalid payload size")
        payload = data[HEADER_SIZE:HEADER_SIZE + payload_size]
        packet = cls(PacketType(pkt_type), payload, flags, sequence)
        packet.version = version
        return packet

    def __repr__(self):
        return f"<Packet type={PacketType(self.pkt_type).name} seq={self.sequence} size={self.payload_size}>"