"""Entry file for NiceGUI's `user` test fixture (see test_api_key_dialog.py):
it re-runs this per test, which re-registers the "/" and "/admin" pages."""

import importlib

import app.ui.admin
import app.ui.shared_page
import app.ui.pages

importlib.reload(app.ui.pages)

from nicegui import ui

app.ui.admin.register_admin_page()
app.ui.shared_page.register_shared_page()

ui.run(storage_secret="test-secret")
