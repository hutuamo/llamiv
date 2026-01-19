# 项目进展

## 2026-01-19: 初始版本实现完成

### 工作总结
1. **架构设计**: 
   - 设计了“GNOME Shell 扩展 + Python 后端服务”的混合架构。
   - 前端负责 UI 绘制和按键拦截，后端负责 AT-SPI2 扫描和输入模拟。
   - 确保了在 Wayland 安全模型下的可行性，避免了主线程阻塞。

2. **后端实现 (`service/`)**:
   - `scanner.py`: 基于 `pyatspi` 实现，用于递归查找窗口内的可点击 UI 元素（按钮、链接等）。
   - `input_controller.py`: 基于 `uinput` (`evdev`) 实现，用于模拟鼠标移动、点击和滚动事件。
   - `ipc.py`: 实现了 Unix Domain Socket 服务器，提供低延迟的跨进程通信。

3. **前端实现 (`extension/`)**:
   - `extension.js`: 采用现代 ES Module 标准（兼容 GNOME 46+）。
   - **UI 覆盖层**: 使用 `St` 和 `Clutter` 库，直接在合成器层绘制提示标签（A, B, C...）。
   - **交互模式**: 
     - **激活模式 (Hint Mode)**: 生成字母标签，输入对应字符即可点击。
     - **滚动模式 (Scroll Mode)**: 使用 HJKL 键进行页面滚动，ESC 退出。

4. **文档建设**:
   - `README.md`: 完成了详细的安装、配置和使用指南。
   - `docs/tech.md`: 记录了技术架构决策。
