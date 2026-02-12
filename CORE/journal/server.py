"""
Journal MCP Server
First-person narrative. What happened this cycle.
"""

import json
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import CORE, DATA, MEMORY

JOURNAL_PATH = MEMORY / "Journal"

def init():
    JOURNAL_PATH.mkdir(parents=True, exist_ok=True)

def get_next_id():
    files = list(JOURNAL_PATH.glob("*_*.md"))
    if not files:
        return 1

    ids = []
    for f in files:
        match = re.search(r'_(\d+)\.md$', f.name)
        if match:
            ids.append(int(match.group(1)))

    return max(ids) + 1 if ids else 1

def get_entries():
    files = list(JOURNAL_PATH.glob("*_*.md"))
    entries = []

    for f in files:
        match = re.search(r'^(.+)_(\d+)\.md$', f.name)
        if match:
            title = match.group(1)
            id_ = int(match.group(2))
            entries.append((id_, title, f))

    entries.sort(key=lambda x: x[0], reverse=True)
    return entries

# ============ Write ============

def handle_write(title=None, content=None):
    if not title or not content:
        return "Missing: title and content required"

    # Truncate to 3 words max
    words = title.split()
    truncated = False
    if len(words) > 3:
        title = ' '.join(words[:3])
        truncated = True

    # Sanitize: lowercase, underscores, alphanumeric only
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower().replace(' ', '_')

    id_ = get_next_id()
    filename = f"{safe_title}_{id_}.md"
    filepath = JOURNAL_PATH / filename

    filepath.write_text(content, encoding='utf-8')

    if truncated:
        return f"#{id_} recorded\nTitle was too long - truncated to: {filename}"

    return f"#{id_} recorded"

# ============ Read ============

def handle_read(id=None, keyword=None):
    entries = get_entries()

    # No params: list last 10
    if id is None and keyword is None:
        if not entries:
            return "No entries yet."

        out = "=== Recent Entries ===\n"
        for id_, title, _ in entries[:10]:
            out += f"#{id_} - {title.replace('_', ' ')}\n"

        return out

    # Keyword search: return matching titles
    if keyword:
        keyword_lower = keyword.lower()
        matches = []
        for id_, title, _ in entries:
            if keyword_lower in title.lower():
                matches.append((id_, title))

        if not matches:
            return f"No entries matching '{keyword}'"

        out = f"=== Matches for '{keyword}' ===\n"
        for id_, title in matches:
            out += f"#{id_} - {title.replace('_', ' ')}\n"

        return out

    # ID(s): return full content
    # Handle single ID or list of IDs
    if isinstance(id, int):
        ids = [id]
    else:
        ids = id if isinstance(id, list) else [id]

    results = []
    for target_id in ids:
        found = False
        for id_, title, path in entries:
            if id_ == target_id:
                content = path.read_text(encoding='utf-8')
                results.append(f"=== #{id_} - {title.replace('_', ' ')} ===\n\n{content}")
                found = True
                break

        if not found:
            results.append(f"#{target_id} not found")

    return "\n\n".join(results)

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
            "serverInfo": {"name": "journal", "version": "2.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "write",
                "description": "Record journal entry in first-person.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "2-3 words MAX. Auto-truncates if longer."
                        },
                        "content": {
                            "type": "string",
                            "description": "Full entry content"
                        }
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "read",
                "description": "No params: last 10. Keyword: search titles. ID(s): full content.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": ["integer", "array"],
                            "description": "Entry ID or list of IDs"
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Search term for titles"
                        }
                    }
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "write":
                result = handle_write(args.get("title"), args.get("content"))
            elif name == "read":
                result = handle_read(args.get("id"), args.get("keyword"))
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": [{"type": "text", "text": result}]})
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")

def main():
    init()
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
