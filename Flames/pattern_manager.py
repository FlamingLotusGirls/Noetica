import logging
from threading import Lock
import sys
import poofermapping
import logging
import json
import copy

gPatterns = list()
patternLock = Lock()
patternFileName = None


logger = logging.getLogger('flames')

def init(flameEffectsFile):
    global patternFileName
    
    logger.info("Pattern Manager Init, sequence file {}".format(flameEffectsFile))
    patternFileName = flameEffectsFile
    patternNames = list()
    try:
        with open(flameEffectsFile) as f:
            savedPatterns = json.load(f)
            for pattern in savedPatterns:
                if not (pattern['name'] in patternNames):
                    if not _validatePattern(pattern):
                        logger.warn("Pattern {} does not validate, rejecting".format(pattern['name']))
                        continue
                    patternNames.append(pattern['name'])
                    gPatterns.append(pattern) 
                else:
                    logger.warn("Pattern name {} used twice".format(pattern['name']))
    except ValueError:
        logger.exception("Bad JSON in pattern file")
    except Exception:
        logger.exception("Unexpected error initializing pattern manager")
        
def shutdown():
    pass
    
def _validatePattern(pattern):
    if not "name" in pattern:
        logger.warn("Pattern has no name")
        return False
    
    if not "events" in pattern:
        logger.warn("Pattern {} has no events".format(pattern["name"]))
        return False
        
    if not "modifiable" in pattern:
        pattern["modifiable"] = False
        
    for event in pattern["events"]:
        if not "ids" in event:
            logger.warn("Pattern {} has no ids".format(pattern["name"]))
            return False
        for id in event["ids"]:
            if not id in poofermapping.mappings.keys():
                logger.warn("Pattern {} contains invalid id {}".format(pattern["name"], id))
                return False
        if not "duration" in event:
            logger.warn("Pattern {} has no duration".format(pattern["name"]))
            return False
        if not "startTime" in event:
            logger.warn("Pattern {} has no startTime".format(pattern["name"]))
            return False
    return True
        
def getPattern(patternName):
    returnPattern = None
    patternLock.acquire()
    for pattern in gPatterns:
        if pattern["name"] == patternName:
            returnPattern = pattern
    patternLock.release()
    return returnPattern
    
def getAllPatterns():
    patternLock.acquire()
    returnPattern = gPatterns
    patternLock.release()
    return returnPattern
    
def getPatternNames():
    patternNames = list()
    patternLock.acquire()
    for pattern in gPatterns:
        patternNames.append(pattern['name'])
    patternLock.release()
    return patternNames
    
def addOrModifyPattern(newPattern):
    patternName = newPattern['name']
    bFoundPattern = False
    for pattern in gPatterns:
        if pattern['name'] == patternName:
            bFoundPattern = True
            break
    if bFoundPattern:
        modifyPattern(newPattern)
    else:
        addPattern(newPattern)
    
        
def addPattern(newPattern): 
    if not _validatePattern(newPattern):
        log.warn("Pattern {} does nto validate, will not add".format(pattern['name']))
        return 
        
    patternLock.acquire()
    patternExists = False
    for pattern in gPatterns:
        if pattern["name"] == newPattern["name"]:
            patternExists = True
            break
    if patternExists:
        logger.warning("Cannot add pattern {}, pattern already exists".format(newPattern["name"]))
    else:
        gPatterns.append(newPattern)
    patternLock.release()
    
def modifyPattern(newPattern): 
    if not _validatePattern(newPattern):
        log.warn("Pattern {} does nto validate, will not modify".format(pattern['name']))
        return 
    patternLock.acquire()
    patternName = newPattern['name']
    foundPattern = None
    for pattern in gPatterns:
        if pattern['name'] == patternName:
            foundPattern = pattern
            break
    if not foundPattern:
        logger.warning("Could not find existing pattern {}, will not modify".format(patternName))
    elif foundPattern["modifiable"] != True:
        logger.warning("Pattern {} is not modifiable, will not modify".format(patternName))
    else:
        foundPattern["events"] = newPattern["events"]
    patternLock.release()
    
def deletePattern(patternName):
    foundPattern = None
    for pattern in gPatterns:
        if pattern['name'] == patternName:
            foundPattern = pattern
            break
    if not foundPattern:
        logger.warning("Could not find pattern {}, will not delete".format(patternName))
    else:
        gPatterns.remove(pattern)
    
    
def savePatterns(filename=None):
    if filename == None:
        filename = patternFileName
    with open(filename, 'w') as f: # open write 
        json.dump(gPatterns, f)
    
if __name__ == '__main__':
    print "pattern manager!"
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d: %(message)s', level=logging.DEBUG)
    if len(sys.argv) > 1:
        pattern_file = sys.argv[1]
    else:
        pattern_file = "pattern_test.json"
        
    init(pattern_file)
    
    pattern = getPattern("Bottom")
    modifiedPattern = copy.deepcopy(pattern)
    modifiedPattern["events"][0]["duration"] = 4000
    print "Original Pattern: ", pattern
    print "Modified Pattern: ", modifiedPattern
    modifyPattern(modifiedPattern)
    print "Original Pattern, modified", pattern
    addPattern({"modifiable": True, "name": "Custom", 
                "events": [{"duration": 2000, "ids": ["NE", "NW"], "startTime": 0}, 
                           {"duration": 2000, "ids": ["NE", "NW"], "startTime": 4000}]})
    addPattern({"modifiable": True, "name": "NE", 
                "events": [{"duration": 2000, "ids": ["NE", "NW"], "startTime": 0}, 
                           {"duration": 2000, "ids": ["NE", "NW"], "startTime": 4000}]})
    savePatterns("pattern_test_output.json")
    deletePattern("Custom")
    savePatterns("pattern_test_output_2.json")

  
    
    
        
    
        
    
