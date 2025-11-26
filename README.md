# Mind

Local, shared long‑term memory for your AI agents. Mind runs entirely in Docker, stores everything in a single SQLite database with sqlite‑vec for vector search, exposes a Gradio v6 UI for humans, and an MCP server for agents.

## Features

- SQLite + sqlite‑vec vectors (vec0 virtual tables)
- Embeddings via OpenRouter (default: `qwen/qwen3-embedding-8b`)
- Optional LLM assist for classification/summaries (default: `qwen/qwen-2.5-7b-instruct`)
- Gradio v6 UI + MCP endpoint on the same port
- One-container Docker setup with persistent volume for data

## Quick start

1) Set your OpenRouter key in `.env`:

```
OPENROUTER_API_KEY=sk-or-...
```

2) Build and run:

```
docker compose up --build
```

3) Open the UI:

- UI: http://localhost:7860
- MCP endpoint: http://localhost:7860/gradio_api/mcp/

Data is persisted in the `mind_data` volume (`/app/data/mind.db` inside the container).

## Using the UI

- Add Memory: type text, optional summary, type/tags, importance, then “Save to Mind”. AI assist can fill metadata.
- Search: enter a query, optional type/tags filters, then “Search Mind”.
- Delete: provide a memory id and click “Delete”.

## MCP client setup

Point your MCP client to the Mind server URL:

```
http://localhost:7860/gradio_api/mcp/
```

Available tools (auto-exposed by Gradio):

- `mind_add_memory(text, type, tags, importance, user_id, agent_id, conversation_id, summary, use_ai)`
- `mind_search_memory(query, top_k, type, tags, since, until)`
- `mind_delete_memory(id)`

### MCP connectivity

Gradio’s MCP endpoint supports the HTTP Stream transport. If your client speaks HTTP Stream, point it directly to:
```
http://localhost:7860/gradio_api/mcp/
```

Example (Claude Desktop / Cursor style):
```json
{
  "mcpServers": {
    "mind": {
      "url": "http://localhost:7860/gradio_api/mcp/"
    }
  }
}
```

If your client only does SSE, use the `mcp-remote` bridge:

1) Install globally:
```
npm install -g mcp-remote
```
1) Configure your client to run the proxy:
```json
{
  "mcpServers": {
    "mind": {
      "command": "mcp-remote",
      "args": ["http://localhost:7860/gradio_api/mcp/"]
    }
  }
}
```
If PATH is an issue, use the full path to `mcp-remote` or `npx mcp-remote` instead of `mcp-remote`.

Tools exposed: `mind_add_memory`, `mind_search_memory`, `mind_delete_memory`.

### Example: Claude Desktop / Cursor

Add to your MCP client config:

```json
{
  "mcpServers": {
    "mind": {
      "url": "http://localhost:7860/gradio_api/mcp/"
    }
  }
}
```

Then prompts like:
- “Use Mind to remember that I’m working on Project X with Qwen.”
- “Use Mind to tell me what I decided about onboarding.”

## Environment variables

See `.env` for defaults:

- `OPENROUTER_API_KEY` (required)
- `MIND_EMBEDDING_MODEL` (default `qwen/qwen3-embedding-8b`)
- `MIND_LLM_MODEL` (default `google/gemini-2.5-flash-lite-preview-09-2025`)
- `MIND_EMBEDDING_DIM` (default `4096`)
- `SQLITE_VEC_PATH` (default `/usr/local/lib/vec0`)
- `MIND_DATA_DIR`, `MIND_DB_PATH` (default `/app/data/mind.db`)
- `MIND_SERVER_NAME`, `MIND_SERVER_PORT` (default `0.0.0.0:7860`)
- `MIND_AI_ASSIST`, `MIND_AUTO_CLUSTER` toggles

## sqlite-vec note

The Dockerfile installs sqlite-vec via the official script. If you need offline builds, drop a prebuilt `vec0.so` at `./sqlite-vec/vec0.so` before building.

## Development

Run locally (non-Docker):

```
pip install -r requirements.txt
python -m mind.main
```

The UI runs on http://localhost:7860; MCP is at `/gradio_api/mcp/`.
