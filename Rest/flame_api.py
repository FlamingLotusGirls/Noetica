from flask import Flask
from flask import request
app = Flask("flg")

# GET /flame. Get status of all poofers, any active patterns. (Poofer status is [on|off], [enabled|disabled].)
# POST /flame playState=[pause|play]. Whole sculpture gross control. Pause/Play: Pause all poofing and flame effects (should terminate any current patterns, prevent any poofing until Play is called]
@app.route("/flame", methods=['GET', 'POST'])
def flame_status():
    if request.method == 'POST':
        control_flame()
    else:
        get_status()

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
    get_flame_patterns()

# POST /flame/patterns/<patternName> active=[true|false] enabled=[true|false]. Start an individual pattern (or stop it if it is currently running). Enable/disable a pattern
@app.route("/flame/patterns/{patternName}")
def flame_pattern():
    set_flame_pattern()
