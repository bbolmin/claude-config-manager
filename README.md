# Claude Config Manager (CCM)

A terminal-based interactive tool for managing Claude Desktop's configuration file (`~/.claude.json`) and associated project directories.

## Features

### 🖥️ MCP Server Management
- View and delete MCP servers
- Display server installation commands

### 📚 Project Management  
- View projects with conversation history
- Delete projects (including `.claude/projects` directories)

## Usage

```bash
# Run with default config file (~/.claude.json)
./ccm.py

# Run with custom config file
./ccm.py /path/to/your/claude.json
```

## File Structure

```
~/.claude.json          # Claude Desktop configuration
~/.claude/projects/     # Project-specific directories
    ├── -mnt-c-Users-username-project1
    ├── -mnt-c-Users-username-project2
    └── ...
```

## Screenshots

### Main Menu
```
📁 Config: /home/username/.claude.json
╔═══ 🤖 Claude Config Manager ═══╗
💡 Use ↑/↓ to navigate, →/Enter to select, ←/ESC to go back
════════════════════════════════════════════════════════════
1. Manage MCP Servers
2. Manage Projects  
3. Exit
```

### Projects Management
```
📁 Config: /home/username/.claude.json
📂 Projects: /home/username/.claude/projects
╔═══ 📚 Projects Management (5 projects, 5 dirs) ═══╗
💡 PgUp/PgDn: page, ↑/↓: item, →/Enter: select, ← back, d/D: delete
════════════════════════════════════════════════════════════
  📂 Project: my-python-app
  💬 History: 23 messages
  🕐 Generated: 2024-08-15 14:30:00
  📍 Path: /home/user/projects/my-python-app
  ────────────────────────
  📂 Project: web-dashboard
  💬 History: 15 messages
  🕐 Generated: 2024-08-14 10:15:00
  📍 Path: /home/user/projects/web-dashboard
════════════════════════════════════════════════════════════
🗑️  [ DELETE ALL PROJECTS ]
◀️  [ Back to Main Menu ]
                                          [2/5]  Page 1/1
```

### Conversation History View
```
📂 Project: my-python-app
📍 Path: /home/user/projects/my-python-app
💬 Total conversations: 23
════════════════════════════════════════════════════════════
💡 PgUp/PgDn: page, ↑/↓: item, ← to go back
════════════════════════════════════════════════════════════
  1. What is the capital of France?
  2. Help me write a Python function to calculate factorial
  3. [Pasted text] | def factorial(n): if n == 0: return 1 else: return n * factorial(n-1)...
  4. Can you explain how recursion works?
  5. Create a simple web server using Flask
  6. How do I handle errors in Python?
  7. What's the difference between list and tuple?
  8. [Pasted text] | import pandas as pd import numpy as np data = pd.DataFrame({...
  9. Explain async/await in Python
 10. Help me optimize this database query
                                          ▼ MORE
                                          [1/23]  Page 1/3
```

## License

MIT License