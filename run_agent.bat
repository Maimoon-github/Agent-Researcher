@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python -m src.main %*
