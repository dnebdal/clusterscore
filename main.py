import scorer
import flask
from flask import render_template,Flask,flash,request,redirect,url_for
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename

OUTPUT_FOLDER = "/tmp/results"
UPLOAD_FOLDER = "/tmp/uploads"

from flask import Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024 # 64 MB max upload
app.secret_key = "random secret key goes here and is random"

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
    filename = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
    file.save(filename)
    ok,result = do_score(filename)
    if ok:
      return flask.send_file(result, mimetype="text/plain", as_attachment = True, attachment_filename="clusters.txt" )
      @after_this_request
      def delete_file(response):
        os.remove(result)
    return render_template("error.html", error=result)


def do_score(datafile):
  sc = scorer.Scorer()
  ok, error = sc.load_data(datafile)
  os.remove(datafile)
  if (not ok):
    print("Error template? " + error)
    return (False,error)
  sc.score()
  outfile = sc.save(OUTPUT_FOLDER)
  return (True,outfile)
