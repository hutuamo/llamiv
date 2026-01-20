import socket
import os
import json
import logging
import struct
from typing import Callable, Any

logger = logging.getLogger(__name__)

RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
SOCKET_PATH = os.path.join(RUNTIME_DIR, "llamiv.sock")
MAX_MSG_SIZE = 1024 * 1024
SOCKET_TIMEOUT_SEC = 1.0

class IPCServer:
    def __init__(self, handler: Callable[[Any], Any]):
        self.handler = handler
        self.running = False
        self._setup_socket()

    def _setup_socket(self):
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.settimeout(SOCKET_TIMEOUT_SEC)
        old_umask = os.umask(0o177)
        try:
            self.server.bind(SOCKET_PATH)
        finally:
            os.umask(old_umask)
        self.server.listen(1)
        # Ensure accessible by the extension (running as same user)
        os.chmod(SOCKET_PATH, 0o600)

    def start(self):
        self.running = True
        logger.info(f"IPC Server listening on {SOCKET_PATH}")
        while self.running:
            try:
                conn, addr = self.server.accept()
                conn.settimeout(SOCKET_TIMEOUT_SEC)
                self._handle_connection(conn)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Socket accept error: {e}")

    def _handle_connection(self, conn):
        with conn:
            try:
                raw_len = self._recv_exact(conn, 4)
                if not raw_len:
                    return
                msg_len = struct.unpack('>I', raw_len)[0]
                if msg_len > MAX_MSG_SIZE:
                    raise ValueError(f"Message too large: {msg_len}")

                data = self._recv_exact(conn, msg_len)
                if not data:
                    return

                request = json.loads(data.decode('utf-8'))
                logger.debug(f"Received request: {request}")

                response = self.handler(request)
            except Exception as e:
                logger.error(f"Connection handling error: {e}")
                response = {"status": "error", "message": str(e)}

            try:
                resp_bytes = json.dumps(response).encode('utf-8')
                conn.sendall(struct.pack('>I', len(resp_bytes)) + resp_bytes)
            except Exception as e:
                logger.error(f"Response send error: {e}")

    def _recv_exact(self, conn, size: int) -> bytes:
        data = b''
        while len(data) < size:
            packet = conn.recv(size - len(data))
            if not packet:
                return b''
            data += packet
        return data

    def stop(self):
        self.running = False
        if self.server:
            try:
                self.server.close()
            except Exception as e:
                logger.error(f"Socket close error: {e}")
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
