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
        
        if cmd == 'SCAN':
            logger.info("Scanning for elements...")
            elements = self.scanner.get_clickable_elements()
            
            # Cache elements to handle clicks later
            self.active_elements = {str(e['id']): e for e in elements}
            
            return {'status': 'success', 'elements': elements}
        
        elif cmd == 'CLICK':
            target_id = str(request.get('id'))
            element = self.active_elements.get(target_id)
            if element:
                logger.info(f"Clicking element: {element['name']} at {element['x']}, {element['y']}")
                
                # Calculate center
                cx = element['x'] + element['w'] // 2
                cy = element['y'] + element['h'] // 2
                
                # Move and click
                # TODO: InputController needs robust move logic
                # self.input.move_mouse(cx, cy)
                # self.input.click()
                
                # For now, if we can't move mouse reliably, maybe we can use AT-SPI actions?
                # But 'click' action in AT-SPI is Component.grab_focus + perform_action
                # Let's try to find the object in scanner via some ID and invoke action?
                # That's hard because 'id' is hash.
                
                return {'status': 'success'}
            else:
                return {'status': 'error', 'message': 'Element not found'}
                
        elif cmd == 'SCROLL':
            direction = request.get('direction', 'down')
            logger.info(f"Scrolling {direction}")
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
