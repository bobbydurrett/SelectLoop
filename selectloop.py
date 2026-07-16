"""

selectloop.py - Uses Claude to generate a series of select statements to resolve a performance issue.
               
"""

import time
import sys
from credentials import get_userpassword,drop_user
from bedrock import getresponse
import re
from db import db_con_cur
import oracledb

def remove_code_fences(s):
    """
    
    If two ``` lines exist remove their lines
    and everything before the first one and after the last one.
    
    Returns unchanged string if there are fewer than 2 ``` lines
    
    """
    
    # find index of first ```
    
    index1 = s.find("```")
    
    if index1 < 0:
        return s
        
    # find index of second ```
    
    index2 = s.find("```",index1+3)
    
    if index2 < 0:
        return s
    
    # find newline after first ```
    
    nlindex = s.find("\n",index1,index2)
    
    if nlindex < 0:
        return s
    
    # trim off around the ``` lines
    
    new_s = s[nlindex+1:index2]
    
    return new_s.strip()

def remove_before_blank_line(s):
    """
    
    If there is a blank line remove it and everything
    before it.
    
    """
    
    # find index of first blank line
    
    index1 = s.find("\n\n")
    
    if index1 < 0:
        return s
        
    # remove blank line and everything before it
    
    new_s = s[index1+2:]
    
    return new_s.strip()

def extract_select(response):
    """
    
    Takes one of Claude's responses and extracts just the select statement. 
    Starts with select and ends with first ;
    
    """
    
    # get rid of ``` around select
    
    response = remove_code_fences(response)
    
    # get rid of blank line and everything before it
    
    response = remove_before_blank_line(response)
    
    index = response.upper().find('SELECT')
    
    if index < 0:
        return None
        
    select_rest = response[index:]
    
    index2 = select_rest.find(';')
    
    if index2 < 0:
        return None
        
    select_no_semicolon = select_rest[:index2]
    
    return select_no_semicolon
    
def first_prompt(question):
    """
    Generate the prompt that gets the first select statement.
    """
    
    return question +"""
Please generate a select statement that will give more information about this subject.
Please only generate ASCII text.
Please keep to no more than 80 character lines.
Please output only the select statement that you want to run next.
End the select statement with ;
    """
    
def strip_comments(s):
    s = re.sub(r"--.*?$", "", s, flags=re.MULTILINE)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return s

def validate_select(select):
    """
    Basic safety check for SELECT-only SQL.
    """

    if not select:
        return False

    s = strip_comments(select).strip().upper()

    # Must start with SELECT
    
    if not re.match(r"\bSELECT\b", s):
        return False
        
    # Reject multiple statements (semicolon anywhere except maybe end)
    
    if ";" in s[:-1]:
        return False
        
    # check for FOR UPDATE clause
    
    # block FOR UPDATE (with whitespace/comments tolerance)
    
    if re.search(r"\bFOR\s+UPDATE\b", s):
        return False
        
    return True
        
def generate_select(prompt,timeout_secs):
    """ 
    Generate a select statement based on a prompt.
    """
    
    # Ask Claude to generate a SELECT statement
    
    response = getresponse(prompt,timeout_secs)
    
    #print("\nClaude response generating SELECT:\n")
    #print(response+"\n")
            
    # Pull just the select statement from the resonse
    
    select = extract_select(response)
    
    if (validate_select(select)):
        return select
    else:
        return "select * from dual"
        
def format_data(column_names,data_list):
    """ 
    Returns a nicely formatted text version of
    the data returned by the query.
    """

    # Get the maximum length of each column as a string

    num_columns = len(column_names)

    # Initialize lengths to column lengths

    max_lengths=[]
    for cn in range(num_columns):
        max_lengths.append(len(column_names[cn]))
            
    # Loop through entire list

    for d in data_list:
        for cn in range(num_columns):
            data_length = len(str(d[cn]))
            if data_length > max_lengths[cn]:
               max_lengths[cn] = data_length
               
    # Print column names padding for max lengths 

    column_name_header=""
    for cn in range(num_columns):
        column_name_header += column_names[cn].rjust(max_lengths[cn]) + " "
    formatted = column_name_header + '\n\n'
            
    # Print data with same padding
    
    for d in data_list:
        data_line=""
        for cn in range(num_columns):
            data_line += str(d[cn]).rjust(max_lengths[cn]) + " "
        formatted += data_line + '\n'

    return formatted
    
