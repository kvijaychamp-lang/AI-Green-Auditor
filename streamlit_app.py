"""Dedicated Streamlit launcher.

Use this file to run the UI without any API entrypoint ambiguity.
"""

from frontend.app_ui import render_main_page

render_main_page()
