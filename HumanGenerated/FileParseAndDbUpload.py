from configparser import ConfigParser
from datetime import datetime
#2020-09-20.ghwvvv added more datetime imports
from datetime import timedelta
from datetime import date
#2020-09-20.ghw^^^
from pathlib import Path
#from cryptography.fernet import Fernet
import pyodbc 
import os
import shutil
import json
import traceback
import logging
import uuid
import re
import sys

#NOTES ON BUILDING ****************************************
# pyInstaller has to be installed in the same directory as everything else - not in the main python install location.
# Otherwise I won't see the cryptography package.  
# Example syntax for pyInstaller:  c:\_work\apiName\env\Scripts\pyinstaller.exe fileparseanddbupload.py
# The above needs to be ran from the directory that contains the .py file to be compiled (i.e. c:\_work\apiName)
# The full install for both the API and FileParseandDbUpload compoents is located in the /dist directory.
# We have to manually copy the DatabaseAPI.INI file into each of those directories before bundling them into a zip for distribution.
# There's probably a way to do that automatically using pyInstaller, but I didn't bother with figuring it out.
#END NOTES ************************************************

#create the parser object and read in (parse) the .INI file.    
parser = ConfigParser()
parser.read('DatabaseAPI.ini')

#Utility functions ###################################################################################################################################

#get a list of file names (with their fully qualified paths) from the passed directory.  This function will exclude subdirectories.
def getFileList(path):
     
    filePaths = []

    try:
        #Get a list of all the stuff in the directory - just a list of files and folders - no path info comes back.
        for f in os.listdir(path):
            #check to see if this thing is a file (have to use join to link the file to the specific directory, since by default it uses your working directory)
            if os.path.isfile(os.path.join(path, f)):
                filePaths.append(os.path.join(path, f))
    
    except:
        handle_exception()
    
    return filePaths


def getDirectories(path):

    directories = []

    try:
    #Get a list of all the stuff in the directory - just a list of files and folders - no path info comes back.
        if os.path.exists(path):
            for d in os.listdir(path):
                #check to see if this thing is NOT a file (have to use join to link the file to the specific directory, since by default it uses your working directory)
                if not os.path.isfile(os.path.join(path, d)):
                    directories.append(os.path.join(path, d))
    
    except:
        handle_exception()
    
    return directories


def getTestFiles(path, pattern):

    files = []

    try:
        #Get a list of all the stuff in the directory - just a list of files and folders - no path info comes back.
        if os.path.exists(path):
            for f in os.listdir(path):

                #check to see if this thing is a file (have to use join to link the
                #file to the specific directory, since by default it uses your
                #working directory)
                if os.path.isfile(os.path.join(path, f)):

                    #make sure it matches the file name pattern we're looking
                    #for...
                    if pattern in f:

                        #...  and is a real test file (not a dummy)
                        if "[" in f:
                            files.append(os.path.join(path, f))
    
    except:
        handle_exception()
    
    return files

def getSettingsFiles(path, pattern):

    files = []

    try:
        #Get a list of all the stuff in the directory - just a list of files and folders - no path info comes back.
        if os.path.exists(path):
            for f in os.listdir(path):

                #check to see if this thing is a file (have to use join to link the
                #file to the specific directory, since by default it uses your
                #working directory)
                if os.path.isfile(os.path.join(path, f)):

                    #make sure it matches the file name pattern we're looking
                    #for...
                    if pattern in f:
                        files.append(os.path.join(path, f))
    
    except:
        handle_exception()
    
    return files

def getSettingsDir(path):
    return "%s\\Settings" % (path)


def getTestsDir(path):
    return "%s\\Tests" % (path)


def getDbConnection():

    #no error handling here - percolate that to the calling routine.
    servername = parser.get('database', 'server_name')
    db = parser.get('database', 'database_name')
    userid = parser.get('database', 'userid')
    ePassword = parser.get('database', 'password')

    password = ASCIItoString(ePassword)

    #create the connection.
    conn = pyodbc.connect(Driver='{SQL Server}', server = servername, database = db, uid = userid, pwd = password, Trusted_Connection = 'no')
     
    return conn

