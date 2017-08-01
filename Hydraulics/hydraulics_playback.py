#!/usr/bin/python

# Hydraulics playback
# manages playback data. Will read current playback into an array
# (and yes, this means that you can blow out memory if the playback data is too long)

import os
import datetime
import time
import logging

import hydraulics_drv

playbackList = []
playbackDir = "./playbacks/"
playbackData = [] 
playbackDataIdx = 0
currentPlayback = None
recordingFilename = None

# XXX - should the playback file specify the interval in which it is expected to run? Probably...
logger = logging.getLogger('playback')

def init(playbackDirectory=playbackDir, playbackName=None):
    global playbackDir
    global currentPlayback
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
        for i in range(len(playbackList)):
            fileName = playbackList[i]
            if not fileName.endswith(".rec"):
                badFiles.append(fileName)
            else:
                fileName = fileName[:-4]
                playbackList[i] = fileName
        
        for fileName in badFiles:
            playbackList.remove(fileName)
        
        if playbackName != None and playbackName in playbackList:
            setCurrentPlayback(playbackName)
            
        if currentPlayback == None and len(playbackList) > 0:
            setCurrentPlayback(playbackList[0])
    except Exception:
        logger.exception('Error initializing playback')
        
def shutdown():
    logger.info("Hydraulics playback shutdown")
        
def getList():
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

    hydraulics_drv.startRecording(_getNewRecordingFile())
    
def isRecording():
    return (recordingFilename == None)
    
def stopRecording():
    global recordingFilename
    hydraulics_drv.stopRecording()
    playbackList.append(recordingFilename)
    recordingFilename = None
    
def deleteRecording(recordingName):
    if recordingName in playbackList:
        os.remove(playbackDir + recordingName + ".rec")
        playbackList.remove(recordingName)
    else:
        log.warn("Recording file {} not found".format(recordingName))

    
def setCurrentPlayback(playbackName):
    ''' Read desired playback into memory, and set up internal cursor to the beginning
    of the playback'''
    global playbackData
    global currentPlayback
    try:
        if not playbackName in playbackList:
            return # XXX throw exception
        with open(playbackDir + "/" + playbackName + ".rec") as f:
            playbackData = map(int, f)
        playbackDataIdx = 0
        currentPlayback = playbackName
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
        
    return x, y, z
    
def _getNewRecordingFile():
    global recordingFilename 
    recordingFilename = time.strftime("%m-%d-%y__%H:%M:%S", time.gmtime())
    #now = datetime.date.today()
    file = open(playbackDir + recordingFilename + ".rec", "w+")
    return file
        
        
    
