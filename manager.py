from flask.ext.script import Manager
from app import app, init_db

manager = Manager(app)

@manager.command
def init():
    init_db()

if __name__ == "__main__":
    manager.run()
