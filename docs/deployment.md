# 部署注意事项

### 1. 权限要求
Python 后端服务需要访问内核级输入设备 (`/dev/uinput`) 以模拟鼠标操作。
- **操作**: 用户必须被添加到 `input` 用户组。
- **命令**: `sudo usermod -aG input $USER`
- **生效**: 修改组权限后，**必须注销并重新登录**（或重启系统）才能生效。

### 2. 系统依赖
目标宿主机需要安装以下基础依赖：
- `python3`
- `python3-gi` (PyGObject，用于 AT-SPI 通信)
- `python3-evdev` (用于 uinput 输入模拟)
- `libglib2.0-dev` (通常包含在发行版的基础库中)

### 3. GNOME 版本兼容性
- **目标环境**: Linux Kernel > 6.11, GNOME > 46 (Wayland)。
- **兼容性限制**: 扩展代码采用 ESM (ECMAScript Modules) 导入方式，仅兼容 GNOME 45 及以上版本。旧版 GNOME (Using `imports.gi`) 无法直接运行。

### 4. 调试建议
如果扩展无法正常工作，请按以下步骤排查：
1. **检查服务状态**: 确认 Python 进程是否启动。
   ```bash
   ps aux | grep llamiv
   ```
2. **查看日志**:
   - GNOME Shell 日志 (前端): `journalctl -f -o cat /usr/bin/gnome-shell`
   - Python 服务日志 (后端): `tail -f /tmp/llamiv_service.log`
3. **常见错误**:
   - `Permission denied`: 通常是因为用户不在 `input` 组，导致无法创建 uinput 设备。
   - `IPC Connection refused`: Python 服务未启动或崩溃。
