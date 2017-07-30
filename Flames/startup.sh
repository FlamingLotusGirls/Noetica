#!/bin/bash
HOME=/home/flaming
CFGFILE=$HOME/Noetica/noetica.cfg
FLAMES=$HOME/Noetica/Flames/flames.py
FLAMES_LOG=/var/log/flames.log

CYCLELOGS=$HOME/Noetica/cycleLogs.sh

$CYCLELOGS $FLAMES_LOG

# start flames code
stdbuf -oL $FLAMES $CFGFILE >& $FLAMES_LOG &

