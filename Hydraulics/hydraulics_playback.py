#!/usr/bin/python

# Hydraulics playback
# manages playback data. Will read current playback into an array
# (and yes, this means that you can blow out memory if the playback data is too long)

import os
import datetime
import time
import logging
from threading import Lock

import event_manager
import hydraulics_drv

playbackList = []
playbackDir = "./playbacks/"
playbackData = [] 
playbackDataIdx = 0
currentPlayback = None
recordingFilename = None
recordingStopTime = 0
recordingFile = None
recordingSources = "sculpture, controller"
recordingSource = "controller"
fileMutex = Lock()

# XXX - should the playback file specify the interval in which it is expected to run? Probably...
logger = logging.getLogger('playback')

def init(playbackDirectory=playbackDir, playbackName=None):
    global playbackDir
    global currentPlayback
    global recordingSource
    logger.info("Hydraulics playback init, playback dir {}, file {}".format(playbackDirectory, playbackName))
    playbackDir = playbackDirectory
    currentPlayback = None
    try: 
        # look at directory containing playback files. Read into an array
        global playbackList

        # if playbacks folder doesn't exist, create one
        if not os.path.exists(playbackDir):
            os.makedirs(playbackDir)

        playbackList = os.listdir(playbackDir)
        badFiles = []
        potentialCurrentPlayback = None
        for i in range(len(playbackList)):
            fileName = playbackList[i]
            if not fileName.endswith(".rec"):
                badFiles.append(fileName)
            elif fileName == "currentPlayback.rec":
                potentialCurrentPlayback = os.path.realpath(playbackDir + "/currentPlayback.rec")
                badFiles.append(fileName)
            else:
                fileName = fileName[:-4]
                playbackList[i] = fileName
                
        for fileName in badFiles:
            playbackList.remove(fileName)
        
        if playbackName != None and playbackName in playbackList:
            setCurrentPlayback(playbackName)
        elif potentialCurrentPlayback != None and potentialCurrentPlayback in playbackList:
            setCurrentPlayback(potentialCurrentPlayback)
            
        if currentPlayback == None and len(playbackList) > 0:
            setCurrentPlayback(playbackList[0])
            
        event_manager.addListener(_eventHandler, "pos")
        setRecordingSource("controller")
        
    except Exception:
        logger.exception('Error initializing playback')
        
def shutdown():
    logger.info("Hydraulics playback shutdown")
    stopRecording()
        
def getPlaybackList():
    ''' Return list of all available recorded sequences (playbacks)'''
    return playbackList
    
def renamePlayback(oldName, newName):
    ''' Rename a playback. Necessary since by default playbacks are named with a timestamp'''
    global playbackList
    if not oldName in playbackList:
        return # XXX throw exception
    if os.path.isfile(playbackDir + oldName + ".rec"):
        os.rename(playbackDir + oldName + ".rec", playbackDir + newName + ".rec")
    for i in range(len(playbackList)):
        if playbackList[i] == oldName:
            playbackList[i] = newName
            break
            
def startRecording():
    global recordingFile
    global recordingFilename
    global recordingStopTime
    if recordingFile != None:
        log.warning("Recording file already exists!")
        raise Exception("Recording file already exists!")
    
    recordingFile, recordingFilename = _getNewRecordingFile()
    recordingStopTime = time.time() + 30 # maximum recording time 30 seconds.
    logger.info("Start recording to file {}".format(recordingFile)) 
        

def setRecordingSource(source):
    global recordingSource
    if source in recordingSources:
        recordingSource = source
    else:
        logger.warning("Attempting to set invalid recording source {}, ignoring".format(source))

def getRecordingSource():
    return recordingSource
    
def getRecordingSources():
    return recordingSources
    
def _eventHandler(msg):
    if ((recordingFilename != None) and (msg["msgType"] == "pos")):
        if recordingStopTime > time.time():
            if recordingSource == "sculpture":
                x = msg["xx"] 
                y = msg["yy"]
                z = msg["zz"]
            else: # recording controller position
                x = msg["x"] 
                y = msg["y"]
                z = msg["z"]
            
            fileMutex.acquire()
            recordingFile.write("%03f\n%03f\n%03f\n" % (x,y,z))
            fileMutex.release() 
        else:
            logger.info("Timeout - Auto stopping recording")
            stopRecording()
            
def stopRecording():
    global recordingFile
    global recordingFilename

    logger.info("Stopping Recording")

    if recordingFile != None:
        fileMutex.acquire()
        recordingFile.close()
        fileMutex.release()
        recordingFile = None
    
    if recordingFilename != None:
        playbackList.append(recordingFilename)
        recordingFilename = None    
       

def isRecording():
    return (recordingFilename != None)
    
def deleteRecording(recordingName):
    if recordingName in playbackList:
        os.remove(playbackDir + recordingName + ".rec")
        playbackList.remove(recordingName)
    else:
        log.warn("Recording file {} not found".format(recordingName))

    
def setCurrentPlayback(playbackName):
    ''' Read desired playback into memory, and set up internal cursor to the beginning
    of the playback. Also link to playback file from currentPlayback.rec'''
    global playbackData
    global currentPlayback
    try:
        if not playbackName in playbackList:
            return # XXX throw exception
        with open(playbackDir + "/" + playbackName + ".rec") as f:
            playbackData = map(float, f)
        playbackDataIdx = 0
        currentPlayback = playbackName
        try:
            os.remove(playbackDir + "/currentPlayback.rec")
        except OSError:
            pass # 
        os.symlink(playbackName + ".rec", playbackDir + "/currentPlayback.rec")
    except IOError:
        logger.warn("Playback file {} not found".format(playbackName))

def getCurrentPlayback():
    ''' Get name of current playback'''
    return currentPlayback
        
def getPlaybackData():
    ''' Returns x,y,z of current playback data. There is an internal cursor to
        the current data, so this function can be called repeatedly to run through
        the playback'''
    global playbackDataIdx
    x = 0
    y = 0
    z = 0
    try:
        x = playbackData[playbackDataIdx]
        y = playbackData[playbackDataIdx + 1]
        z = playbackData[playbackDataIdx + 2]
    except IndexError:
        pass
        
    playbackDataIdx = playbackDataIdx + 3
    if (len(playbackData) <= playbackDataIdx):
        playbackDataIdx = 0
#        logger.info("End of playback data. May wrap. May not")
        # XXX - message to system - end of playback. Can trigger playback stop
        
#    logger.debug("Playback returns {} {} {}, idx is {}, playback file is {}".format(x,y,z, playbackDataIdx, currentPlayback))
    return x, y, z
    
def _getNewRecordingFile():
    filename = time.strftime("%m-%d-%y__%H:%M:%S", time.gmtime())
    file = open(playbackDir + filename + ".rec", "w+")
    return file, filename
     
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d:  %(message)s', level=logging.DEBUG)
    try: 
        event_manager.init()
        hydraulics_drv.init()
        init()
    
        startRecording()
        time.sleep(40)
    except KeyboardInterrupt:
        pass
    except Exception:
        logger.exception("Unexpected exception in test")
    
    shutdown()
    hydraulics_drv.shutdown()
    event_manager.shutdown()   
        
    
