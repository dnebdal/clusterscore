import sqlite3
import base64
import secrets
from enum import Enum

"""
[C]lient, [S]erver, [W]orker.
    C: Opens webpage
    C: Start uploading file
    S: id = bdb.create
    S: bdb.add_file(id, EXPRESSION)
    S: bdb.set_state(id, GOTFILE)
    S: start_cluster_worker(id)
    W: bdb.set_state(id, SCORE_WORK)
    S: redirect client to /result/id (or /error/n)
    (...)
    C: Poll /state/id
    S: return 'SCORE_WORK'
    (...)
    W: bdb.set_state(id, SCORED)
    W: bdb.add_file(id, CLUSTERS)
    W: Dies.
    (...)
    C: Poll /state/id
    S: return 'SCORED'
    C: fetches /file/id/CLUSTERS
    S: sends bdb.get_files(id)['CLUSTERS']
    C: yay.
    (...)
    C: (Still on /result/id)
    C: Uploads survival file
    S: bdb.add_file(id, SURVIVAL)
    S: bdb.set_state(id, GOTSURV)
    S: start_km_worker(id)
    W: bdb.set_state(id, SURV_WORK)
    (...)
    C: Poll /state/id
    S: return 'SURV_WORK'
    (...)
    W: Done.
    W: bdb.set_state(id, SURVDONE)
    W: bdb.add_file(id, KMPLOT)
    W: bdb.add_file(id, KMTEXT)
    W: Dies.
    (...)
    C: Poll /state/id
    S: Return SURVDONE
    C: fetches and displays inline /file/id/KMPLOT
    C: fetches and displays in a <pre> /file/id/KMTEXT
    C: follows links and downloads both
    C: Done. Survives.
    
    Much later:
    [C]ron, [P]eriodic_cleanup.py
    C: The time is nigh!
    C: Starts Periodic_cleanup.py
    P: ids = bdb.get_old()
    P: for id in ids:
    P:     files = bdb.get_files(id)
    P:        for f in files:
    P:            delete f
    P:     bdb.remove(id)
    
"""


class States(Enum):
    NOFILE          = 0
    GOTFILE         = 1
    SCORE_WORK      = 2
    SCORED          = 3
    GOTSURV         = 4
    SURV_WORK       = 5
    SURVDONE        = 6
    
class Filetypes(Enum):
    EXPRESSION  = 1
    SURVIVAL    = 2
    CLUSTERS    = 3
    KMPLOT      = 4
    KMTEXT      = 5

class BackendDB:
    states = ('')
    
    def __init__(self):
        self.c = sqlite3.connect("state.sqlite", isolation_level = None)
        
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS state (
              counter integer primary key,
              id char(14) unique not null,
              state int not null,
              added int not null
              );"""
        )
        
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS files (
                counter integer primary key,
                id char(14) not null,
                filename text not null,
                filetype int not null,
                FOREIGN KEY(id) REFERENCES state(id),
                UNIQUE(id,filetype)
            );""")
        
        
    """ Creates a random text ID we can send to the user.
        This needs to be unguessable: If you can predict the next/previous
        key, or bruteforce them, you can get someone else's session.
    
        The key is 7 bytes, 56 bits, which ought to be enough.
        To make it readable if that should be needed, it's base32-encoded to 
        12 characters, presented as 4-char blocks with dashes.
    """
    def make_id(self):
        id = base64.b32encode( secrets.token_bytes(7) ).decode("ascii")
        id = "-".join((id[0:4], id[4:8], id[8:12]))
        return(id)
    
    def set_state(self, id, state):
        if not type(state) == States:
            raise Exception("state is not a backenddb.States")
        self.c.execute("UPDATE state SET state=? WHERE id=?", (state.value, id))

    def create(self, id=None, state=None):
        if id is None:
            id = self.make_id()
        if state is None:
            state = States.NOFILE
        if not type(state) == States:
            raise Exception("state is not a backenddb.States")
        self.c.execute("""
            INSERT INTO state(id,state, added) 
            VALUES (?,?, datetime("now"))            
            """, (id, state.value) )
        return id
    
    """Get the IDs of all entries older than the given minage (in fractional days)"""
    def get_old(self, minage=1):
        res = self.c.execute("""
            SELECT id FROM state 
            WHERE (julianday('now')-julianday(added)) >=?
            """, (minage, )).fetchall()
        res = [i[0] for i in res]
        return(res)
    
    def get_files(self, id):
        files = self.c.execute("""
            SELECT filename,filetype
            FROM files WHERE id=?""", (id,))
        res = { Filetypes(t).name : n for n,t in files }
        return(res)
    
    def add_file(self, id, filetype):
        if not type(filetype) == Filetypes:
            raise Exception("filetype is not a backenddb.Filetypes")
        filename = id + "." + filetype.name
        self.c.execute("""
            INSERT INTO files(id,filename,filetype)
            VALUES (?, ?, ?);
            """, (id,filename,filetype.value))
        
        
        
