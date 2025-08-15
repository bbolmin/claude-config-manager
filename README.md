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

```
╔═══ 🤖 Claude Config Manager ═══╗
💡 Use ↑/↓ to navigate, →/Enter to select, ←/ESC to go back
════════════════════════════════════════════════════════════
1. Manage MCP Servers
2. Manage Projects  
3. Exit
```

```
📁 Config: /home/username/.claude.json
📂 Projects: /home/username/.claude/projects
╔═══ 📚 Projects Management (5 projects, 5 dirs) ═══╗
💡 PgUp/PgDn: page, ↑/↓: item, →/Enter: select, ←/ESC: back, d/D: delete
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
```

## License

MIT License