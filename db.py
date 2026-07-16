"""

Oracle database connection routine. Put in separate file so it can be different on different platforms.

"""

import oracledb
import sys

def db_con_cur(username, password, database, timeout_secs):
    """
    
    Return a connection and cursor object for the given database and
    credentials.
    
    """
    connect_string = username+"/"+password+"@"+database
    
    try:
        oracledb.init_oracle_client()
        con = oracledb.connect(connect_string)
    except oracledb.DatabaseError as e:
        print('Error on '+database+':'+str(e.args[0]))
        sys.exit(1)

    con.call_timeout = timeout_secs * 1000   # milliseconds

    cur = con.cursor()
    
    return con,cur