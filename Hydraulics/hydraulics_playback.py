#!/usr/bin/python

# Hydraulics playback
# manages playback data. Will read current playback into an array
# (and yes, this means that you can blow out memory if the playback data is too long)

import os
import datetime
import hydraulics_drv
import time

playbackList = []
#playbackDir = "/home/flaming/Noetica/Hydraulics/playbacks/"
playbackDir = "./playbacks/"
playbackData = [] 
playbackDataIdx = 0
currentPlayback = None

def init():
    try: 
        # look at directory containing playback files. Read into an array
        global playbackList
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
        
        print playbackList
        if len(playbackList) > 0:
            setCurrentPlayback(playbackList[0])
    except Exception as e:
        print ('Error initializing playback', e)
        
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
        playbackList[i] = newName
    
def setCurrentPlayback(playbackName):
    ''' Read desired playback into memory, and set up internal cursor to the beginning
    of the playback'''
    global playbackData
    if not playbackName in playbackList:
        return # XXX throw exception
    with open(playbackDir + playbackName + ".rec") as f:
        playbackData = map(int, f)
    playbackDataIdx = 0
    currentPlayback = playbackName

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
    
def getNewRecordingFile():
    now = datetime.date.today()
    file = open(playbackDir + time.strftime("%d-%m-%y__%H:%M:%S", time.gmtime())+ ".rec", "w+")
    return file
        
        
    
