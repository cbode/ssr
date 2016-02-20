#!/bin/bash
####################################################
# ssr_run_all.sh
# by Collin Bode, 2016
# purpose: linux shell script to launch all parts 
# of the Subcanopy Solar Radiation model in order.
# Make sure all run_parts have 2 or 1 values.
#
####################################################
python ssr_lidar.py
python ssr_lpi.py
python ssr_rsun.py
python ssr_algore.py
