# skeleton for API
# To run: 'FLASK_APP=flame_api.py flask run'

from flask import Flask
from flask import request
from flask import Response
import json
import logging

import flames_highlevel
import poofermapping
import pattern_manager

PORT = 5000

logger = logging.getLogger("flames")

app = Flask("flg", static_url_path='')

def serve_forever(httpPort=PORT):
    logger.info("FLAME WebServer: port {}".format(httpPort))
    app.run(host="0.0.0.0", port=httpPort)

# GET /flame. Get status of all poofers, any active patterns. (Poofer status is [on|off], [enabled|disabled].)
# POST /flame playState=[pause|play]. Whole sculpture gross control. Pause/Play: Pause all poofing and flame effects (should terminate any current patterns, prevent any poofing until Play is called]
@app.route("/flame", methods=['GET', 'POST'])
def flame_status():
    if request.method == 'POST':
        if playState in request.values:
            playState = request.values["playState"].lower()
            if playState == "pause":
                flames_highlevel.globalPause()
            elif playState == "play":
                flames_highlevel.globalRelease()
            else:
                abort(400)
        else:
            abort(400)
        return "", 200
        
    else:
        return makeJsonResponse(json.dumps(get_status()))
        
def makeJsonResponse(jsonString, respStatus=200):
    print "JSON RESPONSE data is", jsonString
    resp = Response(jsonString, status=respStatus, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


# GET /flame/poofers/<poofername>. Get status of particular poofer
# POST /flame/poofers/<poofername> enabled=[true|false]. Set enabled state for individual poofers
@app.route("/flame/poofers/{poofer_id}", methods=['GET', 'POST'])
def specific_flame_status():
    if not poofer_id_Valid(poofer_id):
        abort(400)
    if request.method == 'POST':
        if not "enabled" in request.values:
            abort(400)
            
        enabled = request.values["enabled"].lower()
        if enabled == 'true':
            flames_highlevel.enablePoofer(poofer_id)
        elif enabled == 'false':
            flames_highlevel.disablePoofer(poofer_id)
        else:
            abort(400)
            
        return "" # XXX check for errors as a matter of course
    else:
        return makeJsonResponse(json.dumps(get_poofer_status(poofer_id)))

# GET /flame/patterns. Get list of all flame patterns, whether active or not
@app.route("/flame/patterns", methods=['GET','POST'])
def flame_patterns():
    if request.method == 'GET':
        return makeJsonResponse(json.dumps(get_flame_patterns()))
    else:
        if not "patternData" in request.values:
            abort(400)
        set_flame_pattern(request.values["patternData"])
        
    



@app.route("/flame/patterns/{patternName}", methods=['GET', 'POST'])
def flame_pattern(): 
    ''' POST /flame/patterns/<patternName> active=[true|false] enabled=[true|false]. Start an 
    individual pattern (or stop it if it is currently running). Enable/disable a pattern. 
    Also, create or modify an existing pattern'''
    includesPattern = "pattern" in request.values 
    includesEnabled = "enabled" in request.values
    includesActive  = "active"  in request.values
    
    if request.method == 'POST':
        # pattern create - pattern data included, but pattern name not in system
        if  (not includesPattern) and (not patternName_valid(patternName)):
            abort(400)
            
        if includesPattern:
            patternData = json.loads(request.values["pattern"])
            oldPatternData = None
            for pattern in patternList:
                if pattern["name"] == patternData["name"]:
                    oldPatternData = pattern
                    break;
            if oldPatternData == None:
                patternList.append(patternData)
            else:
                oldPatternData["events"] = patternData["events"]
            savePatternData()
        
        if includesEnabled:
            enabled = request.values["enabled"].lower()
            enabledValid = param_valid(enabled, ["true", "false"])
        else:
            enabledValid = False
        if includesActive:
            active = request.values["active"].lower()
            activeValid = param_valid(active, ["true", "false"])
        else:
            activeValid = False
        
        if (not enabledValid and not activeValid):
            abort(400)
        
        if enableValid:
            if (enabled == "true"):
                flames_highlevel.enableFlameEffect(patternName)
            elif (enabled == "false"):
                flames_highlevel.enableFlameEffect(patternName)
        if activeValid:
            if (active == "true"):
                flames_highlevel.doFlameEffect(patternName)
            elif (active == "false"):
                flames_highlevel.stopFlameEffect(patternName)
    
        return ""
        
    else:
        if  (not patternName_valid(patternName)):
            abort(400)
        return makeJsonResponse(json.dumps(get_pattern_status(patternName)))

def get_status():
    pooferList = list()
    patternList = list()
    for pooferId in poofermapping.mappings:
        pooferList.append({"id" : pooferId, 
                           "enabled": flames_highlevel.isPooferEnabled(pooferId),
                           "active" : flames_highlevel.isPooferActive(poofer_id)})
    for patternName in pattern_manager.getPatternNames():
        patternList.append({"name" : patternName,
                            "enabled": flames_highlevel.isFlameEffectEnabled(patternName),
                            "active" : flames_highlevel.isFlameEffectActive(patternName)})
    return {"globalState": (not flames_highlevel.isStopped()), 
            "poofers":pooferList, 
            "patterns":patternList }
                    
        

def get_poofer_status(poofer_id):
    # there's enabled, and there's active (whether it's currently on)
    pooferStatus = {"enabled": flames_highlevel.isPooferEnabled(poofer_id),
                    "active" : flames_highlevel.isPooferActive(poofer_id)}
    return pooferStatus
    
def get_pattern_status(patternName):
    patternStatus = {"enabled": flames_highlevel.isFlameEffectEnabled(patternName),
                     "active" : flames_highlevel.isFlameEffectActive(patternName)}
    return patternStatus

def get_flame_patterns():
    return pattern_manager.getAllPatterns()
    
# abort 500 in general? how are errors expected to be propagated in this framework?s
def set_flame_pattern(pattern):
    pattern_manager.addOrModifyPattern(pattern)
    pattern_manager.savePatterns()
    
def poofer_id_valid(id):
    return id in poofermapping.mappings
    
def patternName_valid(patternName):
    return patternName in pattern_manager.getPatternNames()
    
def param_valid(value, validValues):
    return value != None and (value.lower() in validValues)

    
if __name__ == "main":
    serve_forever()
    

    
