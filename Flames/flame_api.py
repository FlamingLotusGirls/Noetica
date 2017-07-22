# skeleton for API
# To run: 'FLASK_APP=flame_api.py flask run'

from flask import Flask
from flask import request
import json
import logging

import flames_highlevel

PORT = 5000

logger = logging.getLogger("flames")

app = Flask("flg", static_url_path='')

def serve_forever(httpPort=PORT):
    logger.warn("Serving forever at port %s".format(httpPort))
    app.run(host="0.0.0.0", port=httpPort)

# GET /flame. Get status of all poofers, any active patterns. (Poofer status is [on|off], [enabled|disabled].)
# POST /flame playState=[pause|play]. Whole sculpture gross control. Pause/Play: Pause all poofing and flame effects (should terminate any current patterns, prevent any poofing until Play is called]
@app.route("/flame", methods=['GET', 'POST'])
def flame_status():
    if request.method == 'POST':
        return control_flame()
        
    else:
        return json.dumps(get_status())

# GET /flame/poofers/<poofername>. Get status of particular poofer
# POST /flame/poofers/<poofername> enabled=[true|false]. Set enabled state for individual poofers
@app.route("/flame/poofers/{poofer_id}", methods=['GET', 'POST'])
def specific_flame_status():
    if request.method == 'POST':
        set_flame_status()
    else:
        get_flame_status()

# GET /flame/patterns. Get list of all flame patterns, whether active or not
@app.route("/flame/patterns")
def flame_patterns():
    return json.dumps(get_flame_patterns())

# POST /flame/patterns/<patternName> active=[true|false] enabled=[true|false]. Start an individual pattern (or stop it if it is currently running). Enable/disable a pattern
@app.route("/flame/patterns/{patternName}")
def flame_pattern():
    set_flame_pattern()

def control_flame():
    return "control_frame"

def get_status():
    return "get_status"

def set_flame_status():
    return "set_flame_status"

def get_flame_status():
    return "get_flame_status"

def get_flame_patterns():
    return flames_highlevel.getFlameEffects()

def set_flame_pattern():
    return "set_flame_pattern"
    
if __name__ == "main":
    serve_forever()
    