def getWorkingFolder():
    return parser.get('file_paths', 'workingfilepath')

def getArchiveFolder():
    return parser.get('file_paths', 'filearchivepath')

def getProblemFolder():
    return parser.get('file_paths', 'fileproblempath')

#Returns an instance of Fernet class initialized with the encryption key.
def getFernet():

    return Fernet("afEervFjgd9c2qukCwiq830zyA0B_ZeH4vvVfV6Yajw=")


#Encrypts the passed string.
def encrypt(password):

    f = getFernet()

    return f.encrypt(password.encode()).decode()


#Decrypts the passed string.
def decrypt(password):

    f = getFernet()

    return f.decrypt(password.encode())

def StringToASCII(string):
    AsciiText = string.encode('utf-8').hex()
    return AsciiText

def ASCIItoString(hexASCII):
    text = bytearray.fromhex(hexASCII).decode()
    return text

#returns the test ID from the Tests table for the given Test Name.
def getTestId(testName):

    sql = "Select TestID from Tests where TestName = ?"

    cursor = getDbConnection().cursor()

    #Even though it's called 'fetchone', it still returns an array, so grab the first element.
    return cursor.execute(sql, testName).fetchone()[0]



#This function is used to handle files that only have one record - i.e. json files.  
#Files with multiple records are handled differently, since we don't want to commit anything until all the records in the file are successful.
def run_query(sql, *args):

    #no error handling here - percolate that to the calling routine.

    #create the connection.
    conn = getDbConnection()
                         
    #create a cursor (whatever that is in this context :-) )
    cursor = conn.cursor()

    #execute the query with the passed args.  The execute method will automatically create the parameter objects - with pretty good type inference.  Lots easier than ado.net
    cursor.execute(sql, args)

    #Commit these changes.  By default, autocommit is set to false in pyodbc (which from what I hear is good in terms of performance) so if there is an error the implicit 
    #transaction will automatically rollback when execution leaves this method.
    cursor.commit()


def delete_file(file):

    #no error handling here - percolate to calling routine.
    if os.path.exists(file):
        os.remove(file)

def move_file_to_ArchiveFolder(file):
    if os.path.exists(file):
        workingFolder = getWorkingFolder()
        archiveFolder = getArchiveFolder()
        dest = file.replace(workingFolder, archiveFolder)
        destFolder = os.path.dirname(dest)
        if not os.path.exists(destFolder):
            os.makedirs(destFolder)
        shutil.move(file, dest)  # use shutil in case source and dest are on different computers

def move_file_to_ProblemFolder(file):
    if os.path.exists(file):
        workingFolder = getWorkingFolder()
        problemFolder = getProblemFolder()
        dest = file.replace(workingFolder, problemFolder)
        destFolder = os.path.dirname(dest)
        if not os.path.exists(destFolder):
            os.makedirs(destFolder)
        shutil.move(file, dest)  # use shutil in case source and dest are on different computers

#Common exception handling routine.
#Python handles exceptions different from C#.  Most of the exception info is not in the caught exception object.  It's in some sort of global things, so there's no 
#Need to catch the actual exception if all you want to do is log it.
#Also, python has a built in logging mechanism.
# NOTE: this routine expects the logPath to be present on the server - if not it will throw an error.  May want to create the log folder in the future.
def handle_exception(more_info=""):

    try:

         #Create the name for the log file.
         filename = os.path.join(parser.get('file_paths', 'logPath'), datetime.now().strftime("%Y-%m-%d_ErrorLog.log"))

         #pass that to the logging configuration.  Technically this probably only needs to be done once for the whole app, but no biggie doing it here.
         logging.basicConfig(filename=filename, level=logging.DEBUG)

         #The logger for some reason does not log the time of the entry.
         ex = "  Error Occurred On: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

         #add any additional info - I'm using this to pass in the file name that was being worked on in the 'do' routines.
         if more_info != "":
             ex += " Additional Info: " + more_info

         #calling logging.exception tells it to include the exception and stack trace.
         logging.exception(ex)
    
    except:
        print("CATASTROPHIC FAILURE!!! ERROR IN EXCEPTION HANDLER!!!")  #In case something really bad happens.  ;-)


