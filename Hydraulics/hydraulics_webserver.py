#!/usr/bin/python

# Hydraulics test bed - HTTP/REST server

import BaseHTTPServer
import json
import hydraulics_drv
import hydraulics_playback
import logging
import unittest

import attract_manager

from cgi import parse_header, parse_multipart
from sys import version as python_version
if python_version.startswith('3'):
    from urllib.parse import parse_qs
else:
    from urlparse import parse_qs
    
logger = logging.getLogger("HTTP")

class HydraulicsHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def getFile(self, mimeType):
        try:
#            print ("attempting to open", self.path)
            f=open("." + self.path, "rb")
            self.send_response(200)
            self.send_header('Content-type', mimeType)
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
        except FileNotFoundError:
            self.sendError(404)
            
    def sendError(self, err):
        self.send_response(err)
        self.send_header('Content-type','text/html')
        self.end_headers()
        
    def send200(self, data):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data))
        
    def do_OPTIONS(self):
        print "OPTIONS"
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")    
        
    def do_GET(self):
        if self.path.endswith(".png"):
            self.getFile('image/png')
        elif self.path.endswith(".gif"):
            self.getFile('image/gif')
        elif self.path.endswith(".jpeg"):
            self.getFile('image/jpeg')
        elif self.path.endswith(".html"):
            self.getFile('text/html')
        elif self.path.endswith(".js"):
            self.getFile('application/javascript')
        elif self.path.endswith(".css"):
            self.getFile('text/css')
        else:
            pathArray = self.path[1:].split("/")
            if pathArray[-1] == "":
                del pathArray[-1]
            if (len(pathArray) >= 1 and pathArray[0] == "hydraulics"):
                if (len(pathArray) == 1 ):  # just 'hydraulics'
                    self.send200(getHydraulicsState())
                elif (len(pathArray) == 2 and pathArray[1] == "playbacks"):
                    self.send200(getPlaybacks())
                elif (len(pathArray) == 2 and pathArray[1] == "position"):
                    self.send200(getHydraulicsPosition())
                else:
                    self.sendError(404)
            else:
                self.sendError(404)
                
    def do_DELETE(self):
        pathArray = self.path[1:].split("/")
        if (len(pathArray) == 3):
            if ((pathArray[0] == "hydraulics") and (pathArray[1] == "playbacks")):
                hydraulics_playback.deleteRecording(pathArray[2])


    def do_POST(self):
        try:
            ctype, pdict = parse_header(self.headers['content-type'])
            if ctype == 'multipart/form-data':
                postvars = parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers['content-length'])
                postvars = parse_qs(
                        self.rfile.read(length),
                        keep_blank_values=1)
            else:
                postvars = {}
            
            pathArray = self.path[1:].split("/")
            if pathArray[-1] == "":
                del pathArray[-1]
            if (len(pathArray) >= 1 and (pathArray[0] == "hydraulics")):
                if len(pathArray) == 1:
                    if ("manual_x" in postvars and "manual_y" in postvars and "manual_z" in postvars):
                        hydraulics_drv.setManualPosition(int(postvars["manual_x"][0]),
                                                         int(postvars["manual_y"][0]),
                                                         int(postvars["manual_z"][0]))
                    if "inputSource" in postvars:
                        hydraulics_drv.setInputSource(postvars["inputSource"][0])
                    if "feedbackSource" in postvars:
                        hydraulics_drv.setFeedbackSource(postvars["feedbackSource"][0])
                    if "outputEnabled" in postvars:
                        hydraulics_drv.enableOutput(postvars["outputEnabled"][0].lower() == "true")
                    if "attractModeDelta" in postvars:
                        attract_manager.attractModeDelta(int(postvars["attractModeDelta"][0]))
                    if "attractModeTimeout" in postvars:
                        attract_manager.attractModeTimeout(float(postvars["attractModeTimeout"][0]))
                    if "autoAttractEnabled" in postvars:
                        attract_manager.autoAttractModeEnabled(postvars["autoAttractEnabled"][0].lower() == "true")
                    if "playback" in postvars:
                        doPlay = postvars["playback"][0].lower()
                        if doPlay == "true":
                            attract_manager.startAttractMode(False) # False means not interruptable
                        elif doPlay == "false":
                            attract_manager.stopAttractMode()                
                    if "currentPlayback" in postvars:
                        newPlayback = postvars["currentPlayback"][0]
                        hydraulics_playback.setCurrentPlayback(newPlayback)
                    
                    
                elif len(pathArray) == 2 and (pathArray[1] == "playbacks"):   
                    if "record" in postvars:
                        doRecord = postvars["record"][0]
                        if doRecord.lower() == "true":
                            hydraulics_playback.startRecording()
                        else:
                            hydraulics_playback.stopRecording()
                    if "recordingSource" in postvars:
                        hydraulics_playback.setRecordingSource(postvars["recordingSource"][0])
                    if "currentPlayback" in postvars:
                        newPlayback = postvars["currentPlayback"][0]
                        hydraulics_playback.setCurrentPlayback(newPlayback)
                elif len(pathArray) == 3 and (pathArray[1] == "playbacks"):
                    playbackName = pathArray[2]
                    if "newName" in postvars:
                        newPlaybackName = postvars["newName"][0]
                        hydraulics_playback.renamePlayback(playbackName, newPlaybackName)
                    
                self.send_response(200)
            else:
                self.sendError(404)
                
        except Exception:
            logger.exception("Unexpected exception in POST")
            self.sendError(500)
            
    def log_message(self, format, *args):
        # yep, I'm sick of the annoying logging of all requests
        pass

