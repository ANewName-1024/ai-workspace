---
name: windows-gui
description: |
  Windows GUI Controller - Control Windows desktop remotely. 
  Activate when user wants to control Windows desktop, mouse, keyboard, screenshots, 
  open/close apps, manage windows, clipboard operations, or file transfer.
---

# Windows GUI Controller

Control Windows desktop remotely from AI Agent.

## Configuration

- **Windows IP**: 192.168.2.22
- **Port**: 8888
- **Base URL**: http://192.168.2.22:8888

## Tool Name

`windows_gui`

## Capabilities

### Mouse Control
- click, dblclick, rightclick
- move, drag
- scroll

### Keyboard Control  
- type, press, hotkey

### Screen
- screenshot, position, size, pixel

### File
- upload, download, list, delete, cleanup

### App
- open, close, running

### Clipboard
- read, write

### Window
- list, activate, minimize, maximize, close

### System
- health, version, capabilities, info, logs
- update/check, update/pull, update/restart

## Actions

### Health Check
```json
{ "action": "health" }
```

Returns: status, uptime, action_count, screen size, mouse position

### Version
```json
{ "action": "version" }
```

Returns: version, service name

### Capabilities
```json
{ "action": "capabilities" }
```

Returns: all available capabilities

### Screenshot
```json
{ "action": "screenshot" }
```

Returns: PNG image data

### Mouse Click
```json
{ "action": "click", "x": 100, "y": 200 }
{ "action": "click", "x": 100, "y": 200, "button": "right", "clicks": 2 }
```

### Mouse Move
```json
{ "action": "move", "x": 500, "y": 500 }
{ "action": "move", "x": 500, "y": 500, "duration": 0.5 }
```

### Mouse Drag
```json
{ "action": "drag", "x1": 0, "y1": 0, "x2": 100, "y2": 100 }
```

### Keyboard Type
```json
{ "action": "type", "text": "hello world" }
```

### Keyboard Press
```json
{ "action": "press", "key": "enter" }
{ "action": "press", "key": "ctrl,c" }
```

### Keyboard Hotkey
```json
{ "action": "hotkey", "keys": "ctrl,v" }
{ "action": "hotkey", "keys": "alt,tab" }
```

### Open App
```json
{ "action": "open", "app": "notepad" }
{ "action": "open", "app": "chrome" }
{ "action": "open", "app": "qq" }
```

Available apps: notepad, calc, explorer, cmd, powershell, chrome, edge, qq, wechat, dingtalk, vscode, sublime, idea, pycharm, wechatwork, tim, music, steam

### Close App
```json
{ "action": "close", "app": "notepad" }
```

### Clipboard Read
```json
{ "action": "clipboard_read" }
```

### Clipboard Write
```json
{ "action": "clipboard_write", "text": "hello" }
```

### Window List
```json
{ "action": "window_list" }
```

### Window Activate
```json
{ "action": "window_activate", "title": "notepad" }
```

### Window Close
```json
{ "action": "window_close", "title": "notepad" }
```

### System Info
```json
{ "action": "system_info" }
```

### Update Check
```json
{ "action": "update_check" }
```

### Update Pull and Restart
```json
{ "action": "update" }
```

## Notes

- Coordinates are screen pixels (0,0 is top-left)
- Default screen resolution is 2560x1440
- Files are automatically deleted after 5 minutes (configurable)
- Service runs on Windows, accessible from WSL/Linux via HTTP
