from __future__ import annotations

import gradio as gr

from . import memory_engine

# Minimal, modern dark theme
APP_THEME = gr.themes.Base(
    primary_hue="cyan",
    secondary_hue="slate",
    neutral_hue="slate",
    font=["Space Grotesk", "system-ui", "sans-serif"],
)

# Custom CSS: minimal, subtle animations, clean cards
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

body {
  background: #050812;
  color: #e2e8f0;
}

.gradio-container {
  font-family: 'Space Grotesk', system-ui, -apple-system, sans-serif;
  max-width: 1100px !important;
  margin: 0 auto !important;
  padding: 24px 24px 40px !important;
}

/* Smooth transitions everywhere */
*,
*::before,
*::after {
  transition:
    background-color 150ms ease,
    border-color 150ms ease,
    color 150ms ease,
    box-shadow 150ms ease,
    transform 150ms ease;
}

/* Hero header */
.mind-hero {
  background: rgba(15, 23, 42, 0.9);
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  padding: 16px 18px;
  margin-bottom: 12px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.55);
}

.mind-hero h1 {
  margin: 0;
  font-size: 1.4rem;
  letter-spacing: -0.03em;
}

.mind-hero-sub {
  margin: 4px 0 0;
  font-size: 0.9rem;
  color: #94a3b8;
}

/* Pills */
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 11px;
  border-radius: 999px;
  background: rgba(34, 211, 238, 0.06);
  border: 1px solid rgba(34, 211, 238, 0.2);
  color: #a5f3fc;
  font-weight: 500;
  font-size: 0.82rem;
}

/* Tabs */
.gradio-container .tabs {
  margin-top: 10px;
}

.gradio-container .tab-nav button {
  border-radius: 999px !important;
  padding: 7px 14px !important;
  font-size: 0.9rem !important;
}

.gradio-container .tab-nav button[aria-selected="true"] {
  background: rgba(8, 145, 178, 0.16) !important;
  color: #e0f2fe !important;
  border-color: rgba(34, 211, 238, 0.4) !important;
}

/* Cards */
.mind-card {
  background: rgba(15, 23, 42, 0.96);
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.32);
  padding: 16px 16px 14px;
  box-shadow: 0 14px 40px rgba(15, 23, 42, 0.7);
}

.mind-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.9);
}

/* Typography */
.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.section-help {
  font-size: 0.85rem;
  color: #94a3b8;
  margin-bottom: 8px;
}

/* Inputs */
.gr-textbox textarea,
.gradio-container input,
.gradio-container select {
  background: rgba(15, 23, 42, 0.9) !important;
  border-radius: 10px !important;
  border: 1px solid rgba(148, 163, 184, 0.5) !important;
  color: #e5e7eb !important;
}

.gr-textbox textarea:focus,
.gradio-container input:focus,
.gradio-container select:focus {
  border-color: rgba(34, 211, 238, 0.8) !important;
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.3);
}

/* Buttons */
.gr-button {
  border-radius: 999px !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em;
  padding: 8px 14px !important;
}

.gr-button.primary {
  background: linear-gradient(135deg, #22d3ee, #0e7490) !important;
  border: none !important;
  color: #0f172a !important;
}

.gr-button.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 30px rgba(34, 211, 238, 0.35);
}

.gr-button.secondary {
  background: rgba(15, 23, 42, 0.95) !important;
  border: 1px solid rgba(148, 163, 184, 0.6) !important;
  color: #e2e8f0 !important;
}

