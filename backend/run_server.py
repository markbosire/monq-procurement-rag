#!/usr/bin/env python3
import os
import sys
import signal

signal.signal(signal.SIGHUP, signal.SIG_IGN)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
