# Project Todo

- [x] **Phase 1: Setup**
    - [x] Initialize Git repository
    - [x] Create folder structure (`extension/`, `service/`)
    - [x] Create `README.md` and `docs/`

- [x] **Phase 2: Backend Service (Python)**
    - [x] Implement AT-SPI2 tree traversal (Service)
    - [x] Implement Coordinate Extraction logic
    - [x] Implement Input Simulation (libei/uinput)
    - [x] Set up IPC (Socket/DBus) server

- [x] **Phase 3: GNOME Shell Extension**
    - [x] Scaffold extension
    - [x] Implement IPC Client (communicate with Python backend)
    - [x] Implement Overlay UI (Clutter/St)
    - [x] Implement Keyboard Grabber (Global Shortcuts)

- [x] **Phase 4: Logic Implementation**
    - [x] **Activation Mode**:
        - [x] Generate hints for clickable elements
        - [x] Handle character filtering
        - [x] Trigger click on match
    - [x] **Scroll Mode**:
        - [x] Map HJKL to scroll events
        - [x] Visual feedback for scroll mode

- [ ] **Phase 5: Packaging & Polish**
    - [ ] Create installation script (optional, README provided)
    - [ ] Add configuration settings (colors, keys) - *Basic schema added*
    - [ ] Testing on GNOME 46+ (Wayland)
