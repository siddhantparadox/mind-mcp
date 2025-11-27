from __future__ import annotations

import gradio as gr

from . import memory_engine

# Theme and CSS (same look, simpler logic)
APP_THEME = gr.themes.Base(
    primary_hue="teal",
    secondary_hue="stone",
    neutral_hue="slate",
    font=["Space Grotesk", "sans-serif"],
)

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

body {
  background: radial-gradient(circle at 20% 20%, #0f1c2b, #0b1624 35%, #0a1320 70%, #0a101c);
  color: #e6edf6;
}

.gradio-container {
  font-family: 'Space Grotesk', system-ui, -apple-system, sans-serif;
  background: transparent;
  color: #e6edf6;
}

.mind-hero {
  background: rgba(22, 34, 48, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: none;
}

.mind-hero h1 {
  margin: 0;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(12, 138, 138, 0.25);
  color: #c8f3ef;
  font-weight: 600;
  font-size: 0.9rem;
}

.mind-card {
  background: rgba(17, 28, 42, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 14px;
  box-shadow: none;
}

.caption {
  color: #cbd5e1;
  font-size: 0.95rem;
  margin: 6px 0 10px;
}

.gr-button {
  border-radius: 10px !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em;
}

.gr-button.primary {
  background: linear-gradient(135deg, #0fb3b3, #0a7c7c);
  border: none;
  color: #fff;
}

.gr-button.secondary {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e6edf6;
}

.gr-textbox textarea {
  background: rgba(14, 24, 36, 0.9);
  color: #e6edf6;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
}

.gradio-container input,
.gradio-container select,
.gradio-container .gr-number input,
.gradio-container .gr-dropdown input,
.gradio-container .gr-slider input {
  background: rgba(14, 24, 36, 0.9);
  color: #e6edf6;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.gradio-container .tabitem {
  padding-top: 6px;
}
"""


def _split_tags(text: str | None) -> list[str] | None:
    """Split a comma-separated tags string into a clean list."""
    if not text:
        return None
    return [t.strip() for t in text.split(",") if t.strip()]


# ---------- MCP tool functions (minimal parameter sets) ----------


async def mind_add_memory(
    text: str,
    tags_text: str | None = None,
    importance: float = 0.5,
):
    """
    Store a new long-term memory in Mind.

    Use this tool whenever the user says things like:
    - "remember that ..."
    - "save this in Mind"
    - "use Mind to remember that I need to look at X"

    Args:
        text: Natural-language text to remember.
        tags_text: Optional comma-separated tags (e.g. "work, aurora").
        importance: Optional importance score between 0.0 (low) and 1.0 (critical).

    Returns:
        The stored memory record (including id, uuid, type, tags, importance, etc.).
    """
    return await memory_engine.create_memory(
        text=text,
        tags=_split_tags(tags_text),
        importance=importance,
        # Let the engine + MIND_AI_ASSIST handle type/tags/summary inference.
        source="ui",
        use_ai=True,
    )


async def mind_search_memory(
    query: str,
    max_results: int = 20,
):
    """
    Search Mind for relevant memories using semantic similarity.

    Use this tool when the user asks things like:
    - "use Mind to tell me what I worked on yesterday"
    - "what does Mind remember about Project Aurora?"
    - "search Mind for my editor preferences"

    Args:
        query: Natural-language query describing what to retrieve.
        max_results: Maximum number of memories to return (1–100).

    Returns:
        A list of matching memories, each with a `distance` score.
    """
    # We just pass through to the engine's semantic search.
    return await memory_engine.search_memories(
        query=query,
        top_k=max_results,
    )


async def mind_delete_memory(memory_id: int):
    """
    Delete (soft-delete) a memory from Mind by its numeric id.

    Use this tool when the user clearly wants to forget something, e.g.:
    - "remove this from Mind"
    - "delete that old memory from Mind"
    - "delete memory 42 from Mind"

    Args:
        memory_id: The numeric id of the memory to delete.

    Returns:
        A small dict confirming which id was deleted.
    """
    memory_engine.delete_memory(memory_id)
    return {"deleted_id": memory_id}


# ---------- UI wiring ----------


def build_ui():
    """Build the Gradio Blocks UI for Mind (and expose MCP tools)."""
    gr.HTML(
        """
        <div class="mind-hero">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
            <div>
              <h1>Mind</h1>
              <p class="caption" style="margin:4px 0 10px;">
                Local, shared long‑term memory for your agents. UI + MCP on one endpoint.
              </p>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <span class="pill">SQLite + sqlite‑vec</span>
              <span class="pill">Gradio v6 MCP</span>
            </div>
          </div>
        </div>
        """
    )

    gr.Markdown(
        "##### How to use\n"
        "- **Add**: enter text (and optional tags/importance), click **Save to Mind**.\n"
        "- **Search**: enter a natural-language query, click **Search Mind**.\n"
        "- **Delete**: use the numeric `id` from search results and click **Delete**.\n"
        "- **MCP**: call `mind_add_memory`, `mind_search_memory`, `mind_delete_memory` from your MCP client.",
        elem_classes=["caption", "mind-card"],
    )

    with gr.Tabs():
        # ---- Add Memory tab ----
        with gr.Tab("Add Memory"):
            with gr.Column(elem_classes=["mind-card"]):
                gr.Markdown("#### Capture a new memory", elem_classes=["caption"])
                memory_text = gr.Textbox(
                    label="Memory text",
                    lines=8,
                    placeholder="What do you want Mind to remember?",
                )
                tags_text = gr.Textbox(
                    label="Tags (optional, comma-separated)",
                    placeholder="work, aurora, cursor",
                )
                importance = gr.Slider(
                    label="Importance",
                    minimum=0.0,
                    maximum=1.0,
                    step=0.05,
                    value=0.5,
                    info="0 = low, 1 = critical",
                )
                add_btn = gr.Button("Save to Mind", elem_classes=["primary"])
                add_output = gr.JSON(label="Created memory")

                add_btn.click(
                    fn=mind_add_memory,
                    inputs=[memory_text, tags_text, importance],
                    outputs=add_output,
                    api_name="mind_add_memory",
                )

        # ---- Search tab ----
        with gr.Tab("Search"):
            with gr.Column(elem_classes=["mind-card"]):
                gr.Markdown("#### Find what Mind knows", elem_classes=["caption"])
                query = gr.Textbox(
                    label="Search query",
                    placeholder="e.g., what did I work on yesterday?",
                )
                max_results = gr.Slider(
                    label="Max results",
                    minimum=1,
                    maximum=100,
                    step=1,
                    value=20,
                )
                search_btn = gr.Button("Search Mind", elem_classes=["primary"])
                search_output = gr.JSON(label="Matches", show_label=False)

                search_btn.click(
                    fn=mind_search_memory,
                    inputs=[query, max_results],
                    outputs=search_output,
                    api_name="mind_search_memory",
                )

            with gr.Column(elem_classes=["mind-card"]):
                gr.Markdown("#### Delete a memory", elem_classes=["caption"])
                delete_id = gr.Number(label="Memory id", precision=0)
                delete_btn = gr.Button("Delete", elem_classes=["secondary"])
                delete_output = gr.JSON(label="Delete status", show_label=False)

                delete_btn.click(
                    fn=mind_delete_memory,
                    inputs=[delete_id],
                    outputs=delete_output,
                    api_name="mind_delete_memory",
                )

        # ---- Future tabs ----
        with gr.Tab("Clusters"):
            gr.Markdown(
                "Clusters UI coming soon. Mind already has schema support for clusters and relations; "
                "a future version will group related memories here.",
                elem_classes=["mind-card"],
            )

        with gr.Tab("Settings"):
            gr.Markdown(
                "Settings UI coming soon. This will surface AI assist toggles, model choices, "
                "and export/import for your `mind.db`.",
                elem_classes=["mind-card"],
            )
