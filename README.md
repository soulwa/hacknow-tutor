# tutor

## to run development version:
- download the python project, run `pip install .` for requirements 
- set environment variables: 
```
$ export FLASK_APP=tutor
$ export FLASK_ENV=development
```
- make sure you have a database connection (you can set DATABASE_URL in a .env file) and run `flask init-db`
- when you're ready to test, run `python run.py` in the parent directory
	- this ensures socketio uses websockets vs `flask run`