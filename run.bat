@echo off
set FLASK_APP=src.app:app
set FLASK_ENV=development
py -m flask run --host=0.0.0.0 --port=5000
