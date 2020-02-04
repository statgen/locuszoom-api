#!/usr/bin/env python3
import os
from locuszoom.api import create_app

app = create_app()
app.run(
  host=os.environ.get("LZAPI_HOST", "127.0.0.1"),
  port=os.environ.get("LZAPI_PORT", "7000"),
  debug=True
)
