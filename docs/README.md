# Llamiv

Keyboard navigation for GNOME Wayland. Use your keyboard to click elements and scroll, similar to Vimium or Vimac.

## Requirements

- **OS**: Linux
- **Desktop Environment**: GNOME > 46 (Wayland)
- **Dependencies**:
  - `python3`
  - `python3-gi` (PyGObject)
  - `python3-evdev`
  - `libglib2.0-dev`

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your/llamiv.git
    cd llamiv
    ```

2.  **Install Python Dependencies**:
    ```bash
    pip3 install evdev
    # OR use your package manager (recommended)
    # sudo apt install python3-evdev python3-gi
    ```

3.  **Install the Extension**:
    Copy the `extension` folder to your GNOME extensions directory.
    ```bash
    mkdir -p ~/.local/share/gnome-shell/extensions/llamiv@xhl.studio
    cp -r extension/* ~/.local/share/gnome-shell/extensions/llamiv@xhl.studio/
    cp -r service ~/.local/share/gnome-shell/extensions/llamiv@xhl.studio/
    ```
    *Note: The `service` folder must be copied *inside* the extension folder so the extension can find it.*

4.  **Setup Permissions (Important)**:
    The Python backend needs permission to create virtual input devices (`uinput`).
    
    Add your user to the `input` group:
    ```bash
    sudo usermod -aG input $USER
    ```
    **You must restart your session (logout/login) for this to take effect.**

5.  **Enable the Extension**:
    ```bash
    gnome-extensions enable llamiv@xhl.studio
    ```
    Or use the "Extensions" app.

## Usage

- **Activate Mode** (`<Super>f`):
  - Shows hints (A, B, C...) on all clickable elements in the active window.
  - Type the hint to click.
  - Press `Esc` to cancel.

- **Scroll Mode** (`<Super>j`):
  - Enters Scroll Mode.
  - Use `j` (Down) and `k` (Up) to scroll.
  - Press `Esc` to exit.

## Troubleshooting

- Check logs:
  ```bash
  journalctl -f -o cat /usr/bin/gnome-shell
  tail -f /tmp/llamiv_service.log
  ```
- If hints don't appear, check if `main.py` is running and has permissions.
