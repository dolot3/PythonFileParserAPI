from flask import Flask
from flask import request, jsonify
#2020-08-16.ghw: Added Waitress
from waitress import serve
#2020-07-31.ghw: from configparser import SafeConfigParser  -  SafeConfigParser is deprecated
from configparser import ConfigParser
#2020-07-31.ghw: import pyodbc  - pyodbc not needed for this script
import os
import shutil
#from cryptography.fernet import Fernet

#create the parser object and read in (parse) the .INI file.    
#2020-07-31.ghw: parser = SafeConfigParser()  -  SafeConfigParser is deprecated
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

    #2020-07-31.ghw: saveWorkingLocation = "%s\\\\%s" % (rootWorkingLocation, testCellId)
    #2020-07-31.ghw: saveArchiveLocation = "%s\\\\%s" % (rootArchiveLocation, testCellId)
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

    #2020-07-31.ghw: saveWorkingLocation = "%s\\\\%s\\\\%s" % (rootWorkingLocation, testCellId, testName)
    #2020-07-31.ghw: saveArchiveLocation = "%s\\\\%s\\\\%s" % (rootArchiveLocation, testCellId, testName)
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



# A couple of utility functions for generating keys and encrypting text.
#@app.route('/api/getkey', methods=['get'])
#def generateKey():

#    key = Fernet.generate_key()
#    return key


#@app.route('/api/encrypt', methods=['post'])
#def encryptText():

#    key = request.values['key']
#    textToEncrypt = request.values['textToEncrypt']

#    f = Fernet(key)
#    encryptedText = f.encrypt(textToEncrypt.encode())

#    return encryptedText


#The below are test methods that you can use to make sure your client side code is working before trying to send files.  Just FYI...
#@app.route('/api/add', methods=['get'])
#def add_data():
#    if 'data' in request.args:
#        data = str(request.args['data'])
#        if data == 'GoodData':
#            return "Success"
#        else:
#            return "Failure"
#    else:
#        return "No Data"


#@app.route('/api/add', methods=['post'])
#def add_dataPost():
#    if not request.json or not 'title' in request.json:
#        data = { 'Success' : False }
#    else:
#        data = {
#                'Title' : request.json['title'],
#                'Desc' : request.json['description'],
#                'Success' : True
#            }
#    return jsonify(data)


#Actually launches the webserver and this app - listening on port 5000 of localhost.  Might want to test that with another machine name (on another machine) and see how it works.


#2020-08-16.ghw: Replaced run with call to waitress server
#if __name__ == '__main__':
#    # Run the app server on localhost:4449
#    app.run('localhost', 5000)
serve(app, port=5000)

