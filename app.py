from Auction import app, db
from Auction.main import server
import os
# import sqlite3

with app.app_context():
    db.create_all()   # creating the database with all the models in Auction.models

# connection = sqlite3.connect("instance/db.sqlite")
# cursor = connection.cursor()
# command = "DROP TABLE item;"
# cursor.execute(command)
# connection.close()

if __name__ == "__main__":
    pid = os.fork()
    if pid == 0:  #child process
        with app.app_context():
            server('127.0.0.1', 6000)  # runs the main server in the child process
    elif pid > 0:
        app.run(debug=False)  # runs the main application