#End Utility Functions ########################################################################################################################################


#Main routine that checks for files of various types and performs the import.
def importFiles():

    importSystemSettings()
    importFile(doCommonParamsFile, "params_common")
    importFile(doCCTFile, "params_cct")
    importFile(doHeatRiseFile, "params_heatrise")
    importFile(doTestStateFile, "test_state")
    importFile(doPowerOffFile, "power_off")
    importFile(doCycleFile, "cycle_file")
    importFile(doResistanceFile, "resistance")
    importFile(doRStability, 'rstability')
    importFile(doTStability, 'tstability')



#imports any systems settings files.
def importSystemSettings():
    directories = []
    files = []
        
    try:

        #get list of directories in the working directory - should be one for each test cell.
        directories = getDirectories(parser.get('file_paths', 'workingFilePath'))

        for dir in directories:

            #get the 'settings' dir under each test cell dir.
            settingsDir = getSettingsDir(dir)

            #get the system settings files in that dir.
            files = getSettingsFiles(settingsDir, parser.get('file_patterns', 'system_settings'))

            #process each file
            for file in files:
                doSystemsSettingsFile(file)

                #if successful, move the file from the working directory to the archive folder. If not successful, move the file to the Problems folder
                move_file_to_ArchiveFolder(file)
    except:
        #log the exception - which may be simply a re-log of one that occurred in doSystemSettingsFile().
        handle_exception()
        move_file_to_ProblemFolder(file)

#parse the system settings file and load the data to the db.
def doSystemsSettingsFile(file):

    try:
        #The 'with' automatically closes the file when the with block ends - equivalent to 'using' in c#
        with open(file) as json_file:
            data = json.load(json_file)
            
            testCellId = data['Test Cell ID']
            currentDate = datetime.now()
            #take note of json.dumps - which takes a json representation (basically a dictionary in python) and dumps it to a string - hense the 's' on the end of dump (this is apparently some sort of python convention.)
            fileContents = json.dumps(data)

            #The '?' in the query are positional parameter placeholders.  The run_query method accepts an *args list of values used to fill these parameters.
            #Make sure the values are in the correct order
            sql =  ("insert into SystemSettings "
                    "(TestCellId, LastChanged, Settings) " 
                    "values "
                    "(?, ?, ?)")
            
            run_query(sql, testCellId, currentDate, fileContents)

    except:
        handle_exception("Error with file " + file)
        raise   #After logging, raise this exception again so that the file is not deleted in the calling routine.


#Generic import function for all the files in the test directory.  This routine finds the files of the appropriate pattern and then passes those file
#names to the passed function definition - along with the test name, which is extracted from the test directory name.
def importFile(functionDef, setting):

    cellDirectories = []
    testDirectories = []
    files = []
   
    try:
        #get list of directories in the working directory - should be one for each test cell.
        cellDirectories = getDirectories(parser.get('file_paths', 'workingFilePath'))

        for cellDir in cellDirectories:

            #Get the tests directory for this test cell
            testsDir = getTestsDir(cellDir)

            #Now get the list of all the test directories for this cell
            testDirectories = getDirectories(testsDir)

            #In each test directory, get the 
            for testDir in testDirectories:

                files = getTestFiles(testDir, parser.get('file_patterns', setting))

                for file in files:

                    #pass the file name and test name to the passed function.
                    functionDef(file, Path(testDir).name)

                    #if successful, move the file to the archive folder
                    move_file_to_ArchiveFolder(file)

    except:
        handle_exception()
        move_file_to_ProblemFolder(file)

