SelectLoop

This is an experimental script called selectloop.py. It uses a Claude Sonnet 4.6 LLM through
AWS Bedrock. It is written for an Oracle DBA who is solving database problems such as 
performance problems. You pass it a text file such as question.txt and it outputs two other
text files, such as select.txt and report.txt. You can name these anything of course. select.txt
is a list of select statements (queries) that Claude generated and their output when run against
the database. report.txt is the output of a final Claude inference based on the queries and their
outputs. You can limit how long it runs using the command line arguments.

Need seven arguments. Expected run string and example:

python selectloop.py database question_file select_file report_file num_loops timeout_seconds max_rows

python selectloop.py MYDBNAME question.txt select.txt report.txt 10 60 1000

question_file - text file with question you want answered about the database
select_file - list of select statements Claude generated and their outputs
report_file - final output of this run - text file
num_loops - number of select statements to generate and run
timeout_seconds - timeout in seconds for both the database calls and the bedrock LLM calls
max_rows - max number of rows fetched in each query that is run

With big enough values it is easy to blow out the limit of 1,000,000 tokens so these keep it manageable.

Just like working with AI chat sites be sure to check everything it tells you and do your own investigation.

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

Of course you can edit db.py, bedrock.py, and credentials.py to work in your environment.