def getHydraulicsState():
    control_x, control_y, control_z = hydraulics_drv.getCurrentInput()
    pid_x, pid_y, pid_z = hydraulics_drv.getVoltageInput()
    
#    loopback_x, loopback_y, loopback_z = hydraulics_drv.getLoopbackValues()
    
    manualPosition = hydraulics_drv.getManualPosition()
    
    retObj = {}
    
    retObj["x"] = control_x
    retObj["y"] = control_y
    retObj["z"] = control_z
    retObj["pid_x"] = pid_x
    retObj["pid_y"] = pid_y
    retObj["pid_z"] = pid_z
    retObj["playbacks"]       = hydraulics_playback.getPlaybackList()
    retObj["currentPlayback"] = hydraulics_playback.getCurrentPlayback()
    retObj["isRecording"]     = hydraulics_playback.isRecording()
    retObj["recordingSource"]   = hydraulics_playback.getRecordingSource()
    retObj["recordingSources"]  = hydraulics_playback.getRecordingSources()
    retObj["inputSources"]    = hydraulics_drv.getInputSources()
    retObj["feedbackSources"] = hydraulics_drv.getFeedbackSources()
    retObj["inputSource"]     = hydraulics_drv.getInputSource() # get attract mode thingy! XXX
    retObj["feedbackSource"]  = hydraulics_drv.getFeedbackSource()
    retObj["outputEnabled"]   = hydraulics_drv.isOutputEnabled()
    retObj["autoAttractEnabled"] = attract_manager.autoAttractModeEnabled() 
    retObj["attractModeDelta"]   = attract_manager.attractModeDelta() 
    retObj["attractModeTimeout"] = attract_manager.attractModeTimeout() 
    retObj["attractPlaying"]     = attract_manager.inAttractMode()
    retObj["states"]          = getAllStates()
    retObj["currentState"]    = getCurrentState()
    retObj["manual_x"]        = manualPosition[0]
    retObj["manual_y"]        = manualPosition[1]
    retObj["manual_z"]        = manualPosition[2]

    print ( "Adding currentState to the data {} ({})".format(retObj["currentPlayback"],hydraulics_playback.getCurrentPlayback()) )
    
    return retObj

gValidStates = ["passthrough", "nomove", "attract", "manual", "test"]
def getAllStates():
    ''' Get all possible states. States are a high level concept found only in the REST
    API, and can be a combination of various states at the lower level'''
    return gValidStates
    
# XXX - single playback in attract mode, then swap to manual? This should be an option!
# FIXME
# XXX - do we loop through
def setState(state):
    if state in gValidStates:
        if state == "passthrough":
            hydraulics_drv.setInputSource("controller")
            hydraulics_drv.enableOutput(True)
            hydraulics_drv.setFeedbackSource("sculpture")
        elif state == "nomove":
            hydraulics_drv.enableOutput(False)
        elif state == "attract": 
            attract_manager.startAttractMode(False)
            hydraulics_drv.enableOutput(True)
            hydraulics_drv.setFeedbackSource("sculpture")
        elif state == "manual":
            hydraulics_drv.setInputSource("manual")
            hydraulics_drv.enableOutput(True)
            hydraulics_drv.setFeedbackSource("sculpture")            
        elif state == "test":
            hydraulics_drv.setInputSource("controller")
            hydraulics_drv.enableOutput(False)
            hydraulics_drv.setFeedbackSource("recording")
    else:
        logger.warning("Invalid state {} specified, ignoring".format(state))