/* JSON output container */
.gr-json {
  max-height: 260px;
  overflow: auto;
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
    """
    Store long-term memory in the user's Mind.

    Use this tool when the user says things like:
    - "remember that ..."
    - "save this in Mind"
    - "use Mind to remember that I need to look at X"
    """
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
    """
    Search the user's Mind for relevant memories.

    Use this tool when the user asks things like:
    - "use Mind to tell me what I worked on yesterday"
    - "what does Mind remember about X?"
    """
    return await memory_engine.search_memories(
        query=query,
        top_k=top_k,
        type_filter=type_filter or None,
        tags=_split_tags(tags_text),
    )


async def delete_handler(memory_id: int):
    """
    Delete (soft-delete) a memory from Mind by id.

    Use this tool when the user says things like:
    - "remove this from Mind"
    - "delete memory 42 from Mind"
    """
    memory_engine.delete_memory(memory_id)
    return {"deleted_id": memory_id}


def build_ui():
    # Hero
    gr.HTML(
        """
        <div class="mind-hero">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
            <div>
              <h1>Mind</h1>
              <p class="mind-hero-sub">
                Local, shared long‑term memory for your AI agents — one endpoint for UI + MCP.
              </p>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;">
              <span class="pill">SQLite + sqlite‑vec</span>
              <span class="pill">OpenRouter Embeddings</span>
              <span class="pill">Gradio v6 MCP</span>
            </div>
          </div>
        </div>
        """
    )

    with gr.Tabs():
        # --- Add Memory ---
        with gr.Tab("Add"):
            with gr.Row():
                with gr.Column(scale=2):
                    with gr.Group(elem_classes=["mind-card"]):
                        gr.Markdown("##### Capture a new memory", elem_classes=["section-title"])
                        gr.Markdown(
                            "Describe anything you want Mind to remember. "
                            "Optionally let AI structure it into type, tags, and importance.",
                            elem_classes=["section-help"],
                        )
                        memory_text = gr.Textbox(
                            label="Memory text",
                            lines=7,
                            placeholder="What do you want Mind to remember?",
                        )
                        summary = gr.Textbox(
                            label="Summary (optional)",
                            placeholder="Short one-liner for quick recall / clustering",
                        )

                    with gr.Group(elem_classes=["mind-card"]):
                        gr.Markdown("###### Metadata", elem_classes=["section-title"])
                        type_choice = gr.Dropdown(
                            ["auto", "fact", "preference", "task", "journal", "note"],
                            value="auto",
                            label="Type",
                        )
                        tags_text = gr.Textbox(
                            label="Tags (comma-separated)",
                            placeholder="work, cursor, project-x",
                        )
                        importance = gr.Slider(
                            label="Importance",
                            minimum=0.0,
                            maximum=1.0,
                            step=0.05,
                            value=0.5,
                            info="0 = low, 1 = critical",
                        )
                        use_ai = gr.Checkbox(
                            label="Use AI to auto-fill metadata",
                            value=True,
                        )
                        with gr.Accordion("Advanced IDs (optional)", open=False):
                            user_id = gr.Textbox(label="User ID", placeholder="optional")
                            agent_id = gr.Textbox(label="Agent ID", placeholder="optional")
                            conversation_id = gr.Textbox(label="Conversation ID", placeholder="optional")

                        add_btn = gr.Button("Save to Mind", elem_classes=["primary"])

                with gr.Column(scale=1):
                    with gr.Group(elem_classes=["mind-card"]):
                        gr.Markdown("###### Result", elem_classes=["section-title"])
                        gr.Markdown(
                            "Mind will store the structured memory here. "
                            "This is the same JSON shape agents see via MCP.",
                            elem_classes=["section-help"],
                        )
                        add_output = gr.JSON(label="", show_label=False)

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

        # --- Search ---
        with gr.Tab("Search"):
            with gr.Row():
                with gr.Column(scale=2):
                    with gr.Group(elem_classes=["mind-card"]):
                        gr.Markdown("##### Search Mind", elem_classes=["section-title"])
                        query = gr.Textbox(
                            label="Search query",
                            placeholder="e.g., what did I decide about onboarding?",
                        )
                        top_k = gr.Slider(
                            label="Max results",
                            minimum=1,
                            maximum=100,
                            step=1,
                            value=20,
                        )
                        type_filter = gr.Dropdown(
                            ["", "fact", "preference", "task", "journal", "note"],
                            value="",
                            label="Type filter",
                        )
                        tags_filter = gr.Textbox(
                            label="Tags filter (comma-separated)",
                            placeholder="work, sprint, docs",
                        )
                        search_btn = gr.Button("Search Mind", elem_classes=["primary"])

                with gr.Column(scale=1):
                    with gr.Group(elem_classes=["mind-card"]):
                        gr.Markdown("###### Matches", elem_classes=["section-title"])
                        search_output = gr.JSON(label="", show_label=False)

            search_btn.click(
                fn=search_handler,
                inputs=[query, top_k, type_filter, tags_filter],
                outputs=search_output,
                api_name="mind_search_memory",
            )

            with gr.Group(elem_classes=["mind-card"]):
                gr.Markdown("###### Delete by ID", elem_classes=["section-title"])
                delete_id = gr.Number(label="Memory id", precision=0)
                delete_btn = gr.Button("Delete", elem_classes=["secondary"])
                delete_output = gr.JSON(label="", show_label=False)
                delete_btn.click(
                    fn=delete_handler,
                    inputs=[delete_id],
                    outputs=delete_output,
                    api_name="mind_delete_memory",
                )

        # --- Future tabs ---
        with gr.Tab("Clusters"):
            with gr.Group(elem_classes=["mind-card"]):
                gr.Markdown(
                    "Clusters UI coming soon — Mind already has a schema for clusters and relations. "
                    "Next step is grouping similar memories into topics and summarising them here.",
                    elem_classes=["section-help"],
                )

        with gr.Tab("Settings"):
            with gr.Group(elem_classes=["mind-card"]):
                gr.Markdown(
                    "Settings UI coming soon — this will surface AI assist, auto-cluster, model picks, "
                    "and export/import for your `mind.db`.",
                    elem_classes=["section-help"],
                )
