import logging
import time
from typing import List, Dict, Any, Optional
import gi

gi.require_version('Atspi', '2.0')
from gi.repository import Atspi, GLib

logger = logging.getLogger(__name__)

# Constants for roles that are typically clickable
CLICKABLE_ROLES = {
    Atspi.Role.PUSH_BUTTON,
    Atspi.Role.TOGGLE_BUTTON,
    Atspi.Role.CHECK_BOX,
    Atspi.Role.RADIO_BUTTON,
    Atspi.Role.MENU_ITEM,
    Atspi.Role.CHECK_MENU_ITEM,
    Atspi.Role.RADIO_MENU_ITEM,
    Atspi.Role.LINK,
    Atspi.Role.PAGE_TAB,
    Atspi.Role.COMBO_BOX,
    Atspi.Role.LIST_ITEM,
    Atspi.Role.ENTRY,  # Entries are focusable/clickable
}

class AtspiScanner:
    def __init__(self):
        self.root = None
        self._active_object_map = {}
        try:
            Atspi.init()
            self.root = Atspi.get_desktop(0)
            logger.info("AT-SPI initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize AT-SPI: {e}")

    def get_clickable_elements(self) -> List[Dict[str, Any]]:
        """
        Scans the active window for clickable elements.
        Returns a list of dicts: {'id': str, 'x': int, 'y': int, 'w': int, 'h': int, 'name': str}
        """
        elements = []
        self._active_object_map = {}
        if not self.root:
            logger.error("AT-SPI root not initialized.")
            return []

        # Strategy: Find the active window first to optimize performance
        # Scanning the entire desktop is too slow.
        active_window = self._find_active_window()
        if not active_window:
            logger.warning("No active window found.")
            # Fallback: Scan all applications (could be slow)
            return self._scan_desktop_fallback()

        logger.info(f"Scanning active window: {active_window.get_name()}")
        self._scan_recursive(active_window, elements)
        return elements

    def _find_active_window(self) -> Optional[Atspi.Accessible]:
        """Finds the currently active window on the desktop."""
        count = self.root.get_child_count()
        for i in range(count):
            app = self.root.get_child_at_index(i)
            if not app:
                continue
            
            # Check application children for 'active' state window
            # Note: Applications might have multiple windows.
            # We look for a window with STATE_ACTIVE or STATE_FOCUSED
            app_child_count = app.get_child_count()
            for j in range(app_child_count):
                window = app.get_child_at_index(j)
                if not window:
                    continue
                
                try:
                    states = window.get_state_set().get_states()
                    if Atspi.StateType.ACTIVE in states or Atspi.StateType.FOCUSED in states:
                        return window
                except Exception:
                    continue
        return None

    def _scan_desktop_fallback(self) -> List[Dict[str, Any]]:
        elements = []
        count = self.root.get_child_count()
        for i in range(count):
            app = self.root.get_child_at_index(i)
            self._scan_recursive(app, elements, depth_limit=10)
        return elements

    def _scan_recursive(self, obj: Atspi.Accessible, results: List[Dict[str, Any]], depth=0, depth_limit=50):
        if depth > depth_limit:
            return

        try:
            # Check if object is null or dead
            if obj is None:
                return
                
            states = obj.get_state_set().get_states()
            
            # Skip invisible elements
            if Atspi.StateType.VISIBLE not in states and Atspi.StateType.SHOWING not in states:
                # Sometimes containers are not "showing" but have showing children?
                # Usually if a parent is not showing, children aren't either.
                return

            role = obj.get_role()

            # Check if clickable
            if role in CLICKABLE_ROLES:
                self._add_element_if_valid(obj, results)
            
            # Recurse into children
            # Optimization: Don't recurse into some complex widgets if they are leaf-like?
            # But a ComboBox has children (menu items) we might want.
            
            child_count = obj.get_child_count()
            if child_count > 0:
                for i in range(child_count):
                    child = obj.get_child_at_index(i)
                    self._scan_recursive(child, results, depth + 1, depth_limit)

        except Exception as e:
            logger.debug(f"Error traversing object: {e}")

    def _add_element_if_valid(self, obj: Atspi.Accessible, results: List[Dict[str, Any]]):
        try:
            component = obj.get_component_iface()
            if not component:
                return

            # Get screen coordinates
            # DESKTOP_COORDS = 0
            x, y, w, h = component.get_extents(Atspi.CoordType.SCREEN)
            
            # Filter invalid coordinates
            if w <= 0 or h <= 0:
                return

            obj_id = str(hash(obj))
            self._active_object_map[obj_id] = obj

            results.append({
                'name': obj.get_name(),
                'role': obj.get_role_name(),
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                # Use a path or unique ID if possible, but Atspi paths are complex.
                # We might need to store the raw object in a temporary map if we want to invoke actions on it later.
                # For JSON serialization, we just send coords.
                'id': obj_id
            })
        except Exception as e:
            logger.debug(f"Error extracting element bounds: {e}")

    def get_object_by_id(self, obj_id: str) -> Optional[Atspi.Accessible]:
        return self._active_object_map.get(obj_id)

    def perform_action_click(self, obj: Atspi.Accessible) -> bool:
        try:
            action = obj.get_action_iface()
            if not action:
                return False
            if action.get_n_actions() < 1:
                return False
            return action.do_action(0)
        except Exception as e:
            logger.debug(f"Action click failed: {e}")
            return False

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    scanner = AtspiScanner()
    start = time.time()
    elems = scanner.get_clickable_elements()
    duration = time.time() - start
    print(f"Found {len(elems)} elements in {duration:.4f}s")
    for e in elems[:5]:
        print(e)