#Imports the common params file information
def doCommonParamsFile(file, testName):

    try:
        with open(file) as json_file:
            data = json.load(json_file)

            #Extract all the relevant common params info for the insert.
            guid = uuid.uuid1()
            testCellId = data['Test Cell ID']
            testCellName = data['Test Cell Name']
            startTimestamp = data['Start Timestamp']
            catalogNumber = data['Connector']['Catalog Number']
            modelNumber = data['Connector']['Model Number']
            reportNumber = data['Connector']['Report Number']
            electricalClass = data['Connector']['Electrical Class']
            conductorSize = data['Conductor Size']
            testType = data['Test Type']

            #In addition to the specific table columns, write out the whole common params file to a column as raw json.
            paramsCommon = json.dumps(data)
       
            sql =  ("insert into Tests "
                    "(TestID, TestCellId, TestCellName, TestName, StartTimeStamp, CatalogNumber, ModelNumber, ReportNumber, ElectricalClass, ConductorSize, TestType, ParamsCommon) " 
                    "values "
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

            run_query(sql, guid, testCellId, testCellName, testName, startTimestamp, catalogNumber, modelNumber, reportNumber, electricalClass, conductorSize, testType, paramsCommon)

    except:
        handle_exception("Error with file " + file)
        raise


#Update the tests table with a dump of the ParamsCCT json.
def doCCTFile(file, testName):

    try:
        with open(file) as json_file:
            data = json.load(json_file)

            sql =  ("update Tests set ParamsCCT = ? where TestName = ?")

            run_query(sql, json.dumps(data), testName)

    except:
        handle_exception("Error with file " + file)
        raise


#Update the tests table with a dump of the ParamsHeatRise json.
def doHeatRiseFile(file, testName):

    try:
        with open(file) as json_file:
            data = json.load(json_file)

            sql =  ("update Tests set ParamsHeatRise = ? where TestName = ?")

            run_query(sql, json.dumps(data), testName)

    except:
        handle_exception("Error with file " + file)
        raise



#Update the tests table with the test state and stop code from the TestState file.
def doTestStateFile(file, testName):

    try:
        with open(file) as json_file:
            data = json.load(json_file)
            testState = data['Test State']
            stopCode = data['Stop Code']

            sql =  ("update Tests set TestState = ?, StopCode = ?, TestStateObject = ? where TestName = ?")

            run_query(sql, testState, stopCode, json.dumps(data), testName)

    except:
        handle_exception("Error with file " + file)
        raise


#Handles the insertion of Power Off data.
def doPowerOffFile(file, testName):

    #This routine has its own db connection, etc. so that we can wait until the entire file loads successfully to the db before calling commit.

    sql = ""

    try:

        with open(file) as f:

            lines = f.readlines()

            if len(lines) < 2:
                return #something wrong with the file - bomb out.

            #Now fetch the testId based upon the test name and clear out any existing records for this test.
            testId = getTestId(testName)
            sql = "delete from DataBeforePowerOff where TestId = ?"
            run_query(sql, testId)

            #setup the cursor for this transaction
            conn = getDbConnection()
            cursor = conn.cursor()

            #loop through all the lines of data.
            for line in lines[1:]:  #skip the first line since that has the column names.
                splitline = line.strip().split("\t")

                sql = ("insert into DataBeforePowerOff "
                        "(TestId, TimeStamp, CycleNumber, ACCurrent, TCC, T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12, T13, T14, Tamb) " 
                        "values "
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

                cursor.execute(sql, testId, splitline[0], splitline[2], splitline[3], splitline[4], splitline[5], splitline[6], splitline[7], splitline[8], splitline[9], splitline[10], splitline[11], splitline[12], splitline[13], splitline[14], splitline[15], splitline[16], splitline[17], splitline[18], splitline[19])

            #if nothing errors, then commit the data.
            cursor.commit()

    except:
        handle_exception("Error with file " + file)
        raise


#Handles the insertion of Cycle data
def doCycleFile(file, testName):

    #This routine has its own db connection, etc. so that we can wait until the entire file loads successfully to the db before calling commit.

    sql = ""

    try:

        with open(file) as f:

            lines = f.readlines()

            if len(lines) < 2:
                return #something wrong with the file - bomb out.

            #Now fetch the testId based upon the test name and clear out any existing records for this test.
            testId = getTestId(testName)
            cycleNumber = int(re.search("(?<=Cycle)\d{4}", file).group())
            sql = "delete from CycleData where TestId = ? and CycleNumber = ?"
            run_query(sql, testId, cycleNumber)

            #setup the cursor for this transaction
            conn = getDbConnection()
            cursor = conn.cursor()

            for line in lines[1:]:  #skip the first line since that has the column names.
                splitline = line.strip().split("\t")

                try:
                    sql = ("insert into CycleData "
                        "(TestId, TimeStamp, CycleNumber, ACCurrent, TCC, T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12, T13, T14, Tamb) " 
                        "values "
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
                    cursor.execute(sql, testId, splitline[0], splitline[2], splitline[3], splitline[4], splitline[5], splitline[6], splitline[7], splitline[8], splitline[9], splitline[10], splitline[11], splitline[12], splitline[13], splitline[14], splitline[15], splitline[16], splitline[17], splitline[18], splitline[19])
                except:
                    print("Attempt to insert duplicate CycleData record")
            #if nothing errors, then commit the data.
            cursor.commit()

    except:
        handle_exception("Error with file " + file)
        raise


#Handles the insertion of Resistance data
def doResistanceFile(file, testName):

    #This routine has its own db connection, etc. so that we can wait until the entire file loads successfully to the db before calling commit.

    sql = ""

    try:

        with open(file) as f:

            lines = f.readlines()

            if len(lines) < 2:
                return #something wrong with the file - bomb out.

            #Now fetch the testId based upon the test name and clear out any existing records for this test.
            testId = getTestId(testName)
            sql = "delete from ResistanceData where TestId = ?"
            run_query(sql, testId)

            #setup the cursor for this transaction
            conn = getDbConnection()
            cursor = conn.cursor()

            for line in lines[1:]:  #skip the first line since that has the column names.
                splitline = line.strip().split("\t")

                sql = ("insert into ResistanceData "
                        "(TestId, TestName, CycleNumber, ACCurrent, RCC, RC1, RC2, RC3, RC4, RC5, RC6) " 
                        "values "
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

                cursor.execute(sql, testId, testName, splitline[0], splitline[1], splitline[2], splitline[3], splitline[4], splitline[5], splitline[6], splitline[7], splitline[8])

            #if nothing errors, then commit the data.
            cursor.commit()

    except:
        handle_exception("Error with file " + file)
        raise


#Handles RStability files
def doRStability(file, testName):

    handleStability(file, testName, "RStability")


#Handles TStability files.
def doTStability(file, testName):

    handleStability(file, testName, "TStability")



#This routine handles the insertion or update of stability data - either R or T.
def handleStability(file, testName, columnName):

    sql = ""
    lineData = ""

    try:

        with open(file) as f:

            #read the file and combine all the lines into one string (might be a better way to do this)
            lines = f.readlines()
            for line in lines:
                lineData += line

            testId = getTestId(testName)
            
            #If there's already a record, then just update the appropriate column
            if isStabilityRecordThere(testId):
                sql = "Update Stability set %s = ? where TestId = ?" % (columnName)

                run_query(sql, lineData, testId)

            #Insert a new record
            else:   
                sql = "Insert into Stability (TestID, TestName, %s) values (?, ?, ?)" % (columnName)
            
                run_query(sql, testId, testName, lineData)

    except:
        handle_exception("Error with file " + file)
        raise


#Performs a simple check to see if there are any records in Stability with the given testId
def isStabilityRecordThere(testId):

    sql = "Select count(*) from Stability where testId = ?"

    cursor = getDbConnection().cursor()

    return cursor.execute(sql, testId).fetchone()[0] != 0
       

#Starting point.  Actually all the Import functions could be called independently from the API or some other source if needed.
def main():
    
    importFiles()


#If this is being ran independently (as a stand alone python process) then this tells it to run the main() routine.
if __name__ == '__main__':      #I think this __main__ thing is a python convention of some sort.
    
    #If only one arg is passed (There will always be one arg, even if you don't specify one.  Python does it for you.  I think it's the script file name.)... then run main
    if len(sys.argv) == 1:
        main()
    else:

        ePWD = StringToASCII(sys.argv[1])

        #Set the database password in the .ini to the new encrypted password.
        parser.set("database", "password", ePWD)

        #Write the .ini file changes back out to the .ini.
        with open('DatabaseAPI.ini', 'w') as configfile:
            parser.write(configfile)

