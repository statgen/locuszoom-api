#!/usr/bin/env python3
import os
os.environ["LZAPI_MODE"] = "quick"

import sys
sys.path.insert(0,".")

from locuszoom.api import create_app
app = create_app()
app.run(host="0.0.0.0",port=7700,debug=True,use_reloader=False)
