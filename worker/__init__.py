import os
import scorer
import backenddb as bdb

class Worker:
    def __init__(self, app):
        self.db = bdb.BackendDB()
        self.OUTPUT_FOLDER = app.config['OUTPUT_FOLDER']
        self.UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
    
    def score(self, token):
        self.db.set_state(token, bdb.States.SCORE_WORK)
        self.db.add_message(token, 'Received file')
        expr_file = self.db.get_files(token)['EXPRESSION']
        status,res = self.do_score(expr_file)
        if (status):
            self.db.add_file(token, res, bdb.Filetypes.CLUSTERS)
            self.db.set_state(token, bdb.States.SCORED)
            self.db.add_message(token, 'Work finished')
        else:
            self.db.set_state(token, bdb.States.FILE_FAILED)
            self.db.add_message(token, res)
        
    def score_surv(self, id):
        pass

    def do_score(self, datafile):
        sc = scorer.Scorer()
        ok, error = sc.load_data(datafile, True)
        os.remove(datafile)
        if (not ok):
            return (False,error)
        sc.score()
        outfile = sc.save(self.OUTPUT_FOLDER)
        return (True,outfile)
