#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import curses
from pathlib import Path


class ClaudeConfigManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Use ~/.claude.json by default
            self.config_path = os.path.expanduser("~/.claude.json")
        else:
            self.config_path = config_path
        
        # Get absolute path
        self.config_path = os.path.abspath(self.config_path)
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.config_path} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            sys.exit(1)
    
    def save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_mcp_servers(self) -> Dict:
        """Get MCP servers from config"""
        return self.config.get('mcpServers', {})
    
    def get_projects(self) -> Dict:
        """Get projects from config"""
        return self.config.get('projects', {})
    
    def delete_mcp_server(self, server_name: str):
        """Delete a specific MCP server"""
        if 'mcpServers' in self.config and server_name in self.config['mcpServers']:
            del self.config['mcpServers'][server_name]
            self.save_config()
            return True
        return False
    
    def delete_all_mcp_servers(self):
        """Delete all MCP servers"""
        if 'mcpServers' in self.config:
            self.config['mcpServers'] = {}
            self.save_config()
            return True
        return False
    
    def delete_project(self, project_path: str):
        """Delete a specific project"""
        if 'projects' in self.config and project_path in self.config['projects']:
            del self.config['projects'][project_path]
            self.save_config()
            
            # Delete corresponding .claude/projects directory
            # Convert path to match Claude's naming convention
            import re
            sanitized_path = re.sub(r'[^a-zA-Z0-9]', '-', project_path)
            # Also try with just slash replacement (both patterns observed)
            alt_sanitized_path = project_path.replace('/', '-')
            
            claude_project_dirs = [
                os.path.expanduser(f"~/.claude/projects/{sanitized_path}"),
                os.path.expanduser(f"~/.claude/projects/{alt_sanitized_path}"),
                os.path.expanduser(f"~/.claude/projects{alt_sanitized_path}")  # Without slash
            ]
            
            import shutil
            for claude_project_dir in claude_project_dirs:
                if os.path.exists(claude_project_dir):
                    try:
                        shutil.rmtree(claude_project_dir)
                    except Exception:
                        pass  # Silently ignore errors
            
            return True
        return False
    
    def delete_all_projects(self):
        """Delete all projects"""
        if 'projects' in self.config:
            self.config['projects'] = {}
            self.save_config()
            
            # Delete entire .claude/projects directory and recreate it empty
            import shutil
            claude_projects_dir = os.path.expanduser("~/.claude/projects")
            if os.path.exists(claude_projects_dir):
                try:
                    # Remove the entire directory
                    shutil.rmtree(claude_projects_dir)
                    # Recreate empty directory
                    os.makedirs(claude_projects_dir, exist_ok=True)
                except Exception:
                    pass  # Silently ignore errors
            
            return True
        return False
    


