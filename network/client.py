import asyncio
from network.connection import Connection

class Client:
    def __init__(self):
        self.connection = None
        self._on_receive = None

    async def connect(self, host, port, on_receive=None):
        reader, writer = await asyncio.open_connection(host, port)
        self.connection = Connection(reader, writer, (host, port))
        self._on_receive = on_receive
        if on_receive:
            asyncio.create_task(self._read_loop())
        return self.connection

    async def _read_loop(self):
        try:
            while True:
                packet = await self.connection.recv()
                if self._on_receive:
                    self._on_receive(self.connection, packet)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        finally:
            self.connection.close()