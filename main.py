import flask
from flask import render_template,Flask,flash,request,redirect,url_for
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
import backenddb as bdb
import worker as w

OUTPUT_FOLDER = "/tmp/results"
UPLOAD_FOLDER = "/tmp/uploads"

from flask import Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024 # 64 MB max upload
app.secret_key = "random secret key goes here and is random"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = bdb.BackendDB()
worker = w.Worker(app)

@app.route('/')
def frontpage():
	return render_template('index.html')
	
@app.route('/scorefile', methods=['POST'])
def receivefile():
  if 'file' not in request.files:
    print("Did not get a file")
    return render_template("error.html", error="Did not get a file")
  file = request.files['file']
  if file.filename == "":
    return render_template("error.html", error="Did not get a file")
  if file:
    token = db.create()
    filename = ".".join((token, bdb.Filetypes.EXPRESSION.name))
    filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filename)
    db.add_file(token, filename, bdb.Filetypes.EXPRESSION)
    db.set_state(token, bdb.States.GOTFILE)
    # Start a worker
    worker.score(token)
    return flask.redirect("/results/%s" % (token,))

@app.route('/results/<token>')
def get_results(token):
  state = db.get_state(token)
  messages = db.get_messages(token)
  messages = "\n".join(messages)
  if state in (bdb.States.GOTFILE, bdb.States.SCORE_WORK):
    return render_template("results_working.html", 
                           token=token, state=state.name, messages=messages)
  if state in (bdb.States.FILE_FAILED, bdb.States.SURV_FAILED):
    return render_template("error.html", error=messages)
  if state == bdb.States.SCORED:
    return render_template("results_clustered.html",
                           token=token, messages=messages)
  messages += "\nState: " + state.name
  return render_template("error.html", messages=messages)

@app.route('/files/clusters/<token>')
def get_clusters(token):
  clusterfile = db.get_files(token)['CLUSTERS']
  send_as = token+".clusters.csv"
  return flask.send_file(clusterfile, attachment_filename=send_as, mimetype="text/csv")