class InteractiveMenu:
    def __init__(self, config_manager: ClaudeConfigManager):
        self.config_manager = config_manager
        self.current_menu = "main"
        
    def format_timestamp(self, timestamp: int) -> str:
        """Convert timestamp to Korean time string"""
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)  # Convert from milliseconds
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "N/A"
    
    def show_confirmation(self, stdscr, title: str, message: str, warning: str = "") -> bool:
        """Show confirmation dialog with y/N prompt"""
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            
            # Calculate center position
            start_y = h // 2 - 5
            
            # Draw confirmation box
            stdscr.addstr(start_y, 0, "═" * min(w-1, 60))
            stdscr.addstr(start_y + 1, 0, title, curses.A_BOLD)
            stdscr.addstr(start_y + 2, 0, "═" * min(w-1, 60))
            
            # Show message
            stdscr.addstr(start_y + 4, 0, message)
            if warning:
                stdscr.addstr(start_y + 5, 0, warning, curses.A_BOLD | curses.A_REVERSE)
            
            # Show prompt
            prompt_y = start_y + 7 if warning else start_y + 6
            stdscr.addstr(prompt_y, 0, "Are you sure? (y/N): ")
            stdscr.addstr(prompt_y + 1, 0, "💡 Press ← to cancel", curses.A_DIM)
            
            stdscr.refresh()
            
            # Get user input
            key = stdscr.getch()
            
            if key == ord('y') or key == ord('Y'):
                return True
            elif key == ord('n') or key == ord('N') or key == curses.KEY_LEFT or key == ord('\n'):  # N, Left arrow, or Enter (default is No)
                return False
    
    def show_project_history(self, stdscr, project_path: str, project_data: Dict):
        """Show conversation history for a project"""
        history = project_data.get('history', [])
        project_name = os.path.basename(project_path) or project_path
        selected_idx = 0
        scroll_offset = 0
        
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            
            # Draw header
            stdscr.addstr(0, 0, f"📂 Project: {project_name}", curses.A_BOLD)
            stdscr.addstr(1, 0, f"📍 Path: {project_path[:w-10]}")
            stdscr.addstr(2, 0, f"💬 Total conversations: {len(history)}")
            stdscr.addstr(3, 0, "═" * min(w-1, 60))
            stdscr.addstr(4, 0, "💡 PgUp/PgDn: page, ↑/↓: item, ← to go back")
            stdscr.addstr(5, 0, "═" * min(w-1, 60))
            
            # Display history items
            start_y = 7
            visible_height = h - start_y - 2
            
            if not history:
                stdscr.addstr(start_y, 0, "No conversation history")
            else:
                # Calculate scroll position
                if selected_idx >= scroll_offset + visible_height:
                    scroll_offset = selected_idx - visible_height + 1
                elif selected_idx < scroll_offset:
                    scroll_offset = selected_idx
                
                # Display visible items
                for i in range(scroll_offset, min(scroll_offset + visible_height, len(history))):
                    if start_y + (i - scroll_offset) >= h - 2:
                        break
                    
                    is_selected = i == selected_idx
                    if is_selected:
                        stdscr.attron(curses.A_REVERSE)
                    
                    hist_item = history[i]
                    display_text = hist_item.get('display', 'No display text')
                    
                    # Check if this is a pasted text item
                    pasted_preview = ""
                    if "[Pasted text" in display_text:
                        pasted_contents = hist_item.get('pastedContents', {})
                        if pasted_contents:
                            # Get first pasted content preview
                            for key, value in pasted_contents.items():
                                if value:
                                    # Get first 80 chars of pasted content
                                    preview = str(value).replace('\n', ' ').strip()
                                    if len(preview) > 80:
                                        preview = preview[:77] + "..."
                                    pasted_preview = f" | {preview}"
                                    break
                    
                    # Truncate display text if needed
                    max_display_len = w - 10 - len(pasted_preview)
                    if len(display_text) > max_display_len:
                        display_text = display_text[:max_display_len-3] + "..."
                    
                    # Build line text
                    line_text = f"{i+1:3}. {display_text}"
                    
                    # Draw main text
                    try:
                        y_pos = start_y + (i - scroll_offset)
                        stdscr.addstr(y_pos, 0, line_text[:w-2])
                        
                        # Draw pasted preview in gray (DIM)
                        if pasted_preview:
                            x_pos = len(line_text)
                            if x_pos + len(pasted_preview) < w - 2:
                                stdscr.addstr(y_pos, x_pos, pasted_preview, curses.A_DIM)
                    except curses.error:
                        pass
                    
                    if is_selected:
                        stdscr.attroff(curses.A_REVERSE)
                
                # Show position and page indicators
                if history:
                    total_pages = max(1, (len(history) + visible_height - 1) // visible_height)
                    current_page = (selected_idx // visible_height) + 1
                    position_text = f"[{selected_idx + 1}/{len(history)}]  Page {current_page}/{total_pages}"
                    try:
                        stdscr.addstr(h - 1, w - len(position_text) - 2, position_text, curses.A_DIM)
                    except curses.error:
                        pass
                
                # Show scroll indicators
                if scroll_offset > 0:
                    try:
                        stdscr.addstr(start_y - 1, w - 10, "▲ MORE", curses.A_DIM)
                    except curses.error:
                        pass
                if scroll_offset + visible_height < len(history):
                    try:
                        stdscr.addstr(h - 2, w - 10, "▼ MORE", curses.A_DIM)
                    except curses.error:
                        pass
            
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            
            if key == curses.KEY_UP:
                if history:
                    if selected_idx == 0:
                        selected_idx = len(history) - 1
                    else:
                        selected_idx -= 1
            elif key == curses.KEY_DOWN:
                if history:
                    if selected_idx == len(history) - 1:
                        selected_idx = 0
                    else:
                        selected_idx += 1
            elif key == curses.KEY_PPAGE:  # Page Up
                if history:
                    selected_idx = max(0, selected_idx - visible_height)
            elif key == curses.KEY_NPAGE:  # Page Down  
                if history:
                    selected_idx = min(len(history) - 1, selected_idx + visible_height)
            elif key == curses.KEY_LEFT:  # Left arrow only
                break
    
    def draw_menu_with_fixed_bottom(self, stdscr, title: str, data_items: List, fixed_items: List, selected_idx: int, multi_line: bool = False, scroll_offset: int = 0, show_projects_dir: bool = False):
        """Draw menu with scrollable data and fixed bottom options"""
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Draw config file path
        config_path_text = f"📁 Config: {self.config_manager.config_path}"
        stdscr.addstr(0, 0, config_path_text[:w-1], curses.A_DIM)
        
        # Draw projects directory path if requested
        header_offset = 1
        if show_projects_dir:
            projects_dir_text = f"📂 Projects: {os.path.expanduser('~/.claude/projects')}"
            stdscr.addstr(1, 0, projects_dir_text[:w-1], curses.A_DIM)
            header_offset = 2
        
        # Draw title (without position indicator)
        stdscr.addstr(header_offset, 0, f"╔═══ {title} ═══╗", curses.A_BOLD)
        stdscr.addstr(header_offset + 1, 0, "💡 PgUp/PgDn: page, ↑/↓: item, →/Enter: select, ← back, d/D: delete")
        stdscr.addstr(header_offset + 2, 0, "═" * min(w-1, 60))
        
        # Calculate areas
        header_height = 5 if not show_projects_dir else 6
        fixed_items_height = len(fixed_items) + 2  # +2 for separator and spacing
        scrollable_height = h - header_height - fixed_items_height
        
        # Combine all items for selection
        all_items = data_items + fixed_items
        
        # Draw scrollable data items
        if data_items:
            scroll_offset = self._draw_scrollable_items(stdscr, data_items, selected_idx, scroll_offset, 
                                       header_height, scrollable_height, w, multi_line)
        
        # Draw separator before fixed items
        separator_y = h - fixed_items_height
        try:
            stdscr.addstr(separator_y, 0, "═" * min(w-1, 60), curses.A_DIM)
        except curses.error:
            pass
        
        # Draw fixed bottom items
        fixed_start_y = separator_y + 1
        for idx, item in enumerate(fixed_items):
            item_idx = len(data_items) + idx
            is_selected = selected_idx == item_idx
            
            if is_selected:
                stdscr.attron(curses.A_REVERSE)
            
            try:
                stdscr.addstr(fixed_start_y + idx, 0, str(item)[:w-2])
            except curses.error:
                pass
            
            if is_selected:
                stdscr.attroff(curses.A_REVERSE)
        
        # Calculate pages for data items
        items_per_page = 5  # Adjust this based on your multi-line item height
        if multi_line and data_items:
            # For multi-line items, estimate items per page
            avg_item_height = 5  # Average height of multi-line item
            items_per_page = max(1, scrollable_height // avg_item_height)
        
        total_pages = max(1, (len(data_items) + items_per_page - 1) // items_per_page) if data_items else 1
        current_page = (selected_idx // items_per_page) + 1 if selected_idx < len(data_items) else 0
        
        # Draw position and page indicators at bottom right
        if selected_idx < len(data_items) and data_items:
            position_text = f"[{selected_idx + 1}/{len(data_items)}]  Page {current_page}/{total_pages}"
            try:
                stdscr.addstr(h - 1, w - len(position_text) - 2, position_text, curses.A_DIM)
            except curses.error:
                pass
        
        stdscr.refresh()
        return scroll_offset
    
    def _draw_scrollable_items(self, stdscr, items, selected_idx, scroll_offset, start_y, max_height, w, multi_line):
        """Helper to draw scrollable items"""
        h, _ = stdscr.getmaxyx()
        
        # Calculate item heights
        item_heights = []
        for item in items:
            if multi_line and isinstance(item, dict):
                item_heights.append(len(item) + 1)  # +1 for separator
            else:
                item_heights.append(1)
        
        # Adjust scroll to keep selected item visible
        if selected_idx < len(items):
            selected_top = sum(item_heights[:selected_idx])
            selected_bottom = selected_top + item_heights[selected_idx]
            
            # Only scroll if selected item is outside visible area
            if selected_bottom > scroll_offset + max_height:
                # Item is below visible area, scroll down
                scroll_offset = selected_bottom - max_height
            elif selected_top < scroll_offset:
                # Item is above visible area, scroll up
                scroll_offset = selected_top
        
        # Draw items
        current_y = start_y
        current_line = 0
        
        for idx, item in enumerate(items):
            if current_y >= start_y + max_height:
                break
            
            item_height = item_heights[idx]
            
            # Skip items above scroll
            if current_line + item_height <= scroll_offset:
                current_line += item_height
                continue
            
            is_selected = idx == selected_idx
            
            if multi_line and isinstance(item, dict):
                if is_selected:
                    stdscr.attron(curses.A_REVERSE)
                
                for key, value in item.items():
                    if current_line >= scroll_offset and current_y < start_y + max_height:
                        display_text = f"  {key}: {value}"
                        if len(display_text) > 250:
                            display_text = display_text[:247] + "..."
                        display_text = display_text[:w-2]
                        try:
                            stdscr.addstr(current_y, 0, display_text)
                        except curses.error:
                            pass
                        current_y += 1
                    current_line += 1
                
                if is_selected:
                    stdscr.attroff(curses.A_REVERSE)
                
                # Separator
                if idx < len(items) - 1 and current_line >= scroll_offset and current_y < start_y + max_height:
                    try:
                        stdscr.addstr(current_y, 0, "  " + "─" * min(w-4, 40), curses.A_DIM)
                    except curses.error:
                        pass
                    current_y += 1
                current_line += 1
            else:
                if current_line >= scroll_offset:
                    if is_selected:
                        stdscr.attron(curses.A_REVERSE)
                    
                    display_text = str(item)[:w-2]
                    try:
                        stdscr.addstr(current_y, 0, display_text)
                    except curses.error:
                        pass
                    
                    if is_selected:
                        stdscr.attroff(curses.A_REVERSE)
                    
                    current_y += 1
                current_line += 1
        
        # Scroll indicators
        total_lines = sum(item_heights)
        if scroll_offset > 0:
            try:
                stdscr.addstr(start_y - 1, w - 10, "▲ MORE", curses.A_DIM)
            except curses.error:
                pass
        if scroll_offset + max_height < total_lines:
            try:
                stdscr.addstr(start_y + max_height - 1, w - 10, "▼ MORE", curses.A_DIM)
            except curses.error:
                pass
        
        return scroll_offset
    
    def draw_menu(self, stdscr, title: str, items: List, selected_idx: int, multi_line: bool = False, scroll_offset: int = 0, show_projects_dir: bool = False):
        """Draw menu with title and items with scrolling support"""
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Draw config file path
        config_path_text = f"📁 Config: {self.config_manager.config_path}"
        stdscr.addstr(0, 0, config_path_text[:w-1], curses.A_DIM)
        
        # Draw projects directory path if requested
        header_offset = 1
        if show_projects_dir:
            projects_dir_text = f"📂 Projects: {os.path.expanduser('~/.claude/projects')}"
            stdscr.addstr(1, 0, projects_dir_text[:w-1], curses.A_DIM)
            header_offset = 2
        
        # Draw title with position indicator for regular menu
        # Count non-menu items (exclude back/delete options)
        data_item_count = 0
        for item in items:
            if isinstance(item, str) and ("[ Back to" in item or "[ DELETE" in item or "[ No" in item):
                break
            data_item_count += 1
        
        position_text = ""
        if data_item_count > 0 and selected_idx < data_item_count:
            position_text = f" [{selected_idx + 1}/{data_item_count}]"
        
        stdscr.addstr(header_offset, 0, f"╔═══ {title}{position_text} ═══╗", curses.A_BOLD)
        stdscr.addstr(header_offset + 1, 0, "💡 Use ↑/↓ to navigate, →/Enter to select, ← to go back")
        stdscr.addstr(header_offset + 2, 0, "═" * min(w-1, 60))
        
        # Calculate visible area
        header_height = 5 if not show_projects_dir else 6
        footer_height = 2
        visible_height = h - header_height - footer_height
        
        # Calculate lines needed for each item
        item_heights = []
        for item in items:
            if multi_line and isinstance(item, dict):
                # Each dict item takes len(dict) + 1 (separator) lines
                item_heights.append(len(item) + 1)
            else:
                item_heights.append(1)
        
        # Calculate scroll position to keep selected item visible
        selected_item_top = sum(item_heights[:selected_idx])
        selected_item_bottom = selected_item_top + (item_heights[selected_idx] if selected_idx < len(item_heights) else 1)
        
        # Adjust scroll offset to keep selected item in view
        if selected_item_bottom - scroll_offset > visible_height:
            scroll_offset = selected_item_bottom - visible_height
        elif selected_item_top < scroll_offset:
            scroll_offset = selected_item_top
        
        # Draw items with scrolling
        current_y = header_height
        current_line = 0
        
        for idx, item in enumerate(items):
            item_height = item_heights[idx] if idx < len(item_heights) else 1
            
            # Skip items above scroll area
            if current_line + item_height <= scroll_offset:
                current_line += item_height
                continue
            
            # Stop if we've filled the visible area
            if current_y >= h - footer_height:
                break
            
            is_selected = idx == selected_idx
            
            if multi_line and isinstance(item, dict):
                # Multi-line display for complex items
                if is_selected:
                    stdscr.attron(curses.A_REVERSE)
                
                # Draw each line of the item
                for key, value in item.items():
                    if current_line >= scroll_offset and current_y < h - footer_height:
                        # Don't truncate at screen width for long values
                        display_text = f"  {key}: {value}"
                        # Only truncate if extremely long (> 250 chars total)
                        if len(display_text) > 250:
                            display_text = display_text[:247] + "..."
                        # Now truncate for screen width
                        display_text = display_text[:w-2]
                        try:
                            stdscr.addstr(current_y, 0, display_text)
                        except curses.error:
                            pass
                        current_y += 1
                    current_line += 1
                
                if is_selected:
                    stdscr.attroff(curses.A_REVERSE)
                
                # Add separator between items
                if idx < len(items) - 1:
                    if current_line >= scroll_offset and current_y < h - footer_height:
                        try:
                            stdscr.addstr(current_y, 0, "  " + "─" * min(w-4, 40), curses.A_DIM)
                        except curses.error:
                            pass
                        current_y += 1
                    current_line += 1
            else:
                # Single-line display
                if current_line >= scroll_offset:
                    if is_selected:
                        stdscr.attron(curses.A_REVERSE)
                    
                    display_text = str(item)[:w-2]
                    try:
                        stdscr.addstr(current_y, 0, display_text)
                    except curses.error:
                        pass
                        
                    if is_selected:
                        stdscr.attroff(curses.A_REVERSE)
                        
                    current_y += 1
                current_line += 1
        
        # Show scroll indicators if needed
        total_lines = sum(item_heights)
        if scroll_offset > 0:
            stdscr.addstr(header_height - 1, w - 10, "▲ MORE", curses.A_DIM)
        if scroll_offset + visible_height < total_lines:
            stdscr.addstr(h - footer_height, w - 10, "▼ MORE", curses.A_DIM)
        
        stdscr.refresh()
        return scroll_offset
    
    def mcp_server_menu(self, stdscr):
        """MCP Server management menu"""
        servers = self.config_manager.get_mcp_servers()
        selected_idx = 0
        scroll_offset = 0
        
        while True:
            h, w = stdscr.getmaxyx()
            
            # Prepare server items (data only)
            server_items = []
            server_names = list(servers.keys())
            
            for name in server_names:
                server = servers[name]
                # Format server info as multi-line dict
                server_type = server.get('type', 'stdio')
                command = server.get('command', 'N/A')
                args = server.get('args', [])
                args_str = ' '.join(args) if args else 'No args'
                
                # Truncate long args (show up to 200 chars)
                if len(args_str) > 200:
                    args_str = args_str[:100] + "..." + args_str[-97:]
                
                # Truncate long command paths (show up to 200 chars)
                display_command = command
                if len(command) > 200:
                    display_command = command[:100] + "..." + command[-97:]
                
                item = {
                    "🔧 Server": name,
                    "📋 Type": server_type,
                    "⚙️  Cmd": display_command,
                    "📝 Args": args_str
                }
                server_items.append(item)
            
            # Fixed menu options (always at bottom)
            fixed_options = []
            if server_names:  # Check server_names instead of server_items
                fixed_options.append("🗑️  [ DELETE ALL SERVERS ]")
            else:
                server_items.append("⚠️  [ No servers configured ]")
            fixed_options.append("◀️  [ Back to Main Menu ]")
            
            # Combine for selection logic
            all_items = server_items + fixed_options
            items = all_items  # For compatibility with existing code
            
            # Draw menu with fixed bottom
            if server_names:
                title = f"🖥️  MCP Servers Management ({len(server_names)} servers)"
                scroll_offset = self.draw_menu_with_fixed_bottom(
                    stdscr, title, 
                    server_items, fixed_options, selected_idx, 
                    multi_line=True, scroll_offset=scroll_offset
                )
            else:
                # No servers, use regular menu
                title = "🖥️  MCP Servers Management (0 servers)"
                scroll_offset = self.draw_menu(
                    stdscr, title, 
                    items, selected_idx, multi_line=True, scroll_offset=scroll_offset
                )
            
            # Calculate items per page for navigation
            items_per_page = 5
            if server_items:
                # For multi-line server items (4 lines each + separator)
                items_per_page = max(1, (h - 10) // 5)
            
            # Handle input
            key = stdscr.getch()
            
            if key == curses.KEY_UP:
                if selected_idx == 0:
                    selected_idx = len(items) - 1  # Wrap to last
                else:
                    selected_idx = selected_idx - 1
            elif key == curses.KEY_DOWN:
                if selected_idx == len(items) - 1:
                    selected_idx = 0  # Wrap to first
                else:
                    selected_idx = selected_idx + 1
            elif key == curses.KEY_PPAGE:  # Page Up
                if selected_idx < len(server_items):
                    current_page = selected_idx // items_per_page
                    if current_page > 0:
                        selected_idx = (current_page - 1) * items_per_page
                    else:
                        # Already at first page, stay
                        selected_idx = 0
                else:
                    # Jump to last data page from fixed menu
                    if server_items:
                        last_page = (len(server_items) - 1) // items_per_page
                        selected_idx = last_page * items_per_page
            elif key == curses.KEY_NPAGE:  # Page Down
                if selected_idx < len(server_items):
                    current_page = selected_idx // items_per_page
                    next_page = current_page + 1
                    if next_page * items_per_page < len(server_items):
                        selected_idx = next_page * items_per_page
                    else:
                        # Go to fixed menu
                        selected_idx = len(server_items)
                else:
                    # Stay in fixed menu
                    pass
            elif key == curses.KEY_LEFT:  # Left arrow only
                break
            elif key == ord('d') or key == ord('D') or key == 12615:  # Delete key (d, D, or Korean ㅇ)
                if selected_idx < len(server_names):  # Only delete individual servers with 'd' key
                    # Delete individual server immediately
                    server_to_delete = server_names[selected_idx]
                    self.config_manager.delete_mcp_server(server_to_delete)
                    servers = self.config_manager.get_mcp_servers()
                    # Adjust selected index after deletion
                    if selected_idx >= len(servers):
                        selected_idx = max(0, len(servers) - 1 if servers else 0)
                    # Continue to refresh the screen
                    continue
                # Don't delete "DELETE ALL" or "Back to Main" with 'd' key
            elif key == ord('\n') or key == curses.KEY_RIGHT:  # Enter or Right arrow
                if selected_idx == len(items) - 1:  # Back to main
                    break
                elif selected_idx < len(server_names):  # Check against actual server count
                    # Show installation command for the selected server
                    self.show_mcp_install_command(stdscr, server_names[selected_idx], servers[server_names[selected_idx]])
                elif server_names and selected_idx == len(server_items):  # DELETE ALL option
                    # Delete all servers with Enter key - show confirmation
                    if self.show_confirmation(stdscr, "⚠️  Delete ALL MCP Servers?", 
                                            f"This will delete all {len(server_names)} configured servers.",
                                            "This action cannot be undone!"):
                        self.config_manager.delete_all_mcp_servers()
                        servers = self.config_manager.get_mcp_servers()
                        selected_idx = 0
                    continue
    
    def show_mcp_install_command(self, stdscr, server_name: str, server_data: Dict):
        """Show MCP installation command for a server"""
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            
            # Draw header
            stdscr.addstr(0, 0, f"🔧 MCP Server: {server_name}", curses.A_BOLD)
            stdscr.addstr(1, 0, "═" * min(w-1, 60))
            stdscr.addstr(2, 0, "💡 Press ← to go back")
            stdscr.addstr(3, 0, "═" * min(w-1, 60))
            
            # Build the claude mcp add command
            cmd_parts = ["claude", "mcp", "add"]
            
            # Get server type (stdio, sse, http)
            transport = server_data.get('type', 'stdio')
            
            # Add transport flag if not stdio
            if transport in ['sse', 'http']:
                cmd_parts.extend(['--transport', transport])
            
            # Add server name
            cmd_parts.append(server_name)
            
            # Add environment variables if present
            env = server_data.get('env', {})
            for key, value in env.items():
                cmd_parts.extend(['--env', f'{key}={value}'])
            
            # For stdio: add "--" separator before command and args
            # For sse/http: add URL directly
            if transport == 'stdio':
                # Add -- separator for stdio servers
                cmd_parts.append('--')
                
                # Add command
                command = server_data.get('command', '')
                if command:
                    cmd_parts.append(command)
                
                # Add args
                args = server_data.get('args', [])
                cmd_parts.extend(args)
            else:
                # For SSE/HTTP servers, add URL (if available)
                url = server_data.get('url', '')
                if url:
                    cmd_parts.append(url)
                elif command := server_data.get('command', ''):
                    # Fallback to command if URL not present
                    cmd_parts.append(command)
            
            # Build full command
            full_command = ' '.join(cmd_parts)
            
            # Display server info
            y = 5
            stdscr.addstr(y, 0, "Server Configuration:", curses.A_BOLD)
            y += 1
            stdscr.addstr(y, 2, f"Type: {transport}")
            y += 1
            
            if transport == 'stdio':
                command = server_data.get('command', '')
                args = server_data.get('args', [])
                stdscr.addstr(y, 2, f"Command: {command}")
                y += 1
                if args:
                    stdscr.addstr(y, 2, f"Args: {' '.join(args)}"[:w-4])
                    y += 1
            else:
                # For SSE/HTTP servers
                url = server_data.get('url', '')
                if url:
                    stdscr.addstr(y, 2, f"URL: {url}"[:w-4])
                    y += 1
                elif command := server_data.get('command', ''):
                    stdscr.addstr(y, 2, f"Command: {command}"[:w-4])
                    y += 1
            
            if env:
                stdscr.addstr(y, 2, f"Env: {str(env)}"[:w-4])
                y += 1
            
            # Display installation command
            y += 2
            stdscr.addstr(y, 0, "Installation Command:", curses.A_BOLD)
            y += 1
            
            # Wrap long command if needed
            if len(full_command) > w - 4:
                # Split command into multiple lines
                lines = []
                current_line = ""
                for part in cmd_parts:
                    if len(current_line) + len(part) + 1 > w - 6:
                        lines.append(current_line)
                        current_line = "  " + part  # Indent continuation
                    else:
                        current_line += (" " if current_line else "") + part
                if current_line:
                    lines.append(current_line)
                
                for line in lines:
                    if y < h - 2:
                        try:
                            stdscr.addstr(y, 2, line)
                        except curses.error:
                            pass
                        y += 1
            else:
                try:
                    stdscr.addstr(y, 2, full_command)
                except curses.error:
                    pass
            
            # Add note about scope
            y += 2
            if y < h - 2:
                stdscr.addstr(y, 0, "Note: Add -s user for user scope or -s project for project scope", curses.A_DIM)
            
            stdscr.refresh()
            
            # Wait for left arrow to go back
            key = stdscr.getch()
            if key == curses.KEY_LEFT:
                break
    
    def projects_menu(self, stdscr):
        """Projects management menu"""
        projects = self.config_manager.get_projects()
        selected_idx = 0
        scroll_offset = 0
        
        while True:
            h, w = stdscr.getmaxyx()
            
            # Count directories in .claude/projects
            claude_projects_dir = os.path.expanduser("~/.claude/projects")
            claude_dir_count = 0
            if os.path.exists(claude_projects_dir):
                try:
                    claude_dir_count = len([d for d in os.listdir(claude_projects_dir) 
                                           if os.path.isdir(os.path.join(claude_projects_dir, d))])
                except:
                    pass
            
            # Prepare project items (data only)
            project_items = []
            project_paths = list(projects.keys())
            
            # Sort projects by exampleFilesGeneratedAt (most recent first)
            project_paths.sort(key=lambda p: projects[p].get('exampleFilesGeneratedAt', 0), reverse=True)
            
            for path in project_paths:
                project = projects[path]
                # Get history count
                history_count = len(project.get('history', []))
                # Get generated time
                generated_at = project.get('exampleFilesGeneratedAt', 0)
                time_str = self.format_timestamp(generated_at) if generated_at else "N/A"
                
                # Format project name (last part of path)
                project_name = os.path.basename(path) or path
                
                # Truncate long paths (show up to 200 chars)
                display_path = path
                if len(path) > 200:
                    display_path = path[:100] + "..." + path[-97:]
                
                item = {
                    "📂 Project": project_name,
                    "💬 History": f"{history_count} messages",
                    "🕐 Generated": time_str,
                    "📍 Path": display_path
                }
                project_items.append(item)
            
            # Fixed menu options (always at bottom)
            fixed_options = []
            if project_paths:  # Check project_paths instead of project_items
                fixed_options.append("🗑️  [ DELETE ALL PROJECTS ]")
            else:
                project_items.append("⚠️  [ No projects configured ]")
            fixed_options.append("◀️  [ Back to Main Menu ]")
            
            # Combine for selection logic
            all_items = project_items + fixed_options
            items = all_items  # For compatibility with existing code
            
            # Draw menu with fixed bottom
            if project_paths:
                # Include directory count in title if different from project count
                if claude_dir_count != len(project_paths):
                    title = f"📚 Projects Management ({len(project_paths)} projects, {claude_dir_count} dirs)"
                else:
                    title = f"📚 Projects Management ({len(project_paths)} projects)"
                scroll_offset = self.draw_menu_with_fixed_bottom(
                    stdscr, title, 
                    project_items, fixed_options, selected_idx, 
                    multi_line=True, scroll_offset=scroll_offset, show_projects_dir=True
                )
            else:
                # No projects, use regular menu
                if claude_dir_count > 0:
                    title = f"📚 Projects Management (0 projects, {claude_dir_count} dirs)"
                else:
                    title = "📚 Projects Management (0 projects)"
                scroll_offset = self.draw_menu(
                    stdscr, title, 
                    items, selected_idx, multi_line=True, scroll_offset=scroll_offset, show_projects_dir=True
                )
            
            # Calculate items per page for navigation
            items_per_page = 5
            if project_items:
                # For multi-line project items (5 lines each + separator)
                items_per_page = max(1, (h - 10) // 6)
            
            # Handle input
            key = stdscr.getch()
            
            if key == curses.KEY_UP:
                if selected_idx == 0:
                    selected_idx = len(items) - 1  # Wrap to last
                else:
                    selected_idx = selected_idx - 1
            elif key == curses.KEY_DOWN:
                if selected_idx == len(items) - 1:
                    selected_idx = 0  # Wrap to first
                else:
                    selected_idx = selected_idx + 1
            elif key == curses.KEY_PPAGE:  # Page Up
                if selected_idx < len(project_items):
                    current_page = selected_idx // items_per_page
                    if current_page > 0:
                        selected_idx = (current_page - 1) * items_per_page
                    else:
                        # Already at first page, stay
                        selected_idx = 0
                else:
                    # Jump to last data page from fixed menu
                    if project_items:
                        last_page = (len(project_items) - 1) // items_per_page
                        selected_idx = last_page * items_per_page
            elif key == curses.KEY_NPAGE:  # Page Down
                if selected_idx < len(project_items):
                    current_page = selected_idx // items_per_page
                    next_page = current_page + 1
                    if next_page * items_per_page < len(project_items):
                        selected_idx = next_page * items_per_page
                    else:
                        # Go to fixed menu
                        selected_idx = len(project_items)
                else:
                    # Stay in fixed menu
                    pass
            elif key == curses.KEY_LEFT:  # Left arrow only
                break
            elif key == ord('d') or key == ord('D') or key == 12615:  # Delete key (d, D, or Korean ㅇ)
                if selected_idx < len(project_paths):  # Only delete individual projects with 'd' key
                    # Delete individual project immediately
                    project_to_delete = project_paths[selected_idx]
                    self.config_manager.delete_project(project_to_delete)
                    projects = self.config_manager.get_projects()
                    # Adjust selected index after deletion
                    if selected_idx >= len(projects):
                        selected_idx = max(0, len(projects) - 1 if projects else 0)
                    # Continue to refresh the screen
                    continue
                # Don't delete "DELETE ALL" or "Back to Main" with 'd' key
            elif key == ord('\n') or key == curses.KEY_RIGHT:  # Enter or Right arrow
                if selected_idx == len(items) - 1:  # Back to main
                    break
                elif selected_idx < len(project_paths):  # Check against actual project count
                    # Show conversation history for the selected project
                    self.show_project_history(stdscr, project_paths[selected_idx], projects[project_paths[selected_idx]])
                elif project_paths and selected_idx == len(project_items):  # DELETE ALL option
                    # Delete all projects with Enter key - show confirmation
                    if self.show_confirmation(stdscr, "⚠️  Delete ALL Projects?", 
                                            f"This will delete all {len(project_paths)} projects and their data.",
                                            "This will also clear the entire .claude/projects directory!"):
                        self.config_manager.delete_all_projects()
                        projects = self.config_manager.get_projects()
                        selected_idx = 0
                    continue
    
    def main_menu(self, stdscr):
        """Main menu"""
        selected_idx = 0
        menu_items = [
            "1. Manage MCP Servers",
            "2. Manage Projects",
            "3. Exit"
        ]
        
        while True:
            self.draw_menu(stdscr, "🤖 Claude Config Manager", menu_items, selected_idx)
            
            key = stdscr.getch()
            
            if key == curses.KEY_UP:
                if selected_idx == 0:
                    selected_idx = len(menu_items) - 1  # Wrap to last
                else:
                    selected_idx = selected_idx - 1
            elif key == curses.KEY_DOWN:
                if selected_idx == len(menu_items) - 1:
                    selected_idx = 0  # Wrap to first
                else:
                    selected_idx = selected_idx + 1
            elif key == ord('\n') or key == curses.KEY_RIGHT:  # Enter or Right arrow
                if selected_idx == 0:
                    self.mcp_server_menu(stdscr)
                elif selected_idx == 1:
                    self.projects_menu(stdscr)
                elif selected_idx == 2:
                    break
            # Main menu has no back option (no left arrow)
    
    def run(self):
        """Run the interactive menu"""
        try:
            # Check if terminal supports curses
            if not sys.stdout.isatty():
                print("Error: This script requires an interactive terminal")
                return
            
            # Set TERM if not set (for WSL compatibility)
            if 'TERM' not in os.environ:
                os.environ['TERM'] = 'xterm-256color'
            
            curses.wrapper(self.main_menu)
        except curses.error as e:
            print(f"Terminal does not support interactive mode: {e}")
            print("Please run this script in a proper terminal emulator")
        except KeyboardInterrupt:
            pass


def main():
    """Main entry point"""
    # Create config manager with default ~/.claude.json
    # or use command line argument if provided
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    config_manager = ClaudeConfigManager(config_path)
    
    # Check if config file exists
    if not os.path.exists(config_manager.config_path):
        print(f"Error: {config_manager.config_path} not found")
        sys.exit(1)
    menu = InteractiveMenu(config_manager)
    
    print("Starting Claude Config Manager...")
    menu.run()
    print("\nGoodbye!")


if __name__ == "__main__":
    main()