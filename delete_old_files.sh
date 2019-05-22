#!/bin/sh

echo "select f.filename from state s join files f on (s.id=f.id)  where julianday('now') - julianday(s.added) > 1;" | sqlite3 state.sqlite | xargs  echo rm 


