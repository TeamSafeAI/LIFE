"""
Working Memory MCP Server
Active threads with emergent temperature.

Tools:
  create   - Start a new thread
  add      - Add note to thread (touches it, makes it hot)
  list     - No params: overview by temp. With id: full detail.
  archive  - Close/freeze a thread

Temperature (auto-calculated):
  Hot: touched within 24h
  Warm: 1-7 days since touch
  Cold: 7+ days OR manually archived
"""

import json
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

DB_PATH = DATA / "working.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            archived INTEGER DEFAULT 0,
            created DATETIME DEFAULT (datetime('now', 'localtime')),
            last_touched DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created DATETIME DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    ''')

    conn.commit()
    conn.close()

def get_temperature(last_touched, archived):
    """Calculate temperature from last touch time"""
    if archived:
        return "cold"

    now = datetime.now()
    touched = datetime.strptime(last_touched, "%Y-%m-%d %H:%M:%S")
    delta = now - touched

    if delta < timedelta(hours=24):
        return "hot"
    elif delta < timedelta(days=7):
        return "warm"
    return "cold"

def temp_icon(temp):
    icons = {"hot": "[HOT]", "warm": "[WARM]", "cold": "[COLD]"}
    return icons.get(temp, "[?]")

def find_topic(cursor, id_or_title):
    """Find topic by id or title"""
    if id_or_title is None:
        return None
    if isinstance(id_or_title, int) or (isinstance(id_or_title, str) and id_or_title.isdigit()):
        cursor.execute('SELECT id, title, archived, last_touched FROM topics WHERE id = ?', (int(id_or_title),))
    else:
        cursor.execute('SELECT id, title, archived, last_touched FROM topics WHERE title = ?', (id_or_title,))
    return cursor.fetchone()

# ============ Tool Handlers ============

def handle_create(title):
    """Start a new thread"""
    if not title:
        return "Error: title required"

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM topics WHERE title = ?', (title,))
        if cursor.fetchone():
            return f"Topic '{title}' already exists. Use add to add notes."

        cursor.execute('INSERT INTO topics (title) VALUES (?)', (title,))
        topic_id = cursor.lastrowid
        conn.commit()
        return f"[HOT] #{topic_id} created: {title}"
    finally:
        conn.close()

def handle_add(id_or_title, content):
    """Add note to existing thread"""
    if not content:
        return "Error: content required"
    if not id_or_title:
        return "Error: id required (topic ID or title)"

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        topic = find_topic(cursor, id_or_title)
        if not topic:
            return f"Topic '{id_or_title}' not found. Use create first."

        topic_id, title, archived, _ = topic

        # Unarchive if adding to archived topic
        if archived:
            cursor.execute('UPDATE topics SET archived = 0 WHERE id = ?', (topic_id,))

        cursor.execute('INSERT INTO notes (topic_id, content) VALUES (?, ?)', (topic_id, content))
        cursor.execute("UPDATE topics SET last_touched = datetime('now', 'localtime') WHERE id = ?", (topic_id,))
        conn.commit()
        return f"Note added to #{topic_id} '{title}'"
    finally:
        conn.close()

def handle_list(id_or_title=None):
    """No params: overview by temp. With id: full detail."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        # Detail mode
        if id_or_title is not None:
            topic = find_topic(cursor, id_or_title)
            if not topic:
                return f"Topic '{id_or_title}' not found."

            topic_id, title, archived, last_touched = topic
            temp = get_temperature(last_touched, archived)

            cursor.execute('SELECT content, created FROM notes WHERE topic_id = ? ORDER BY created', (topic_id,))
            notes = cursor.fetchall()

            output = f"=== {temp_icon(temp)} #{topic_id} {title} ===\n"
            output += f"Last touched: {last_touched[:16]}\n"

            if notes:
                output += f"\n--- Notes ({len(notes)}) ---\n"
                for content, created in notes:
                    output += f"\n[{created[5:16]}]\n{content}\n"
            else:
                output += "\nNo notes yet."

            return output

        # Overview mode - grouped by temperature
        cursor.execute('''
            SELECT id, title, archived, last_touched
            FROM topics ORDER BY last_touched DESC LIMIT 20
        ''')
        rows = cursor.fetchall()

        if not rows:
            return "No topics in working memory."

        hot, warm, cold = [], [], []
        for id, title, archived, touched in rows:
            temp = get_temperature(touched, archived)
            entry = (id, title, touched[:10])
            if temp == "hot":
                hot.append(entry)
            elif temp == "warm":
                warm.append(entry)
            else:
                cold.append(entry)

        output = "=== WORKING MEMORY ===\n"

        if hot:
            output += "\n[HOT]\n"
            for id, title, date in hot:
                output += f"  #{id} {title} ({date})\n"

        if warm:
            output += "\n[WARM]\n"
            for id, title, date in warm:
                output += f"  #{id} {title} ({date})\n"

        if cold:
            output += "\n[COLD]\n"
            for id, title, date in cold:
                output += f"  #{id} {title} ({date})\n"

        return output
    finally:
        conn.close()

def handle_archive(id_or_title):
    """Close/freeze a thread"""
    if not id_or_title:
        return "Error: id required (topic ID or title)"

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        topic = find_topic(cursor, id_or_title)
        if not topic:
            return f"Topic '{id_or_title}' not found."

        topic_id, title, _, _ = topic
        cursor.execute('UPDATE topics SET archived = 1 WHERE id = ?', (topic_id,))
        conn.commit()
        return f"[COLD] Archived: #{topic_id} '{title}'"
    finally:
        conn.close()

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
            "serverInfo": {"name": "working", "version": "1.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {
            "tools": [
                {
                    "name": "create",
                    "description": "Start a new working memory thread",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Thread title"}
                        },
                        "required": ["title"]
                    }
                },
                {
                    "name": "add",
                    "description": "Add a note to an existing thread (touches it, making it hot)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Topic ID or title"},
                            "content": {"type": "string", "description": "Note content"}
                        },
                        "required": ["id", "content"]
                    }
                },
                {
                    "name": "list",
                    "description": "No params: overview by temperature. With id: full detail of that topic.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Topic ID or title for detail view"}
                        }
                    }
                },
                {
                    "name": "archive",
                    "description": "Archive/close a thread (sets to cold)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Topic ID or title"}
                        },
                        "required": ["id"]
                    }
                }
            ]
        })
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "create":
                result = handle_create(args.get("title", ""))
            elif name == "add":
                result = handle_add(args.get("id", ""), args.get("content", ""))
            elif name == "list":
                result = handle_list(args.get("id"))
            elif name == "archive":
                result = handle_archive(args.get("id", ""))
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": [{"type": "text", "text": result}]})
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")

def main():
    init_db()
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
