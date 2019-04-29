import os
import os.path
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
        outfile = os.path.join(self.OUTPUT_FOLDER, "%s.KMTEXT.csv" % (token, ) ) 
        status,res = self.do_score(expr_file, outfile)
        if (status):
            self.db.add_file(token, outfile, bdb.Filetypes.CLUSTERS)
            self.db.set_state(token, bdb.States.SCORED)
            self.db.add_message(token, 'Work finished')
        else:
            self.db.set_state(token, bdb.States.FILE_FAILED)
            self.db.add_message(token, res)
        
    def score_surv(self, token):
        self.db.set_state(token, bdb.States.SURV_WORK)
        self.db.add_message(token, "Received survival data")
        files       = self.db.get_files(token)
        survfile    = files['SURVIVAL']
        clusterfile = files['CLUSTERS']
        status,res,res2 = self.do_surv(token, survfile,clusterfile)
        if(status):
            self.db.add_file(token, res,  bdb.Filetypes.KMPLOT)
            self.db.add_file(token, res2, bdb.Filetypes.KMTEXT)
            self.db.set_state(token, bdb.States.SURVDONE)
            self.db.add_message(token, "KM plot done")
        else:
            self.db.set_state(token, bdb.States.SURV_FAILED)
            self.db.add_message(token, res)

    def do_score(self, datafile, outfile):
        sc = scorer.Scorer()
        ok, error = sc.load_data(datafile, True)
        if (not ok):
            return (False,error)
        sc.score()
        outfile = sc.save(outfile)
        return (True, "")
    
    def do_surv(self, token, survfile, clusterfile):
        kmplotfile = os.path.join(self.OUTPUT_FOLDER, token+".KMPLOT.png")
        kmtextfile = os.path.join(self.OUTPUT_FOLDER, token+".KMTEXT.csv")
        sc = scorer.Scorer()
        ok, error = sc.load_surv(survfile, clusterfile)
        if (not ok):
            return (False, error, "")        
        sc.score_surv(kmplotfile, kmtextfile)
        return(True, kmplotfile, kmtextfile)
