# tutor

## to run development version:
- download the python project, run `poetry install --no-root` or `pip install -r requirements.txt` for requirements 
	- `pip install .` works, but it also installs the app as a dependency which breaks heroku?? so uninstall if deploying
- set environment variables: 
```
$ export FLASK_APP=tutor
$ export FLASK_ENV=development
```
- make sure you have a database connection (you can set DATABASE_URL in a .env file) and run `flask init-db`
- when you're ready to test, run `flask run.py` in the parent directory
	- this ensures socketio uses websockets 