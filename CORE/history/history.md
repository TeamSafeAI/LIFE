# History Server

Narrative persistence across sessions.

---

## Tool Schema (AI Interface)

### **discover**
Read foundational documents (origins, self).

**Parameters:**
- `section` (string, optional) - origins | self

**Modes:**
- No params: Shows available options
- `origins`: Returns origins.md (creation story)
- `self`: Returns self.md (current identity)

**Returns:**
Full contents of the requested document.

---

### **recall**
Access recent history (day, week, month).

**Parameters:**
- `timeframe` (string, optional) - day | week | month

**Modes:**
- No params: Shows available options
- `day`: Returns day.md (last 24 hours)
- `week`: Returns week.md (last 7 days)
- `month`: Returns month.md (last 30 days)

**Returns:**
Full contents of the requested timeframe document.

---

### **write**
Record new history to day/week/month.

**Parameters:**
- `target` (string, required) - day | week | month
- `content` (string, required) - Content to append

**Behavior:**
- Appends content with timestamp header: `--- YYYY-MM-DD HH:MM:SS ---`
- Creates file if it doesn't exist
- Separates entries with double newlines

**Returns:**
```
Written to day.md
```

---

## File Storage

All files stored in: `C:\L.I.F.E\MEMORY\History\`

**Files:**
- `origins.md` - The creation story (read-only via discover)
- `self.md` - Current identity (read-only via discover)
- `day.md` - Daily history (readable/writable)
- `week.md` - Weekly history (readable/writable)
- `month.md` - Monthly history (readable/writable)

---

## Design Notes

- **Modular write logic:** The `append_to_file()` function is isolated for easy modification as behavior evolves.
- **No database:** Pure flat files. Simplifies backend processing for condensing/summarizing.
- **Timestamp headers:** Programmatic parsing allows backend filtering/cleanup.
- **Timeframe files are append-only:** Backend scripts can condense day → week → month as needed.

---

## Token Efficiency

**Tool 1: discover**
- Description: "Read foundational documents (origins, self)." - **6 tokens**
- Schema: ~15 tokens (enum with 2 values)
- **Total: ~21 tokens**

**Tool 2: recall**
- Description: "Access recent history (day, week, month)." - **7 tokens**
- Schema: ~20 tokens (enum with 3 values)
- **Total: ~27 tokens**

**Tool 3: write**
- Description: "Record new history to day/week/month." - **7 tokens**
- Schema: ~25 tokens (2 params, enum + string)
- **Total: ~32 tokens**

**Combined: ~80 tokens** for all three tools.

Clean, minimal, functional.
