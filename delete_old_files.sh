#!/bin/sh

# Delete files, then file entries, then states.
# To make this run automatically, add something like this to the crontab
# of the user owning the files:
# @hourly /path/to/delete_old_files.sh

# There is an obvious race condition in this: If a thing ages out while we're deleting, we may 
# delete only the file entries and states, but not the files.
# To fix this, we give ourselves 0.01 day (Â~15 min) leeway.
# This can fail the other way (delete the file but not the entry), but that fixes itself
# with nothing more than log warnings next time around.

echo "select f.filename from state s join files f on (s.id=f.id)  where julianday('now') - julianday(s.added) > 1;" | sqlite3 state.sqlite | xargs rm >> ~/delete.log 2>&1
echo "delete from files  where files.id in (select id from state  where julianday('now') - julianday(added) > 1.01);" | sqlite3 state.sqlite >> ~/delete.log 2>&1
echo "delete from state  where  where julianday('now') - julianday(added) > 1.011;" | sqlite3 state.sqlite >> ~/delete.log 2>&1

