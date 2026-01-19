import logging
import time
import evdev
from evdev import UInput, ecodes as e

logger = logging.getLogger(__name__)

class InputController:
    def __init__(self):
        self.ui = None
        self._setup_uinput()

    def _setup_uinput(self):
        """
        Sets up the uinput device.
        Requires user to be in 'input' group or root.
        """
        try:
            # Capabilities for a virtual mouse/keyboard
            cap = {
                e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
                e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
                e.EV_ABS: [e.ABS_X, e.ABS_Y], # For absolute positioning if needed
            }
            
            self.ui = UInput(cap, name="Llamiv-Input-Device")
            logger.info("UInput device initialized.")
        except PermissionError:
            logger.error("Permission denied creating UInput device. Ensure user is in 'input' group or run as root.")
        except Exception as e:
            logger.error(f"Failed to initialize UInput: {e}")

    def move_mouse(self, x: int, y: int):
        """
        Moves mouse to absolute coordinates.
        Note: Standard uinput/evdev often works in relative movements.
        For absolute movement, we might need a specific device configuration or use REL events calculated from current pos.
        However, usually on Wayland, uinput ABS events might not map 1:1 to screen pixels without compositor support.
        
        Alternative: We might rely on the frontend to tell us 'deltas' or we assume we can set ABS.
        Let's try ABS first, but typically mouse is REL.
        
        If ABS doesn't work, we might need to use a library like 'pynput' which wraps underlying X11/Wayland protocols,
        but pynput on Wayland has limitations.
        
        Actually, for Wayland, the best way for a BACKGROUND service to move mouse is uinput.
        But mapping 0-65535 ABS range to Screen Resolution is tricky.
        """
        # TODO: Implement robust absolute positioning. 
        # For now, we'll placeholder this. 
        # On Wayland, "warping" the mouse is restricted.
        # This is a risk point. 
        pass

    def click(self, button: str = "left"):
        if not self.ui:
            return
        
        btn_code = e.BTN_LEFT
        if button == "right":
            btn_code = e.BTN_RIGHT
        elif button == "middle":
            btn_code = e.BTN_MIDDLE

        self.ui.write(e.EV_KEY, btn_code, 1)
        self.ui.syn()
        time.sleep(0.05)
        self.ui.write(e.EV_KEY, btn_code, 0)
        self.ui.syn()

    def scroll(self, direction: str, amount: int = 1):
        if not self.ui:
            return
        
        # direction: 'up', 'down'
        # REL_WHEEL: positive is up, negative is down usually
        val = amount if direction == "up" else -amount
        self.ui.write(e.EV_REL, e.REL_WHEEL, val)
        self.ui.syn()

    def close(self):
        if self.ui:
            self.ui.close()

if __name__ == "__main__":
    # Test stub
    logging.basicConfig(level=logging.INFO)
    ctl = InputController()
    # ctl.scroll("down")
    ctl.close()
