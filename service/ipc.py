import socket
import os
import json
import logging
import struct
from typing import Callable, Any

logger = logging.getLogger(__name__)

SOCKET_PATH = "/tmp/llamiv.sock"

class IPCServer:
    def __init__(self, handler: Callable[[Any], Any]):
        self.handler = handler
        self.running = False
        self._setup_socket()

    def _setup_socket(self):
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(SOCKET_PATH)
        self.server.listen(1)
        # Ensure accessible by the extension (running as same user)
        os.chmod(SOCKET_PATH, 0o600) 

    def start(self):
        self.running = True
        logger.info(f"IPC Server listening on {SOCKET_PATH}")
        while self.running:
            try:
                conn, addr = self.server.accept()
                self._handle_connection(conn)
            except Exception as e:
                logger.error(f"Socket accept error: {e}")

    def _handle_connection(self, conn):
        with conn:
            try:
                # Read message length (4 bytes big endian)
                raw_len = conn.recv(4)
                if not raw_len:
                    return
                msg_len = struct.unpack('>I', raw_len)[0]
                
                # Read payload
                data = b''
                while len(data) < msg_len:
                    packet = conn.recv(msg_len - len(data))
                    if not packet:
                        break
                    data += packet
                
                # Process
                request = json.loads(data.decode('utf-8'))
                logger.debug(f"Received request: {request}")
                
                response = self.handler(request)
                
                # Send response
                resp_bytes = json.dumps(response).encode('utf-8')
                conn.sendall(struct.pack('>I', len(resp_bytes)) + resp_bytes)
                
            except Exception as e:
                logger.error(f"Connection handling error: {e}")

    def stop(self):
        self.running = False
        if self.server:
            self.server.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
