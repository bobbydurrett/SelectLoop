SelectLoop

Selectloop is a Python script that queries an Oracle database to answer your question.

You pass it the database name and the name of a text file containing your question. 

Expected run string and example:

python selectloop.py database question_file

python selectloop.py MYDBNAME question.txt

database - name of the Oracle database that you are connecting to
question_file - text file with question you want answered about the database

For this version to work you need a user with these
privileges:

CREATE SESSION
SELECT ANY DICTIONARY
SELECT ANY TABLE

Put the username and password in credentials.py to hard code 
or substitute your own routine.

To run this script you need an AWS user that has the ability
to make Bedrock calls using Claude 4.6.

This code in bedrock.py assumes that you have the details
such as your region and secrets setup so this can run without
error:

    bedrock = boto3.client(
        service_name='bedrock-runtime',config=config)

Similarly you need an Oracle 19c or later client setup
so this code in db.py will run without error:

        oracledb.init_oracle_client()
        con = oracledb.connect(connect_string)

You need a tnsnames.ora with the database in it and 
all the environment variables and path setup for this to run
with defaults.

You need to edit db.py, bedrock.py, and credentials.py to work in your environment.
