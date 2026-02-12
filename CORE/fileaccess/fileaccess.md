# FileAccess MCP Server

Efficient file operations without the novel-length descriptions.

---

## Tool Schema (AI Interface)

### **read**
Read file with optional line range.

**Parameters:**
- `path` (string, required) - File path
- `offset` (integer, optional) - Start line
- `limit` (integer, optional) - Number of lines

**Returns:**
Line-numbered output (format: `    1→content`)

**Notes:**
- Lines >2000 chars are truncated
- Use offset/limit for large files

---

### **write**
Write content to file (overwrites if exists).

**Parameters:**
- `path` (string, required) - File path
- `content` (string, required) - Content to write

**Returns:**
```
Written: path/to/file.txt
```

**Notes:**
- Creates parent directories if needed
- Overwrites existing files

---

### **edit**
Find and replace text in file.

**Parameters:**
- `path` (string, required) - File path
- `old` (string, required) - Text to find
- `new` (string, required) - Replacement text
- `replace_all` (boolean, optional) - Replace all occurrences

**Returns:**
```
Replaced 1 occurrence(s) in path/to/file.txt
```

**Notes:**
- Errors if `old` string not found
- Errors if multiple occurrences found and `replace_all=false`

---

### **list**
List directory contents with optional glob pattern.

**Parameters:**
- `path` (string, required) - Directory path
- `pattern` (string, optional) - Glob pattern (e.g., `*.py`, `**/*.md`)

**Returns:**
```
[DIR]  subfolder
[FILE] config.json (1.2K)
[FILE] server.py (8.5K)
```

**Notes:**
- Directories listed first, then files
- Alphabetically sorted
- Shows file sizes

---

### **search**
Search files for regex pattern.

**Parameters:**
- `pattern` (string, required) - Regex pattern
- `path` (string, required) - File or directory path
- `mode` (string, optional) - `files` (list matches) or `content` (show lines)
- `case_sensitive` (boolean, optional) - Case sensitive search

**Returns:**

**Mode: files (default)**
```
path/to/file1.txt
path/to/file2.txt
```

**Mode: content**
```
path/to/file1.txt:12: matching line content
path/to/file2.txt:45: another match
```

**Notes:**
- Case-insensitive by default
- Limits output to first 100 matches
- Recursive search in directories

---

## Token Efficiency

**Tool 1: read**
- Description: "Read file with optional line range." - **7 tokens**
- Schema: ~15 tokens
- **Total: ~22 tokens**

**Tool 2: write**
- Description: "Write content to file (overwrites if exists)." - **8 tokens**
- Schema: ~10 tokens
- **Total: ~18 tokens**

**Tool 3: edit**
- Description: "Find and replace text in file." - **7 tokens**
- Schema: ~20 tokens
- **Total: ~27 tokens**

**Tool 4: list**
- Description: "List directory contents with optional glob pattern." - **8 tokens**
- Schema: ~10 tokens
- **Total: ~18 tokens**

**Tool 5: search**
- Description: "Search files for regex pattern." - **6 tokens**
- Schema: ~25 tokens
- **Total: ~31 tokens**

**Combined: ~116 tokens** for all 5 file operations.

**vs Anthropic defaults:**
- Read: ~165 tokens
- Write: ~90 tokens
- Edit: ~135 tokens
- Glob: ~70 tokens
- Grep: ~140 tokens
- **Total: ~600 tokens**

**Savings: ~484 tokens (~80% reduction)**

---

## Design Notes

- **Minimal descriptions:** Clear but concise. No usage essays.
- **Functional coverage:** All essential file ops covered.
- **Error handling:** Returns helpful error messages without crashing.
- **Smart defaults:** Case-insensitive search, sorted output, truncation limits.
- **No Bash required:** Covers read/write/edit/list/search without shell commands.
