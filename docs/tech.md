# Implementation Plan: Keyboard Navigation for GNOME Wayland

## 1. Architecture Overview

To satisfy the requirements (Linux Kernel > 6.11, GNOME > 46, Wayland) and functionality (Activation & Scroll modes), a **Hybrid Architecture** is proposed. This decouples the heavy accessibility tree traversal from the GNOME Shell main thread to prevent UI freezes.

### Components

1.  **Frontend: GNOME Shell Extension (JavaScript/GJS)**
    *   **Responsibility**:
        *   Global shortcut management (Toggle modes).
        *   Input Capture: Grabbing keyboard input when "Active" or "Scroll" mode is on.
        *   Overlay Rendering: Drawing hint labels (A, B, AA, AB...) on top of the screen using Clutter/St.
        *   Communication: exchanging data with the backend service (DBus or Subprocess).
    *   **Tech**: GJS (GNOME JavaScript), Clutter, St.

2.  **Backend: Accessibility Service (Python)**
    *   **Responsibility**:
        *   **AT-SPI2 Scanning**: Traversing the application tree to find clickable elements (buttons, links, inputs).
        *   **Coordinate Mapping**: Extracting `(x, y, w, h)` for each element.
        *   **Input Simulation**: Executing mouse clicks and scroll events.
    *   **Tech**: `pyatspi2` (Accessibility), `libei` (Emulated Input) or `uinput` (Fallback).

---

## 2. Technical Decisions

### A. UI Element Discovery (AT-SPI2)
*   **Method**: Use `pyatspi` to query the registry.
*   **Filtering**: Recursively scan `Role.WINDOW` -> `Role.FRAME` -> children. Filter for "Clickable" state or specific roles (PUSH_BUTTON, MENU_ITEM, LINK, etc.).
*   **Performance**: Scanning the entire tree is slow. Optimization:
    *   Only scan the *active* window first (fastest response).
    *   Then scan visible windows.
    *   Cache the tree structure and listen for `object:children-changed` events (advanced).

### B. Overlay Rendering (Wayland)
*   **Challenge**: Wayland prevents global overlays from standard apps for security.
*   **Solution**: A **GNOME Shell Extension** runs *inside* the compositor space, allowing it to draw arbitrary content over any window.
*   Implementation: Create a `St.Widget` container added to `Main.layoutManager.uiGroup`.

### C. Input Simulation (Clicks & Scrolls)
*   **Primary Strategy (GNOME 46+)**: **libei** (Emulated Input).
    *   GNOME 46 supports the `libei` protocol for sandboxed input emulation.
    *   This is the future-proof Wayland native method.
*   **Alternative (Root/User Group)**: `/dev/uinput`.
    *   Requires the user to be in the `input` group or have udev rules set up.
    *   More reliable but requires setup.
*   **Fallback**: **RemoteDesktop Portal**.
    *   Requires user permission dialog on first run.

---

## 3. Step-by-Step Implementation

### Phase 1: Environment & Project Setup
1.  **Initialize Repository**: Git setup, directory structure (`extension/`, `service/`).
2.  **Docs**: Create `tech.md` (Architecture) and `todo.md` (Task tracking).

### Phase 2: The Backend Service (Python)
1.  **AT-SPI Prototyping**:
    *   Script to list all open windows.
    *   Script to recursively find clickable elements in the active window.
    *   Output coordinates to console to verify handling of HiDPI/Scaling.
2.  **Input Simulation**:
    *   Implement `click(x, y)` and `scroll(direction)` functions.
    *   Verify operation on Wayland (ensure cursor moves and clicks register).
3.  **IPC Server**:
    *   Set up a simple Unix Socket or DBus service to receive commands ("Scan", "Click", "Scroll").

### Phase 3: The Frontend (GNOME Extension)
1.  **Basic Skeleton**: Generate extension with `gnome-extensions create`.
2.  **Key Grabbing**:
    *   Implement global shortcut listener.
    *   Implement "Modal" mode where all keyboard input is intercepted (preventing typing in apps while hinting).
3.  **Overlay Logic**:
    *   Draw dummy labels on the screen (Clutter actors).
    *   Implement the "Hint Generation Algorithm" (e.g., recursive division or simple alpha-numeric sequence).

### Phase 4: Integration
1.  **Connect Frontend & Backend**:
    *   Extension spawns the Python service on load.
    *   On "Trigger", Extension asks Service for list of targets.
    *   Service returns JSON `[{label: "A", x: 100, y: 200}, ...]`.
    *   Extension draws labels.
2.  **Activation Mode**:
    *   User types "A". Extension highlights "A". User types "B". Extension tells Service "Click Element AB".
    *   Service moves mouse and clicks.
3.  **Scroll Mode**:
    *   Extension captures `h/j/k/l`.
    *   Sends "ScrollUp", "ScrollDown" commands to Service.

### Phase 5: Refinement
1.  **Multi-Monitor Support**: Ensure coordinates map correctly across displays.
2.  **Performance Tuning**: Limit AT-SPI scan depth or timeout.
3.  **Error Handling**: Handle cases where accessibility bus is busy.

---

## 4. Dependencies & Prerequisites

*   `python3-pyatspi`
*   `libglib2.0-dev` (for GObject Introspection)
*   `gnome-shell-extension-tool`
*   `python3-evdev` (if using uinput)
*   `libei` (optional, for native input)

