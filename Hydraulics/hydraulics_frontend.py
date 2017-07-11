#!/usr/bin/python

# Hydraulics test bed - HTTP/REST server

import BaseHTTPServer
import json
import hydraulics_drv
import hydraulics_playback

from cgi import parse_header, parse_multipart
from sys import version as python_version
if python_version.startswith('3'):
    from urllib.parse import parse_qs
else:
    from urlparse import parse_qs

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
        self.end_headers()
        self.wfile.write(json.dumps(data))
    
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
        else:
            print self.path
            pathArray = self.path[1:].split("/")
            print pathArray
            if (len(pathArray) >= 1 and pathArray[0] == "hydraulics"):
                if (len(pathArray) == 1):  # just 'hydraulics'
                    self.send200(getHydraulicsState())
                elif (len(pathArray) == 2 and pathArray[1] == "playbacks"):
                    self.send200(getPlaybacks())
                elif (len(pathArray) == 2 and pathArray[1] == "position"):
                    self.send200(getHydraulicsPosition())
                else:
                    self.sendError(404)
            else:
                self.sendError(404)

    def do_POST(self):
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
        if (len(pathArray) == 1):
            if (pathArray[0] == "hydraulics"):
                if "state" in postvars:
                    newState = postvars["state"][0]
                    hydraulics_drv.setState(newState)
                    self.send_response(200)
                if ("oldPlaybackName" in postvars and "newPlaybackName" in postvars):
                    oldName = postvars["oldPlaybackName"][0]
                    newName = postvars["newPlaybackName"][0]
                    hydraulics_playback.renamePlayback(oldName, newName)
                if ("currentPlayback" in postvars):
                    playback = postvars["currentPlayback"][0]
                    hydraulics_playback.setCurrentPlayback(playback)
                if ("record" in postvars):
                    doRecord = postvars["record"][0]
                    if doRecord.lower() == "true":
                        recordingFile = hydraulics_playback.getNewRecordingFile()
                        hydraulics_drv.startRecording(recordingFile)
                    else:
                        hydraulics_drv.stopRecording()
                if ("loopback_x" in postvars):
                    loopback_x = postvars["loopback_x"][0]
                    x,y,z = hydraulics_drv.getLoopbackValues()
                    print ("loopback_x set to", loopback_x)
                    hydraulics_drv.setLoopbackValues(loopback_x, y, z)
                if ("loopback_y" in postvars):
                    print postvars
                    loopback_y = postvars["loopback_y"][0]
                    print("loopback_y set to", loopback_y)
                    x,y,z = hydraulics_drv.getLoopbackValues()
                    hydraulics_drv.setLoopbackValues(x, loopback_y, z)
                if ("loopback_z" in postvars):
                    loopback_z = postvars["loopback_z"][0]
                    print("loopback_z set to", loopback_z);
                    x,y,z = hydraulics_drv.getLoopbackValues()
                    hydraulics_drv.setLoopbackValues(x, y, loopback_z)
                self.send_response(200)
            else:
                self.sendError(404)
        else:
            self.sendError(404)

def getHydraulicsState():
    control_x, control_y, control_z = hydraulics_drv.getCurrentInput()
    pid_x, pid_y, pid_z = hydraulics_drv.getVoltageInput()
    
    loopback_x, loopback_y, loopback_z = hydraulics_drv.getLoopbackValues()
    
    retObj = {}
    
    retObj["x"] = control_x
    retObj["y"] = control_y
    retObj["z"] = control_z
    retObj["pid_x"] = pid_x
    retObj["pid_y"] = pid_y
    retObj["pid_z"] = pid_z
    retObj["playbacks"]       = hydraulics_playback.getList()
    retObj["currentPlayback"] = hydraulics_playback.getCurrentPlayback()
    retObj["states"]          = hydraulics_drv.getAllStates()
    retObj["currentState"]    = hydraulics_drv.getState()
    retObj["isRecording"]     = hydraulics_drv.isRecording()
    retObj["loopback_x"]      = loopback_x
    retObj["loopback_y"]      = loopback_y
    retObj["loopback_z"]      = loopback_z
    
    return retObj
    
def getHydraulicsPosition():
    pos_x, pos_y, pos_z = hydraulics_drv.getCurrentInput()
    retObj = {}
    
    retObj["x"] = pos_x
    retObj["y"] = pos_y
    retObj["z"] = pos_z
    
    return retObj

    
def getPlaybacks():
    return hydraulics_playback.getList()
        
