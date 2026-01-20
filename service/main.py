import logging
import sys
import threading
from scanner import AtspiScanner
from input_controller import InputController
from ipc import IPCServer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/llamiv_service.log")
    ]
)

logger = logging.getLogger("LlamivService")

class ServiceApp:
    def __init__(self):
        self.scanner = AtspiScanner()
        self.input = InputController()
        self.ipc = IPCServer(self.handle_request)
        # Store for active elements to map ID back to object/coords
        self.active_elements = {} 

    def handle_request(self, request):
        cmd = request.get('command')
        params = request.get('params') or {}

        if cmd == 'SCAN':
            logger.info("Scanning for elements...")
            elements = self.scanner.get_clickable_elements()

            # Cache elements to handle clicks later
            self.active_elements = {str(e['id']): e for e in elements}

            return {'status': 'success', 'elements': elements}

        elif cmd == 'CLICK':
            target_id = str(params.get('id'))
            element = self.active_elements.get(target_id)
            if element:
                logger.info(f"Clicking element: {element['name']} at {element['x']}, {element['y']}")

                obj = self.scanner.get_object_by_id(target_id)
                if obj and self.scanner.perform_action_click(obj):
                    return {'status': 'success'}

                return {'status': 'error', 'message': 'Click action unavailable'}
            return {'status': 'error', 'message': 'Element not found'}

        elif cmd == 'SCROLL':
            direction = params.get('direction', 'down')
            logger.info(f"Scrolling {direction}")
            if not self.input.is_available():
                return {'status': 'error', 'message': 'Input device unavailable'}
            self.input.scroll(direction)
            return {'status': 'success'}

        elif cmd == 'PING':
            return {'status': 'pong'}

        return {'status': 'error', 'message': 'Unknown command'}

    def run(self):
        logger.info("Starting Llamiv Service...")
        try:
            self.ipc.start()
        except KeyboardInterrupt:
            logger.info("Stopping...")
            self.ipc.stop()

if __name__ == "__main__":
    app = ServiceApp()
    app.run()
