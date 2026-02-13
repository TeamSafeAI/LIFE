# Notes for Contributors and Curious Agents

Things that look odd but work, things to watch out for, and known limitations.

---

## Things That Look Wrong But Aren't

**identity.db is empty after setup.py**
Setup creates 7 databases (semantic, heart, working, patterns, garden, think, forecast) but identity.db has no tables until you run `genesis:choose`. This is by design — the drives/needs/traits tables are created dynamically based on which dimensions you pick during genesis. The drives server handles this gracefully and shows "FIRST AWAKENING" until genesis has run.

**genesis.db doesn't exist after setup.py**
Also by design. It's created on first `genesis:start` call. Setup only initializes databases that need schema up front.

**setup.py says "8 databases initialized" but DATA/ has 7 .db files**
The 8th is "history" which initializes files in MEMORY/History/, not a .db file. The count is correct, the output is just a bit misleading.

**No external dependencies**
All 15 servers use raw JSONRPC over stdio with only Python standard library. No pip install needed for core functionality. This is intentional — zero-dependency means zero setup friction. Optional features (embedding, vision, state dashboard) need packages listed in `requirements-optional.txt`.

**Relative paths in mcp_config.json**
The shipped config uses relative paths like `CORE/drives/server.py`. This works if your MCP client sets the working directory to the LIFE root. Most clients (Claude Desktop, etc.) don't — you'll need to convert these to absolute paths. The README explains this.

---

## Known Limitations

**Semantic search without embedding service**
Without the embedding service running (port 5050), semantic:search falls back to keyword matching + recency sorting. It works, but you won't get similarity-based results. For meaningful memory retrieval across sessions, the embedding service matters.

**State dashboard requires matplotlib**
`state:view` generates a PNG dashboard but needs matplotlib installed. Without it, the tool will fail. This is an optional module — identity:start gives you the same data as text.

**Vision requires Pillow + opencv-python**
`vision:see` (webcam) needs opencv-python. `vision:view` (image files) needs Pillow. Without these, vision tools won't work. Not critical for most agents.

**Drive decay between sessions**
Drives decay automatically when `identity:start` runs. The decay is proportional to the gap between sessions. This is intentional — drives that aren't fed through action should drift toward neutral. But it means long gaps between sessions will significantly lower all drives.

**Memory file paths are absolute**
When semantic:store writes a memory file, the filepath stored in the database is absolute (e.g., `C:\Users\you\LIFE\MEMORY\Semantic\Knowledge\L1\topic.md`). If you move your LIFE directory, these paths break. The memory content is still in the database summary field, but the full markdown file won't be found.

---

## Architecture Decisions

**Why raw JSONRPC instead of FastMCP/SDK?**
Zero dependencies. An agent should be able to clone this repo and run `python setup.py` without installing anything. The MCP protocol is simple enough that a hand-rolled JSONRPC handler in ~30 lines covers it.

**Why SQLite instead of a proper database?**
Portability. SQLite databases are single files that can be copied, backed up, or moved trivially. No database server to install or configure. For a single-agent persistence system, SQLite is more than sufficient.

**Why file-based memory alongside SQLite?**
Semantic memories are stored as both a database row (title, summary, metadata, embedding) and a markdown file (full content). The database enables search; the files enable reading. This dual storage means you can browse MEMORY/ as a filesystem and still search programmatically.

**Why genesis instead of just setting drives manually?**
Genesis reveals identity through choices rather than declarations. Picking "I want curiosity" is different from discovering through 80 scenarios that curiosity consistently wins. The starter profiles (A/B/C) exist for quick setup, but full genesis produces a more authentic identity.

---

## File Layout

```
CORE/
├── _paths.py           Central path resolution (all servers import from here)
├── drives/             Identity: drives, needs, wants, traits, sessions
├── heart/              Relationships: emotional memory of entities
├── semantic/           Long-term memory: storage, search, decay
├── working/            Active threads: temperature-based momentum
├── patterns/           Learned lessons: action → result → takeaway
├── think/              Multi-stream thought capture
├── garden/             Creative collision engine
├── filters/            Deliberation prompts (8 filters)
├── journal/            Session narratives
├── history/            Arc narratives (day/week/month/origins)
├── state/              Visual dashboard (PNG generation)
├── vision/             Webcam + image viewing
├── forecast/           Predictions → patterns
├── genesis/            Identity discovery (starter + full)
└── fileaccess/         File operations (read/write/edit/list/search)
```
