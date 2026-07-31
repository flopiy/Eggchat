import struct
import asyncio
from protocol.packet import Packet, HEADER_SIZE

class Connection:
    def __init__(self, reader, writer, addr):
        self.reader = reader
        self.writer = writer
        self.addr = addr
        self.node_id = None  # 16-байтний ідентифікатор віддаленого вузла

    async def send(self, packet: Packet):
        data = packet.pack()
        # префікс: 4-байтова довжина пакета
        length = len(data)
        self.writer.write(struct.pack("!I", length) + data)
        await self.writer.drain()

    async def recv(self) -> Packet:
        # читаємо 4 байти довжини
        length_bytes = await self.reader.readexactly(4)
        length = struct.unpack("!I", length_bytes)[0]
        if length > 65535 + HEADER_SIZE:
            raise ValueError("Packet too large")
        # читаємо сам пакет
        data = await self.reader.readexactly(length)
        return Packet.unpack(data)

    def close(self):
        try:
            self.writer.close()
        except:
            pass