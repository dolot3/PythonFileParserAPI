from flask import Flask
from flask import request, jsonify
from waitress import serve
from configparser import ConfigParser
import os
import shutil

#create the parser object and read in (parse) the .INI file.    
parser = ConfigParser()
parser.read('DatabaseAPI.ini')

# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
app = Flask(__name__)

# Flask route decorators map urls to functions.

#NOTE:  No error handling or logging going on in here.  I wanted to wait and discuss how you want to handle this.

@app.route('/api/addSystemSettings', methods=['post'])
def add_systemSettings():
    file = request.files['file']
    testCellId = request.values['testcellid']

    rootWorkingLocation = parser.get('file_paths', 'workingFilePath')
    rootArchiveLocation = parser.get('file_paths', 'filearchivepath')

    saveWorkingLocation = "%s\\\\%s\\\\Settings" % (rootWorkingLocation, testCellId)
    saveArchiveLocation = "%s\\\\%s\\\\Settings" % (rootArchiveLocation, testCellId)

    save_file(file, saveArchiveLocation, saveWorkingLocation)

    return "success"

@app.route('/api/addData', methods=['post'])
def add_data():
    file = request.files['file']
    testCellId = request.values['testcellid']
    testName = request.values['testname']

    rootWorkingLocation = parser.get('file_paths', 'workingFilePath')
    rootArchiveLocation = parser.get('file_paths', 'filearchivepath')

    saveWorkingLocation = "%s\\\\%s\\\\Tests\\\\%s" % (rootWorkingLocation, testCellId, testName)
    saveArchiveLocation = "%s\\\\%s\\\\Tests\\\\%s" % (rootArchiveLocation, testCellId, testName)

    save_file(file, saveArchiveLocation, saveWorkingLocation)

    return "success"



#This method saves the file object to both the archive directory and working directory
def save_file(file, archiveLocation, workingLocation):

    #create the directories if they aren't there already
    os.makedirs(archiveLocation, exist_ok=True)
    os.makedirs(workingLocation, exist_ok=True)
    
    archiveLocation = "%s\\\\%s" % (archiveLocation, file.filename)

    file.save(archiveLocation)
    shutil.copy(archiveLocation, workingLocation)


#Actually launches the webserver and this app - listening on port 5000 of localhost.  
serve(app, port=5000)

