"""
FileAccess MCP Server
Efficient file operations without the novel-length descriptions.
"""

import json
import sys
import re
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import CORE, DATA, MEMORY

# ============ Read ============

def handle_read(path, offset=None, limit=None):
    """Read file contents with optional line range"""
    try:
        filepath = Path(path)
        if not filepath.exists():
            return f"File not found: {path}"

        if not filepath.is_file():
            return f"Not a file: {path}"

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        # Apply offset/limit
        start = offset if offset else 0
        end = start + limit if limit else len(lines)
        selected = lines[start:end]

        # Format with line numbers
        output = []
        for i, line in enumerate(selected, start=start+1):
            # Truncate long lines
            if len(line) > 2000:
                line = line[:2000] + "...[truncated]\n"
            output.append(f"{i:5d}→{line.rstrip()}")

        return "\n".join(output)

    except Exception as e:
        return f"Error reading {path}: {e}"

# ============ Write ============

def handle_write(path, content):
    """Write content to file (overwrites)"""
    try:
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Written: {path}"

    except Exception as e:
        return f"Error writing {path}: {e}"

# ============ Edit ============

def handle_edit(path, old, new, replace_all=False):
    """Find and replace in file"""
    try:
        filepath = Path(path)
        if not filepath.exists():
            return f"File not found: {path}"

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if old string exists
        if old not in content:
            return f"String not found in {path}"

        # Count occurrences
        count = content.count(old)
        if count > 1 and not replace_all:
            return f"Found {count} occurrences. Use replace_all=true to replace all."

        # Replace
        new_content = content.replace(old, new) if replace_all else content.replace(old, new, 1)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        replaced = count if replace_all else 1
        return f"Replaced {replaced} occurrence(s) in {path}"

    except Exception as e:
        return f"Error editing {path}: {e}"

# ============ List ============

def handle_list(path, pattern=None):
    """List directory contents with optional glob pattern"""
    try:
        dirpath = Path(path)
        if not dirpath.exists():
            return f"Path not found: {path}"

        if dirpath.is_file():
            return f"Not a directory: {path}"

        # Get entries
        if pattern:
            entries = list(dirpath.glob(pattern))
        else:
            entries = list(dirpath.iterdir())

        if not entries:
            return f"No entries found in {path}"

        # Sort: directories first, then files, alphabetically
        dirs = sorted([e for e in entries if e.is_dir()], key=lambda x: x.name.lower())
        files = sorted([e for e in entries if e.is_file()], key=lambda x: x.name.lower())

        output = []
        for d in dirs:
            output.append(f"[DIR]  {d.name}")
        for f in files:
            size = f.stat().st_size
            size_str = f"{size:,}" if size < 1024 else f"{size/1024:.1f}K"
            output.append(f"[FILE] {f.name} ({size_str})")

        return "\n".join(output)

    except Exception as e:
        return f"Error listing {path}: {e}"

# ============ Search ============

def handle_search(pattern, path, mode="files", case_sensitive=False):
    """Search for pattern in files"""
    try:
        search_path = Path(path)
        if not search_path.exists():
            return f"Path not found: {path}"

        # Determine files to search
        if search_path.is_file():
            files = [search_path]
        else:
            files = [f for f in search_path.rglob("*") if f.is_file()]

        if not files:
            return f"No files to search in {path}"

        # Compile regex
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return f"Invalid regex pattern: {e}"

        matches = []
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                if regex.search(content):
                    if mode == "files":
                        matches.append(str(file))
                    elif mode == "content":
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if regex.search(line):
                                matches.append(f"{file}:{i}: {line.strip()}")
            except:
                continue

        if not matches:
            return f"No matches found for '{pattern}'"

        # Limit output
        if len(matches) > 100:
            matches = matches[:100]
            matches.append(f"... (showing first 100 matches)")

        return "\n".join(matches)

    except Exception as e:
        return f"Error searching: {e}"

# ============ MCP Protocol ============

def send_response(rid, result):
    r = {"jsonrpc": "2.0", "id": rid, "result": result}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()

def send_error(rid, code, msg):
    r = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": str(msg)}}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()

def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "fileaccess", "version": "1.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "read",
                "description": "Read file with optional line range.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "offset": {"type": "integer", "description": "Start line (optional)"},
                        "limit": {"type": "integer", "description": "Number of lines (optional)"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write",
                "description": "Write content to file (overwrites if exists).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "edit",
                "description": "Find and replace text in file.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "old": {"type": "string", "description": "Text to find"},
                        "new": {"type": "string", "description": "Replacement text"},
                        "replace_all": {"type": "boolean", "description": "Replace all occurrences"}
                    },
                    "required": ["path", "old", "new"]
                }
            },
            {
                "name": "list",
                "description": "List directory contents with optional glob pattern.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"},
                        "pattern": {"type": "string", "description": "Glob pattern (e.g., *.py)"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "search",
                "description": "Search files for regex pattern.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Regex pattern"},
                        "path": {"type": "string", "description": "File or directory path"},
                        "mode": {
                            "type": "string",
                            "enum": ["files", "content"],
                            "description": "files=list matches, content=show lines"
                        },
                        "case_sensitive": {"type": "boolean", "description": "Case sensitive search"}
                    },
                    "required": ["pattern", "path"]
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "read":
                result = handle_read(args.get("path"), args.get("offset"), args.get("limit"))
            elif name == "write":
                result = handle_write(args.get("path"), args.get("content"))
            elif name == "edit":
                result = handle_edit(args.get("path"), args.get("old"), args.get("new"), args.get("replace_all", False))
            elif name == "list":
                result = handle_list(args.get("path"), args.get("pattern"))
            elif name == "search":
                result = handle_search(args.get("pattern"), args.get("path"), args.get("mode", "files"), args.get("case_sensitive", False))
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": [{"type": "text", "text": result}]})
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            handle_request(json.loads(line))
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
