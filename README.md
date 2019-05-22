# clusterscore  
This is python3, and uses [Flask](http://flask.pocoo.org/docs/1.0/).
The exact details to run the server depends on how you have flask installed
On the FreeBSD server I use, I have installed `py36-Flask` and this works:
```
export FLASK_APP=main.py
flask-3.6 run
```

On Ubuntu, install `python3-Flask` and try this:
```
export FLASK_APP=main.py
flask run
```

This will start a server that listens on http://127.0.0.1:5000/ .
For server use, it's possible to use `flask run -h x.x.x.x` to listen to an external IP. 
While that is what I do right now, the proper solution is to use a production quality server:
I've previously used [gUnicorn](https://gunicorn.org) to run flask apps, and should really
get around to setting that up for this as well.

There are settings for the temporary storage directories near the top of the main.py file. 
By default these are /tmp/results and /tmp/uploads.
If you're running on windows you probably want to change this. 
If you're just testing, "." should work, but will dump files in the script directory.

To automatically delete old uploaded/genereated files, look at the delete\_old\_files.sh script.

# Requirements
* Python3

The following python3 packages:
* flask 3.6 or newer
* pandas
* sqlite3
* matplotlib
* lifelines (https://github.com/CamDavidsonPilon/lifelines)
