# skeleton for API
# To run: 'FLASK_APP=flame_api.py flask run'

from flask import Flask
from flask import request
import json
import logging

import flames_highlevel
import poofermapping

PORT = 5000

logger = logging.getLogger("flames")

app = Flask("flg", static_url_path='')

def serve_forever(httpPort=PORT):
    logger.info("Serving forever at port %s".format(httpPort))
    app.run(host="0.0.0.0", port=httpPort)

# GET /flame. Get status of all poofers, any active patterns. (Poofer status is [on|off], [enabled|disabled].)
# POST /flame playState=[pause|play]. Whole sculpture gross control. Pause/Play: Pause all poofing and flame effects (should terminate any current patterns, prevent any poofing until Play is called]
@app.route("/flame", methods=['GET', 'POST'])
def flame_status():
    if request.method == 'POST':
        playState = request.values["playState"]
        if playState != None:
            playState = playState.lower()
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
        return json.dumps(get_status()), 200

# GET /flame/poofers/<poofername>. Get status of particular poofer
# POST /flame/poofers/<poofername> enabled=[true|false]. Set enabled state for individual poofers
@app.route("/flame/poofers/{poofer_id}", methods=['GET', 'POST'])
def specific_flame_status():
    if not poofer_id_Valid(poofer_id):
        abort(400)
    if request.method == 'POST':
        enabled = request.values["enabled"]
        if enabled == None:
            abort(400)
        enabled = enabled.lower()
        if enabled == 'true':
            flames_highlevel.enablePoofer(poofer_id)
        elif enabled == 'false':
            flames_highlevel.disablePoofer(poofer_id)
        else:
            abort(400)
            
        return "" # XXX check for errors as a matter of course
    else:
        return json.dumps(get_poofer_status(poofer_id))

# GET /flame/patterns. Get list of all flame patterns, whether active or not
@app.route("/flame/patterns", methods=['GET'])
def flame_patterns():
    return json.dumps(get_flame_patterns())

# POST /flame/patterns/<patternName> active=[true|false] enabled=[true|false]. Start an individual pattern (or stop it if it is currently running). Enable/disable a pattern
@app.route("/flame/patterns/{patternName}", methods=['GET', 'POST'])
def flame_pattern(): 
    if  not patternName_valid(patternName):
        abort(400)
        
    if request.method == 'POST':
        enabled = request.values["enabled"]
        active = request.values["active"]
        enabledValid = param_valid(enabled, ["true", "false"])
        activeValid = param_valid(active, ["true", "false"])
        
        if (not enabledValid and not activeValid):
            abort(400)
        
        if enableValid:
            enabled = enabled.lower()
            if (enabled == "true"):
                flames_highlevel.enableFlameEffect(patternName)
            elif (enabled == "false"):
                flames_highlevel.enableFlameEffect(patternName)
        if activeValid:
            active = active.lower()
            if (active == "true"):
                flames_highlevel.doFlameEffect(patternName)
            elif (active == "false"):
                flames_highlevel.stopFlameEffect(patternName)
    
        return ""
        
    else:
        return json.dumps(get_pattern_status(patternName))

def get_status():
    pooferList = list()
    patternList = list()
    for pooferId in poofermapping.mappings:
        pooferList.append({"id" : pooferId, 
                           "enabled": flames_highlevel.isPooferEnabled(pooferId),
                           "active" : flames_highlevel.isPooferActive(poofer_id)})
    for patternName in flames_highlevel.getFlameEffects():
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
    return flames_highlevel.getFlameEffects()

    
def poofer_id_valid(id):
    return id in poofermapping.mappings
    
def patternName_valid(patternName):
    return patternName in flames_highlevel.getFlameEffects()
    
def param_valid(value, validValues):
    return value != None and value.lower() in validValues

    
if __name__ == "main":
    serve_forever()
    

    
