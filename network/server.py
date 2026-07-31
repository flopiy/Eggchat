import asyncio
from network.connection import Connection

class Server:
    def __init__(self, host, port, on_receive=None):
        self.host = host
        self.port = port
        self.on_receive = on_receive
        self._server = None
        self._running = False

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"[Server] Connection from {addr}")
        conn = Connection(reader, writer, addr)
        if self.on_receive:
            asyncio.create_task(self._read_loop(conn))

    async def _read_loop(self, conn):
        try:
            while self._running:
                packet = await conn.recv()
                if self.on_receive:
                    self.on_receive(conn, packet)
        except (asyncio.IncompleteReadError, ConnectionResetError, ValueError):
            pass
        finally:
            conn.close()

    async def start(self):
        self._running = True
        self._server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"[Server] Listening on {self.host}:{self.port}")
        await self._server.serve_forever()

    def stop(self):
        self._running = False
        if self._server:
            self._server.close()