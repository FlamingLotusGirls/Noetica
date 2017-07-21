HOME=/home/flaming
CFGFILE=$HOME/Noetica/noetica.cfg
HYDRAULICS=$HOME/Noetica/Hydraulics/hydraulics.py
HYDRAULICS_LOG=/var/log/hydraulics.log

CYCLELOGS=$HOME/Noetica/cycleLogs.sh

$CYCLELOGS $HYDRAULICS_LOG

# start hydraulics code
stdbuf -oL $HYDRAULICS $CFGFILE >& $HYDRAULICS_LOG &

