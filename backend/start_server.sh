#!/bin/bash
cd /home/spidey/projects/monq-procurement-rag/backend
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