def run_select(cur,select,max_rows):
    """
    Run the select statement and return a formatted output
    """

    try:
        cur.execute(select)
   
        data_list = cur.fetchmany(max_rows)
    except oracledb.DatabaseError as e:
        err = e.args[0]
    
        details = []
        details.append(f"message={err.message}")    # full message text
    
        # These may or may not exist depending on error
        if hasattr(err, "offset") and err.offset:
            details.append(f"offset={err.offset}")  # position in SQL text
        
        return " | ".join(details)
    
    column_names = []
    for d in cur.description:
        column_names.append(d[0])
        
    output = format_data(column_names,data_list)
    
    return output
    
def middle_prompt(question,query_history):
    """
    Generate the prompt that gets each additional select statement
    based on the original question and the query history.
    """
    
    return question +"""
Please generate a select statement that will give more information about this subject.
After this prompt will be a history of the select statements the you recommended earlier
and their outputs. Use them to guide your choice of the next select statement.
Please only generate ASCII text.
Please keep to no more than 80 character lines.
Please output only the select statement that you want to run next.
End the select statment with ;
Earlier queries and their output:
    """ +query_history

def final_prompt(question,query_history):
    """
    Generate the prompt that produces a report explaining all
    the queries and their outputs.
    """
    
    return question +"""
Please generate a short report which explains this subject based on 
the select statements and their outputs which follow.
Please only generate ASCII text.
Please keep to no more than 80 character lines.
Please keep the output at no more than 30 lines.
Queries and their output:
    """ +query_history

if __name__ == '__main__':

    # Capture time so I can keep track of how long it takes to run this script
    
    before = time.perf_counter()
    
    # Main code
    
    # Process arguments
    
    if len(sys.argv) < 8:
        print("\nNeed seven arguments. Expected run string and example:\n")
        print("python selectloop.py database question_file select_file report_file num_loops timeout_seconds max_rows\n")
        print("python selectloop.py MYDBNAME question.txt select.txt report.txt 10 60 1000\n")
        sys.exit(-1)
        
    database = sys.argv[1]
    question_file = sys.argv[2]
    select_file = sys.argv[3]
    report_file = sys.argv[4]
    num_loops = int(sys.argv[5])
    timeout_secs = int(sys.argv[6])
    max_rows = int(sys.argv[7])
    
    print("\nDatabase: "+database)
    print("Question file: "+question_file)
    print("Select file: "+select_file)
    print("Report file: "+report_file)
    print("Number of loops: "+str(num_loops))
    print("Query and Bedrock timeout in seconds: "+str(timeout_secs))
    print("Maximum number of rows fetched from query: "+str(max_rows))
    
    # get username and password for given database
    
    username, password = get_userpassword(database)
        
    # read in question file
    
    with open(question_file, "r", encoding="utf-8") as f:
        question = f.read()
        
    # get the prompt to generate the first select statement

    prompt = first_prompt(question)
    
    print("\nProcessing select statement 1 prompt length = "+str(len(prompt)))
    
    select = generate_select(prompt,timeout_secs)
    
    #print("\nGenerated select:\n")
    #print(select+"\n")
    
    # Get database connection and cursor
            
    con,cur = db_con_cur(username,password,database,timeout_secs)
            
    # Run select statement
        
    output = run_select(cur,select,max_rows)
        
    # Loop through rest of select statements
    
    history = select+'\n\n'+output+'\n\n'
    
    for loop in range(num_loops - 1):
        
        # Start with select number 2
        
        select_number = loop + 2
        
        # Generate next select based on output of previous.
    
        prompt = middle_prompt(question,history)

        print("Processing select statement "+str(select_number)+" prompt length = "+str(len(prompt)))
    
        select = generate_select(prompt,timeout_secs)

        #print("\nGenerated select:\n")
        #print(select+"\n")

        # Run select statement
        
        output = run_select(cur,select,max_rows)
                
        history += select+'\n\n'+output+'\n\n'
        
    # Close connection and cursor
        
    cur.close()
    con.close()
    
    # Write history to select file
    
    with open(select_file, "w") as f:
        f.write(history)    
    
    # Do final inference to explain report
    
    prompt = final_prompt(question,history)
        
    # Ask Claude to generate a final report
    
    print("\nGenerating final report")
    
    report = "*** Report generated by AI. It may contain errors. ***\n\n"
    
    report += remove_code_fences(getresponse(prompt,timeout_secs))
    
    # Write report to report file
    
    with open(report_file, "w") as f:
        f.write(report)    
                     
    # Finish run time calculation and print out
    
    after = time.perf_counter()
    
    print(' ')  
    print('Run time in seconds: {0:<10.0f}'.format(after - before))

