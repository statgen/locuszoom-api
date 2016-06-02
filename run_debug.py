#!/usr/bin/env python
import os
os.environ["PORTALAPI_MODE"] = "dev"

from portalapi import app
app.run(host="0.0.0.0",port=7600,debug=True)

