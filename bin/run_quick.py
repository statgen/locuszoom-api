#!/usr/bin/env python
import os
os.environ["PORTALAPI_MODE"] = "quick"

import sys
sys.path.insert(0,".")

from portalapi import app
app.run(host="0.0.0.0",port=7700,debug=True,use_reloader=False)

