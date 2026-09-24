"""
Vercel entrypoint. Vercel's Python runtime auto-detects a FastAPI/ASGI
app named `app` in this file and serves it as a serverless function.
Every request to /api/* (per the root vercel.json routing) lands here.
"""

import sys
import os

# Make "app" package (backend/app/...) importable when this file runs from
# backend/api/ inside the Vercel build.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa: E402  (re-exported for Vercel)