def getCurrentState():
    inputSource = hydraulics_drv.getInputSource()
    feedbackSource = hydraulics_drv.getFeedbackSource()
    enabled = hydraulics_drv.isOutputEnabled()
    state = "mixed"
    
    if not enabled and feedbackSource == "recording":
        state = "test"
    elif not enabled:
        state = "nomove"
    elif inputSource == "controller" and feedbackSource == "sculpture":
        state = "passthrough"
    elif inputSource == "manual":
        state = "manual"
    elif attract_manager.inAttractMode():
        state = "attract"
    else:
        logger.info("State not easily described")
    
    return state    
    
def getHydraulicsPosition():
    pos_x, pos_y, pos_z = hydraulics_drv.getCurrentInput()
    retObj = {}
    
    retObj["x"] = pos_x
    retObj["y"] = pos_y
    retObj["z"] = pos_z
    
    return retObj

baseURL = "http://localhost:9000/hydraulics/"

class WebserverTestCase(unittest.TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_basicStatus(self):
        r = requests.get(baseURL)
        print baseURL
        print r.status_code
        json = r.json()
        self.assertTrue(r.status_code == 200)
        self.assertFalse(json["isRecording"])
        self.assertTrue(json["manual_x"] == 0)
        self.assertTrue(json["manual_y"] == 0)
        self.assertTrue(json["manual_z"] == 0)
        self.assertTrue(len(json["playbacks"]) == 3)
        self.assertTrue(json["currentPlayback"] == "firstPlayback")
        print r.json()
        
    def test_playbackGet(self):
        r = requests.get(baseURL + "playbacks")
        self.assertTrue(r.status_code == 200)
        print r.text
        
    def test_playbackSet(self):
        r = requests.post(baseURL + "playbacks", data={"currentPlayback":"secondPlayback"})
        self.assertTrue(r.status_code == 200)
        r = requests.get(baseURL)
        self.assertTrue(r.status_code == 200)
        self.assertTrue(r.json()["currentPlayback"] == "secondPlayback")
        r = requests.post(baseURL + "playbacks", data={"currentPlayback":"secondPlayback"})
        
    def test_manualPosSet(self):
        r = requests.post(baseURL, data={"manual_x":50,"manual_y":55, "manual_z":66})      
        self.assertTrue(r.status_code == 200)
        r = requests.get(baseURL)
        self.assertTrue(r.status_code == 200)
        json = r.json()
        print ("JSON IS", json["manual_x"])
        self.assertTrue(json["manual_x"] == 50)
        self.assertTrue(json["manual_y"] == 55)
        self.assertTrue(json["manual_z"] == 66)
        r = requests.post(baseURL + "playbacks", data={"manual_x":0,"manual_y":0, "manual_z":0})  
        
    def test_play1(self):
        r = requests.post(baseURL, {"playback":True})      
        self.assertTrue(r.status_code == 200)         
        r = requests.get(baseURL)
        self.assertTrue(r.status_code == 200)
        print r.json()
        self.assertTrue(r.json()["currentState"] == "attract")
        r = requests.post(baseURL, {"playback":False}) 
             
def getPlaybacks():
    return hydraulics_playback.getPlaybackList()
    
if __name__ == "__main__":
    import requests
    import sys
    from multiprocessing import Process
    import event_manager
    import hydraulics_playback
    
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d: %(message)s', level=logging.DEBUG)
    try: 
        event_manager.init()
        hydraulics_playback.init("playback_tests2")
        httpd = BaseHTTPServer.HTTPServer(("", 9000), HydraulicsHandler)
        httpProcess = Process(target = httpd.serve_forever)
        httpProcess.start()
    
        unittest.main()
        print "TIMEOUT"
        
    except KeyboardInterrupt:
        pass
        
    httpProcess.terminate()
    hydraulics_playback.shutdown()
    event_manager.shutdown()
    
    
    # attract mode   
    # go into attract mode one shot - check inputs during and after recording
    # go into attract mode continuous - check inputs during and after recording
    # go into manual mode - Check inputs
    # record something - use manual controls
    # playback thing - check settings
    # delete the playback we just recorded
    
    
    # set, get mode
    # add playback
    # delete playback

        
