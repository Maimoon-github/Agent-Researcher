@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python -m pytest tests/
