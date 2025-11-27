Here’s a cleaned‑up, up‑to‑date README you can drop straight into the repo, followed by a concrete “what’s next” for the MCP server.

---

## 🔹 Updated `README.md`

````markdown
# Mind 🧠

**Mind** is a local, shared long‑term memory service for your AI agents.

- Fully local, Dockerized
- Stores everything in a single **SQLite** database with **sqlite‑vec** for vector search
- Uses **OpenRouter** for embeddings + optional LLM assist
- Exposes a **Gradio v6 UI** for humans
- Exposes an **MCP server** on the same port for agents (Claude, Cursor, etc.)

Everything stays on your machine.

---

## Architecture

- **Database:** SQLite with [`sqlite-vec`](https://github.com/asg017/sqlite-vec) as a `vec0` virtual table for embeddings  
- **Schema:** `memories`, `vec_memories`, `clusters`, `memory_relations` :contentReference[oaicite:0]{index=0}  
- **Embeddings:** OpenRouter `/embeddings` (`MIND_EMBEDDING_MODEL`, default `qwen/qwen3-embedding-8b`) :contentReference[oaicite:1]{index=1}  
- **LLM assist:** OpenRouter `/chat/completions` (`MIND_LLM_MODEL`, default `qwen/qwen-2.5-7b-instruct` unless overridden in `.env`) :contentReference[oaicite:2]{index=2}  
- **UI & MCP:** Gradio v6 `Blocks`, launched with `mcp_server=True` at `/gradio_api/mcp/` :contentReference[oaicite:3]{index=3}  

---

## Prerequisites

You can use Mind entirely via Docker (recommended).

### Required

- **OpenRouter account + API key**  
  - Create an account on OpenRouter  
  - Get an API key and set `OPENROUTER_API_KEY` in `.env`

- **Docker & Docker Compose**  
  - Docker 24+ recommended  
  - Compose v2+ (usually bundled with Docker Desktop)

### Optional (for MCP clients that need a bridge)

If your MCP client only supports **local stdio servers** (e.g. Claude Desktop, most Cursor builds right now), you’ll also want:

- **Node.js** (20+ recommended)
- `mcp-remote` installed globally:

  ```bash
  npm install -g mcp-remote
````

`mcp-remote` is a tiny CLI that lets stdio‑only MCP clients connect to remote HTTP MCP servers like Mind. ([Nicola Iarocci][1])

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

MIND_AI_ASSIST=true
MIND_AUTO_CLUSTER=true
```

Notes:

* `OPENROUTER_API_KEY` **must** be set.
* In code, the default LLM model is `qwen/qwen-2.5-7b-instruct`; the example `.env` overrides it to a Gemini model via OpenRouter. 

---

## Running Mind

### Docker (recommended)

Build & run:

```bash
docker compose up --build
```

This:

* Builds the image (installs python deps + `sqlite-vec`, sets up `/app/data`) 
* Starts the Mind server at `http://localhost:7860`
* Creates/uses the `mind_data` volume for persistent storage

Access:

* **UI:** [http://localhost:7860](http://localhost:7860)
* **MCP endpoint:** [http://localhost:7860/gradio_api/mcp/](http://localhost:7860/gradio_api/mcp/)

Data:

* SQLite DB lives at `/app/data/mind.db` inside the container
* Bound to the `mind_data` Docker volume 

### Local (non‑Docker) dev

If you want to run it directly:

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY=sk-or-...
python -m mind.main
```

Same endpoints:

* UI: [http://localhost:7860](http://localhost:7860)
* MCP: [http://localhost:7860/gradio_api/mcp/](http://localhost:7860/gradio_api/mcp/)

---

## UI Usage

The UI lives at `http://localhost:7860` and is built in `mind/ui.py`. 

### 1. Add a memory

1. Go to the **“Add Memory”** tab.
2. Fill in:

   * **Memory text** – the thing you want Mind to remember.
   * Optional **summary** – short one‑liner.
   * **Type** – `auto`, `fact`, `preference`, `task`, `journal`, or `note`.
   * **Tags** – comma-separated list like `work, cursor, project-x`.
   * **Importance** – 0.0–1.0 (0 = low, 1 = critical).
   * Optionally toggle **“Use AI to auto‑fill fields”** (if on, Mind will use the LLM to propose type/tags/importance/summary).
   * Optional advanced fields:

     * `user_id`, `agent_id`, `conversation_id`
3. Click **Save to Mind**.

Under the hood:

* `add_memory_handler` calls `memory_engine.create_memory`, which:

  * Optionally calls `classify_memory()` via OpenRouter for metadata.
  * Calls `embed_texts()` with `MIND_EMBEDDING_MODEL` via OpenRouter. 
  * Inserts into `memories` + `vec_memories`. 

A JSON representation of the stored memory is shown in the UI:

```jsonc
{
  "id": 1,
  "uuid": "c7a8f...",
  "user_id": null,
  "agent_id": null,
  "source": "ui",
  "type": "fact",
  "text": "I am working on Project Aurora using Cursor and Bun.",
  "summary": "Working on Project Aurora using Cursor and Bun.",
  "tags": ["project", "aurora", "cursor", "bun"],
  "importance": 0.8,
  "conversation_id": null,
  "cluster_id": null,
  "created_at": 1732000000,
  "updated_at": 1732000000,
  "last_accessed_at": null,
  "deleted_at": null,
  "extra_json": null
}
```

(If retrieved via search you’ll also see a `distance` field.)

### 2. Search memories

1. Go to the **“Search”** tab.
2. Fill:

   * **Search query** – natural language, e.g. “what am I working on with Bun?”.
   * **Max results** – 1–100.
   * Optional **Type filter** – `fact`, `preference`, `task`, `journal`, `note`.
   * Optional **Tags filter** – comma separated, e.g. `work, aurora`.
3. Click **Search Mind**.

Under the hood:

* `search_handler` calls `memory_engine.search_memories()`, which: 

  * Embeds the query via OpenRouter.
  * Uses sqlite‑vec:

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
    WHERE m.deleted_at IS NULL AND ...filters...
    ORDER BY matches.distance;
    ```
  * Converts rows into JSON-friendly dicts.

The UI shows an array of memory objects with `distance` included.

### 3. Delete a memory

At the bottom of **Search**:

1. Enter a numeric **Memory id** (the integer `id` field).
2. Click **Delete**.

Under the hood:

* `delete_handler` calls `memory_engine.delete_memory(id)`. 
* This sets `deleted_at` on the row and removes the embedding from `vec_memories`.

---

## MCP Server

Mind exposes MCP tools via **Gradio v6** on:

```text
http://localhost:7860/gradio_api/mcp/
```

This endpoint speaks **MCP over HTTP Stream**, not stdio. 

### Available tools

Gradio maps the following functions in `mind/ui.py` to MCP tools: 

#### 1️⃣ `mind_add_memory`

Backed by `add_memory_handler`:

```python
async def add_memory_handler(
    text: str,
    type_choice: str = "auto",
    tags_text: str | None = None,
    importance: float = 0.5,
    use_ai: bool = True,
    user_id: str | None = None,
    agent_id: str | None = None,
    conversation_id: str | None = None,
    summary: str | None = None,
)
```

Usage (natural language):

* “Remember that I’m working on Project Aurora with Bun. Use Mind.”
* “Use Mind to remember that I need to review the onboarding doc tomorrow.”

Behavior:

* Optionally calls the LLM to classify type/tags/importance/summary (if `use_ai=true` and you left fields blank).
* Embeds the text and persists to SQLite + sqlite‑vec.
* Returns the full stored memory object (same shape as in the UI).

#### 2️⃣ `mind_search_memory`

Backed by `search_handler`:

```python
async def search_handler(
    query: str = "",
    top_k: int = 20,
    type_filter: str = "",
    tags_text: str | None = None,
)
```

Usage:

* “Use Mind to tell me what I worked on yesterday.”
* “Use Mind to fetch my Node.js preferences.”

Behavior:

* Embeds `query`, vector-searches `vec_memories`, applies type/tags filters, and returns an array of memory objects, each with a `distance` score. 

#### 3️⃣ `mind_delete_memory`

Backed by `delete_handler`:

```python
async def delete_handler(memory_id: int)
```

Usage:

* “Remove memory 42 from Mind.”
* “Delete this memory from Mind.” (host model needs to resolve which ID.)

Behavior:

* Soft deletes the memory and removes its embedding.

---

## Using Mind from MCP clients

### Why `mcp-remote` is usually required right now

Mind (via Gradio) speaks MCP over **HTTP Stream**.

Many MCP clients today (Claude Desktop, a lot of Cursor versions) only know how to talk to **local stdio MCP servers**, not HTTP Stream servers. That’s why you need the `mcp-remote` bridge. ([Nicola Iarocci][1])

`mcp-remote`:

* runs as a local process (stdio)
* forwards MCP messages over HTTP to `http://localhost:7860/gradio_api/mcp/`

So the flow is:

> MCP client ⇄ stdio ⇄ `mcp-remote` ⇄ HTTP Stream ⇄ Mind

### Install `mcp-remote`

```bash
npm install -g mcp-remote
```

### Example: Claude Desktop / Cursor config

In your MCP config file (varies per client), add:

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

Then you can say to your agent:

* “Use Mind to remember that my favorite editor theme is Nord.”
* “Use Mind to tell me what I worked on yesterday.”
* “Use Mind to remove that memory about the old repo.”

The client will:

1. Spawn `mcp-remote` (local process)
2. `mcp-remote` connects to Mind’s HTTP MCP endpoint
3. Tools `mind_add_memory`, `mind_search_memory`, `mind_delete_memory` become available

### Direct `url` (only if your client supports HTTP Stream natively)

Some future clients (e.g. ChatGPT desktop, newer MCP hosts) will speak HTTP Stream natively. In those, you’ll be able to configure Mind like:

```jsonc
{
  "mcpServers": {
    "mind": {
      "url": "http://localhost:7860/gradio_api/mcp/"
    }
  }
}
```

But as of now, most desktop IDE clients still need the `mcp-remote` form.

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
* `MIND_AUTO_CLUSTER` (default `"true"`; currently reserved for future clustering)

---

## Development notes

* Schema is created on startup via `init_db()` in `mind/db.py`. 
* Core operations (`create_memory`, `search_memories`, `update_memory`, `delete_memory`, `get_memory`) live in `mind/memory_engine.py`. 
* LLM helpers and embedding helpers are in `mind/llm.py` and `mind/embeddings.py`. 

Contributions / ideas are welcome, especially around clustering and graph-based memory.

````

---