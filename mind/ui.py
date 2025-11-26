from __future__ import annotations

import gradio as gr

from . import memory_engine

# Theme and CSS for a brighter, intentional look.
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

.mind-grid {
  gap: 14px;
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

.gradio-container .tabitem {
  padding-top: 6px;
}
"""


def _split_tags(text: str | None) -> list[str] | None:
    if not text:
        return None
    return [t.strip() for t in text.split(",") if t.strip()]


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
):
    """Store long-term memory in the user's Mind."""
    return await memory_engine.create_memory(
        text=text,
        type_=type_choice if type_choice != "auto" else None,
        tags=_split_tags(tags_text),
        importance=importance,
        user_id=user_id or None,
        agent_id=agent_id or None,
        conversation_id=conversation_id or None,
        summary=summary or None,
        source="ui",
        use_ai=use_ai,
    )


async def search_handler(
    query: str = "",
    top_k: int = 20,
    type_filter: str = "",
    tags_text: str | None = None,
):
    """Search the user's Mind for relevant memories."""
    return await memory_engine.search_memories(
        query=query,
        top_k=top_k,
        type_filter=type_filter or None,
        tags=_split_tags(tags_text),
    )


async def delete_handler(memory_id: int):
    """Delete (soft) a memory from Mind by id."""
    memory_engine.delete_memory(memory_id)
    return {"deleted_id": memory_id}


def build_ui():
    gr.HTML(
        """
        <div class="mind-hero">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
            <div>
              <h1>Mind</h1>
              <p class="caption" style="margin:4px 0 10px;">Local, shared long-term memory for your agents. UI + MCP on one endpoint.</p>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <span class="pill">SQLite + sqlite-vec</span>
              <span class="pill">Gradio v6 MCP</span>
            </div>
          </div>
        </div>
        """
    )

    gr.Markdown(
        "##### How to use\n"
        "- Add: fill text, adjust metadata, click **Save to Mind**.\n"
        "- Search: enter a query and optional filters, click **Search Mind**.\n"
        "- Delete: provide a memory id and click **Delete**.\n"
        "- MCP: point your client to `http://localhost:7860/gradio_api/mcp/` to call `mind_add_memory`, `mind_search_memory`, `mind_delete_memory`.",
        elem_classes=["caption", "mind-card"],
    )

    with gr.Tabs():
        with gr.Tab("Add Memory"):
            with gr.Column(elem_classes=["mind-card"]):
                gr.Markdown("#### Capture a new memory", elem_classes=["caption"])
                memory_text = gr.Textbox(
                    label="Memory text",
                    lines=8,
                    placeholder="What do you want Mind to remember?",
                )
                summary = gr.Textbox(label="Summary (optional)", placeholder="Short one-liner for clusters")
                type_choice = gr.Dropdown(
                    ["auto", "fact", "preference", "task", "journal", "note"],
                    value="auto",
                    label="Type",
                )
                tags_text = gr.Textbox(label="Tags (comma-separated)", placeholder="work, cursor, project-x")
                importance = gr.Slider(
                    label="Importance", minimum=0.0, maximum=1.0, step=0.05, value=0.5, info="0 = low, 1 = critical"
                )
                use_ai = gr.Checkbox(label="Use AI to auto-fill fields", value=True)
                with gr.Accordion("Advanced IDs (optional)", open=False):
                    user_id = gr.Textbox(label="User ID", placeholder="optional")
                    agent_id = gr.Textbox(label="Agent ID", placeholder="optional")
                    conversation_id = gr.Textbox(label="Conversation ID", placeholder="optional")
                add_btn = gr.Button("Save to Mind", elem_classes=["primary"])
                add_output = gr.JSON(label="Created memory")
                add_btn.click(
                    fn=add_memory_handler,
                    inputs=[
                        memory_text,
                        type_choice,
                        tags_text,
                        importance,
                        use_ai,
                        user_id,
                        agent_id,
                        conversation_id,
                        summary,
                    ],
                    outputs=add_output,
                    api_name="mind_add_memory",
                )

        with gr.Tab("Search"):
            with gr.Column(elem_classes=["mind-card"]):
                gr.Markdown("#### Find what Mind knows", elem_classes=["caption"])
                query = gr.Textbox(label="Search query", placeholder="e.g., what did I decide about onboarding?")
                top_k = gr.Slider(label="Max results", minimum=1, maximum=100, step=1, value=20)
                type_filter = gr.Dropdown(
                    ["", "fact", "preference", "task", "journal", "note"], value="", label="Type filter"
                )
                tags_filter = gr.Textbox(label="Tags filter (comma-separated)", placeholder="work, sprint, docs")
                search_btn = gr.Button("Search Mind", elem_classes=["primary"])
                search_output = gr.JSON(label="Matches", show_label=False)
                search_btn.click(
                    fn=search_handler,
                    inputs=[query, top_k, type_filter, tags_filter],
                    outputs=search_output,
                    api_name="mind_search_memory",
                )

            with gr.Column(elem_classes=["mind-card"]):
                gr.Markdown("#### Delete a memory", elem_classes=["caption"])
                delete_id = gr.Number(label="Memory id", precision=0)
                delete_btn = gr.Button("Delete", elem_classes=["secondary"])
                delete_output = gr.JSON(label="Delete status", show_label=False)
                delete_btn.click(
                    fn=delete_handler,
                    inputs=[delete_id],
                    outputs=delete_output,
                    api_name="mind_delete_memory",
                )

        with gr.Tab("Clusters"):
            gr.Markdown("Clusters UI coming soon.", elem_classes=["mind-card"])

        with gr.Tab("Settings"):
            gr.Markdown("Settings UI coming soon.", elem_classes=["mind-card"])
