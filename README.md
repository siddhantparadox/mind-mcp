# Mind 🧠

**Mind** is a local, shared long‑term memory service for your AI agents.

- Runs fully locally in **Docker**
- Stores everything in a single **SQLite** database with **sqlite‑vec** for vector search
- Uses **OpenRouter** for embeddings + optional LLM assist (classification & summaries)
- Exposes a **Gradio v6 UI** for humans
- Exposes an **MCP server** on the same port for agents (Claude, Cursor, etc.)

Everything stays on your machine.

---

## Architecture

- **Database:** SQLite with [`sqlite-vec`](https://github.com/asg017/sqlite-vec) as a `vec0` virtual table for embeddings :contentReference[oaicite:3]{index=3}  
  - Main tables: `memories`, `vec_memories`, `clusters`, `memory_relations`
- **Embeddings:** OpenRouter `/embeddings`  
  - Model: `MIND_EMBEDDING_MODEL` (default `qwen/qwen3-embedding-8b`) :contentReference[oaicite:4]{index=4}  
- **LLM assist (optional):** OpenRouter `/chat/completions`  
  - Model: `MIND_LLM_MODEL` (default `qwen/qwen-2.5-7b-instruct`, overridable in `.env`) :contentReference[oaicite:5]{index=5}  
  - Used to infer `type`, `tags`, `importance`, and a `summary` for each memory
- **UI & MCP:** Gradio v6 `Blocks`, launched with `mcp_server=True` and custom theme/CSS at `/gradio_api/mcp/` :contentReference[oaicite:6]{index=6}  

---

## Prerequisites

You can run Mind entirely via Docker (recommended).

### Required

- **OpenRouter account + API key**
  - Create an OpenRouter account
  - Get an API key and set `OPENROUTER_API_KEY` in `.env`
- **Docker** & **Docker Compose**
  - Docker 24+ recommended
  - Compose v2+ (usually bundled with Docker Desktop)

### Optional (for many MCP clients)

If your MCP client only supports **local stdio servers** (Claude Desktop, many Cursor builds, etc.), you’ll also want:

- **Node.js** (20+ recommended)
- `mcp-remote` installed globally:

```bash
npm install -g mcp-remote
````

`mcp-remote` is a tiny CLI that lets stdio‑only MCP clients talk to Mind’s HTTP MCP endpoint.

---

## Configuration (`.env`)

Create a `.env` file in the repo root:

```env
# Required: OpenRouter key
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY_HERE

# Optional overrides (all have defaults in code)
MIND_EMBEDDING_MODEL=qwen/qwen3-embedding-8b
MIND_LLM_MODEL=google/gemini-2.5-flash-lite-preview-09-2025
MIND_EMBEDDING_DIM=4096

SQLITE_VEC_PATH=/usr/local/lib/vec0

MIND_DATA_DIR=./data
MIND_DB_PATH=./data/mind.db

MIND_SERVER_NAME=0.0.0.0
MIND_SERVER_PORT=7860

# AI assist: if true, Mind uses an LLM to infer type/tags/importance/summary
MIND_AI_ASSIST=true

# Reserved for future automatic clustering
MIND_AUTO_CLUSTER=true
```

Notes:

* `OPENROUTER_API_KEY` **must** be set.
* `MIND_AI_ASSIST` defaults to `true` in code and in `docker-compose.yml`, so AI assist is on unless you explicitly turn it off. 

---

## Running Mind

### Docker (recommended)

Build & run:

```bash
docker compose up --build
```

This:

* Installs Python deps + `sqlite-vec` into the image 
* Ensures `/app/data` exists for the database
* Starts the Mind server at `http://localhost:7860`
* Creates/uses the `mind_data` volume for persistent storage 

Access:

* **UI:** [http://localhost:7860](http://localhost:7860)
* **MCP endpoint:** [http://localhost:7860/gradio_api/mcp/](http://localhost:7860/gradio_api/mcp/)

Data:

* SQLite DB lives at `/app/data/mind.db` inside the container
* Persisted in the `mind_data` Docker volume

### Local (non‑Docker) dev

If you want to run Brain directly:

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY=sk-or-...
python -m mind.main
```

Same endpoints:

* UI: [http://localhost:7860](http://localhost:7860)
* MCP: [http://localhost:7860/gradio_api/mcp/](http://localhost:7860/gradio_api/mcp/)

---

## AI Assist: what it does

When **AI assist is enabled** (`MIND_AI_ASSIST=true` and/or the per-call `use_ai` flag is true):

* `memory_engine.create_memory()` will call `classify_memory()` via OpenRouter. 
* The LLM returns JSON with:

  * `type`: one of `fact`, `preference`, `task`, `journal`, `note`
  * `tags`: list of lowercase tags
  * `importance`: 0.0–1.0
  * `summary`: one-line description
* Mind uses these to fill in missing metadata when you add a memory.

You can disable AI assist by:

* Setting `MIND_AI_ASSIST=false` in `.env`, and
* (If the UI still exposes a “Use AI” checkbox) unchecking it so calls pass `use_ai=False`.

Even with AI assist off, Mind still:

* Stores text
* Computes embeddings via OpenRouter
* Supports semantic search

---

## UI Usage

The UI lives at [http://localhost:7860](http://localhost:7860) and is defined in `mind/ui.py`. 

### 1. Add a memory

1. Go to the **“Add Memory”** tab.
2. Fill in:

   * **Memory text** – what you want Mind to remember.
   * Optional **Tags** – comma-separated list like `work, cursor, project-x`.
   * Optional **Importance** – slider from 0.0–1.0.
3. Click **Save to Mind**.

Under the hood:

* `mind_add_memory` (UI handler + MCP tool) calls `memory_engine.create_memory()`. 
* If AI assist is enabled, the LLM proposes type/tags/importance/summary.
* Mind computes an embedding via OpenRouter and inserts into:

  * `memories` (metadata + raw text)
  * `vec_memories` (embedding) 

A JSON representation of the stored memory is shown in the UI, including `id`, `uuid`, `type`, `tags`, `importance`, timestamps, etc.

### 2. Search memories

1. Go to the **“Search”** tab.
2. Enter a natural-language **Search query**, e.g.:

   * “what did I work on yesterday?”
   * “my Node.js preferences”
3. Optionally adjust **Max results**.
4. Click **Search Mind**.

Under the hood:

* `mind_search_memory` calls `memory_engine.search_memories()` with your query. 

* Mind embeds the query via OpenRouter, then runs a sqlite‑vec search:

  ```sql
  WITH matches AS (
    SELECT rowid, distance
    FROM vec_memories
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT ?
  )
  SELECT m.*, matches.distance
  FROM matches
  JOIN memories m ON m.id = matches.rowid
  WHERE m.deleted_at IS NULL
  ORDER BY matches.distance;
  ```

* Results are returned as JSON, each with a `distance` score (smaller is closer).

### 3. Delete a memory

At the bottom of **Search**:

1. Take note of the numeric `id` of the memory you want to delete.
2. Enter that **Memory id**.
3. Click **Delete**.

Under the hood:

* `mind_delete_memory` calls `memory_engine.delete_memory(id)`. 
* Mind soft-deletes the memory (`deleted_at` set) and removes its embedding from `vec_memories`.

---

## MCP Server

Mind exposes MCP tools via Gradio v6 on:

```text
http://localhost:7860/gradio_api/mcp/
```

This endpoint speaks MCP over **HTTP Stream** transport, not stdio. 

### Available tools (simplified)

The core tools (both in UI and MCP) are:

#### 1️⃣ `mind_add_memory`

```python
async def mind_add_memory(
    text: str,
    tags_text: str | None = None,
    importance: float = 0.5,
)
```

Use when the user says things like:

* “remember that I’m working on Project Aurora with Bun. Use Mind.”
* “use Mind to remember that I need to review onboarding tomorrow.”

Behavior:

* Stores the text as a memory.
* Optionally uses AI assist to classify type/tags/importance/summary.
* Returns the stored memory object, including its `id`.

#### 2️⃣ `mind_search_memory`

```python
async def mind_search_memory(
    query: str,
    max_results: int = 20,
)
```

Use when the user says:

* “use Mind to tell me what I worked on yesterday.”
* “what does Mind remember about Project Aurora?”
* “search Mind for my editor preferences.”

Behavior:

* Embeds `query`, searches `vec_memories`, and returns up to `max_results` closest matches.

#### 3️⃣ `mind_delete_memory`

```python
async def mind_delete_memory(memory_id: int)
```

Use when the user says:

* “remove this memory from Mind.”
* “delete memory 42 from Mind.”

Behavior:

* Soft-deletes the memory, removes its embedding, and returns `{ "deleted_id": 42 }`.

---

## Using Mind from MCP clients

### Why `mcp-remote` is usually required

Mind (via Gradio) speaks MCP over **HTTP Stream**.

Most current MCP clients (Claude Desktop, many Cursor builds) only support **process/stdio** MCP servers. `mcp-remote` bridges that gap:

> MCP client ⇄ stdio ⇄ `mcp-remote` ⇄ HTTP Stream ⇄ Mind

### Install `mcp-remote`

```bash
npm install -g mcp-remote
```

### Example config (Claude Desktop / Cursor style)

```jsonc
{
  "mcpServers": {
    "mind": {
      "command": "mcp-remote",
      "args": ["http://localhost:7860/gradio_api/mcp/"]
    }
  }
}
```

Now you can say:

* “Use Mind to remember that my favourite editor theme is Nord.”
* “Use Mind to tell me what I worked on yesterday.”
* “Use Mind to remove that memory about the old repo.”

`mcp-remote` will:

1. Start as a local process speaking MCP over stdio.
2. Forward those calls to Mind’s HTTP MCP endpoint.
3. Return results back to the client.

### Direct `url` (if your client supports HTTP MCP natively)

Some future clients will support HTTP MCP directly. In those you’d configure:

```jsonc
{
  "mcpServers": {
    "mind": {
      "url": "http://localhost:7860/gradio_api/mcp/"
    }
  }
}
```

But today, most IDE clients still need the `mcp-remote` bridge.

---

## Environment variables (reference)

All handled in `mind/config.py`: 

* `OPENROUTER_API_KEY` (**required**)
* `OPENROUTER_BASE` (default `https://openrouter.ai/api/v1`)
* `MIND_EMBEDDING_MODEL` (default `qwen/qwen3-embedding-8b`)
* `MIND_LLM_MODEL` (default `qwen/qwen-2.5-7b-instruct`)
* `MIND_EMBEDDING_DIM` (default `4096`)
* `SQLITE_VEC_PATH` (default `/usr/local/lib/vec0`)
* `MIND_DATA_DIR` (default `<repo>/data`)
* `MIND_DB_PATH` (default `${MIND_DATA_DIR}/mind.db`)
* `MIND_SERVER_NAME` (default `0.0.0.0`)
* `MIND_SERVER_PORT` (default `7860`)
* `MIND_AI_ASSIST` (default `"true"`)
* `MIND_AUTO_CLUSTER` (default `"true"`, reserved for future use)