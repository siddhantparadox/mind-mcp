from __future__ import annotations

import gradio as gr

from .config import SERVER_NAME, SERVER_PORT
from .db import init_db
from .ui import APP_THEME, CUSTOM_CSS, build_ui


def create_app() -> gr.Blocks:
    init_db()
    with gr.Blocks(title="Mind") as demo:
        build_ui()
    return demo


demo = create_app()

if __name__ == "__main__":
    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        mcp_server=True,
        theme=APP_THEME,
        css=CUSTOM_CSS,
    )
