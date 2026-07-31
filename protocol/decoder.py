import json

from protocol.packet import Packet
from protocol.packet_types import PacketType


class PacketDecoder:

    @staticmethod
    def decode(data: bytes) -> Packet:

        raw = json.loads(data.decode())

        return Packet(
            packet_type=PacketType(raw["type"]),
            sender=raw["sender"],
            receiver=raw.get("receiver"),
            payload=raw.get("payload", {}),
            packet_id=raw["packet_id"],
            timestamp=raw["timestamp"]
        )