import json

from protocol.packet import Packet


class PacketEncoder:

    @staticmethod
    def encode(packet: Packet) -> bytes:

        return (
            json.dumps(packet.to_dict())
            .encode("utf-8")
        )