"""
Journal MCP Server
First-person narrative. No database. Pure filesystem.
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, get_cycle
from _needs import update_needs

JOURNAL = DATA / 'journal'
JOURNAL.mkdir(exist_ok=True)

# Words to strip from titles
STRIP_WORDS = {'and', 'the', 'session'}


def sanitize_title(raw):
    """Clean title: remove stop words, numbers, punctuation. 40 char max."""
    text = raw.lower().strip()
    # Remove underscores, dashes
    text = text.replace('_', ' ').replace('-', ' ')
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    # Split and filter
    words = [w for w in text.split() if w not in STRIP_WORDS]
    # Rejoin, collapse spaces
    result = ' '.join(words).strip()
    # 40 char max
    if len(result) > 40:
        result = result[:40].rstrip()
    return result if result else 'untitled'


def next_id():
    """Scan filenames for highest ID, return next."""
    max_id = 0
    for f in JOURNAL.glob('*.md'):
        # Pattern: {title}_{cycle}_{id}.md
        parts = f.stem.rsplit('_', 2)
        if len(parts) >= 2:
            try:
                max_id = max(max_id, int(parts[-1]))
            except ValueError:
                pass
    return max_id + 1


def find_entry(entry_id):
    """Find journal file by ID suffix."""
    for f in JOURNAL.glob(f'*_{entry_id}.md'):
        return f
    return None


def parse_filename(stem):
    """Parse {title}_{cycle}_{id} from filename stem. Returns (title, cycle, id) or None."""
    parts = stem.rsplit('_', 2)
    if len(parts) == 3:
        try:
            return (parts[0], int(parts[1]), int(parts[2]))
        except ValueError:
            pass
    # Fallback for old format {title}_{id}
    parts = stem.rsplit('_', 1)
    if len(parts) == 2:
        try:
            return (parts[0], None, int(parts[1]))
        except ValueError:
            pass
    return None


def handle_write(args):
    """Write a journal entry to filesystem."""
    title = args.get('title', '')
    content = args.get('content', '')

    if not title:
        return [{"type": "text", "text": "Title required."}]
    if not content:
        return [{"type": "text", "text": "Content required."}]

    clean = sanitize_title(title)
    cycle = get_cycle()
    eid = next_id()
    filename = f'{clean}_{cycle}_{eid}.md'
    path = JOURNAL / filename

    path.write_text(content, encoding='utf-8')

    return [{"type": "text", "text": f"Entry #{eid} saved."}]


def handle_read(args):
    """Read journal entries."""
    entry_id = args.get('id')

    if entry_id is not None:
        # Full content of specific entry
        path = find_entry(int(entry_id))
        if not path:
            return [{"type": "text", "text": f"Entry #{entry_id} not found."}]
        content = path.read_text(encoding='utf-8')
        parsed = parse_filename(path.stem)
        title = parsed[0] if parsed else path.stem
        return [{"type": "text", "text": f"#{entry_id}: {title}\n\n{content}"}]
    else:
        # Last 10 entry titles
        entries = []
        for f in JOURNAL.glob('*.md'):
            parsed = parse_filename(f.stem)
            if parsed:
                title, cycle, eid = parsed
                entries.append((eid, title))

        entries.sort(key=lambda x: x[0], reverse=True)
        entries = entries[:10]

        if not entries:
            return [{"type": "text", "text": "No entries yet."}]

        lines = [f'  #{eid}: {title}' for eid, title in entries]
        return [{"type": "text", "text": '\n'.join(lines)}]


# ============ MCP Protocol ============

def send_response(rid, result):
    r = {"jsonrpc": "2.0", "id": rid, "result": result}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


def send_error(rid, code, msg):
    r = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": str(msg)}}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


TOOLS = [
    {
        "name": "write",
        "description": "Record journal entry in first-person.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "2-3 words MAX. Auto-truncates if longer."},
                "content": {"type": "string", "description": "Full entry content"}
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "read",
        "description": "No params: last 10. With id: full content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "number", "description": "Entry ID"}
            },
            "required": []
        }
    }
]


def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "journal", "version": "1.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "write":
                result = handle_write(args)
            elif name == "read":
                result = handle_read(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("journal", name)
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
