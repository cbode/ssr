#!/usr/bin/env python
############################################################################
#
# MODULE:       ssr_utilities.py
# AUTHOR:       Collin Bode, UC Berkeley                March, 2012
#
# PURPOSE:      Various small utility functions for GRASS in python
#
# COPYRIGHT:    (c) 2012 Collin Bode
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# MODULES REQUIRED
import os
import sys
import re
import shutil
import platform
import datetime as dt
import grass.script as grass
import grass.script.setup as gsetup
from ssr_params import *

###############################################################
#
#   INSIDE FUNCTIONS:  These functions are run inside GRASS.
#
###############################################################

def printout(str_text,lf):
    timestamp = dt.datetime.strftime(dt.datetime.now(),"%H:%M:%S")
    lf.write(timestamp+": "+str_text+'\n')
    print timestamp+": "+str_text

def set_region(bregion,C):
    # remove g.region for normal runs
    if(bregion == "default" or bregion == "d"):
        grass.run_command("g.region", flags="d")            
    elif(bregion == "b5k"):
        grass.run_command("g.region", n=4400220.4, s=4395220.4, e=447761.8, w=442761.8,ewres=C,nsres=C) # b5k
    elif(bregion == "b8k"):
        grass.run_command("g.region", n=4401000.00, s=4393000.00, e=450000.00, w=442000.00,ewres=C,nsres=C) #b8k
    elif(bregion == "b9k"):
        grass.run_command("g.region", n=4401000.00, s=4392000.00, e=451000.00, w=442000.00,ewres=C,nsres=C) #b9k
    elif(bregion == "b10k"):
        grass.run_command("g.region", n=4401000.00, s=4391000.00, e=450000.00, w=440000.00,ewres=C,nsres=C) # b10k
    elif(bregion == "cahto"):
        grass.run_command("g.region", n=4398000.00, s=4392000.00, e=451000.00, w=448000.00,ewres=C,nsres=C) # cahto
    else:
        grass.run_command("g.region", flags="d")
        grass.run_command("g.region",ewres=C,nsres=C)

def mapset_gotocreate(mapset,bregion,C,lf):
    #grass.run_command("g.mapset","l")
    bmapexists = False
    mapset_list = grass.mapsets(False) 
    for map in mapset_list:
        grass.message(map)
        if(mapset == map):
            bmapexists = True
            #grass.message("FOUND! "+mapset+" = "+map)
    if(bmapexists == True):
        grass.run_command("g.mapset",mapset=mapset)
        printout('Changed mapsets to '+mapset,lf)
    else:  
        grass.run_command("g.mapset",flags="c",mapset=mapset)
        printout("Mapset didn't exist. Created then changed mapsets to "+mapset,lf)
    set_region(bregion,C)

def raster_exists(raster,mapset):
    #boocan = raster_exists(can,'PERMANENT')
    print '1 start'
    booexists = False
    print '2 list'
    raster_list = grass.list_grouped('rast')[mapset] 
    print '3 iteration'
    for rast in raster_list:
        print '4 ',rast
        if(rast == raster):
           booexists = True
           print '5 found a true'
    print '6 done with iter'
    return booexists
    print '7 returned'

		
###############################################################
#
#   OUTSIDE FUNCTIONS:  These functions are run outside
#   of a GRASS session.  Python is started from command line.
#
###############################################################
'''
def set_server_environment(lf): # OUTSIDE
    server_name = platform.uname()[1]
    if(server_name == 'ios.safl.umn.edu'):
        # Ios.safl.umn.edu
        gisbase = os.environ['GISBASE'] = "/usr/lib64/grass-6.4.1"		# Ios: Grass 6.4.1 from RPM
        #gisdbase = os.path.abspath("/ssd/collin_light/")
        gisdbase = os.path.abspath("/local/collin_light/")
    elif(server_name == 'pollux'):
        # Pollux
        gisbase = os.environ['GISBASE'] = "/usr/lib64/grass-6.4.2"		# Grass 6.4.2 from RPM
        gisdbase = os.path.abspath("/archive/grassdata/")
    elif(server_name == 'ubander'):
        # uBander with OpenCL
        gisbase = os.environ['GISBASE'] = "/usr/local/grass-7.0.svn/"	        # Grass 7.0svn
        gisdbase = os.path.abspath("/home/collin/grass/")
    elif(server_name == 'Bandersnatch'):
        gisbase = os.environ['GISBASE'] = "C:/Programs/GRASS/"
        gisdbase = os.path.abspath("S:/ssr/")        
    else:
        printout('WARNING! set_server_environment failed.  Unrecognized server_name. Quitting.',lf)
        exit()
    sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "python"))
    return gisbase,gisdbase
'''

def get_path():
    path = os.path.dirname(os.path.realpath(__file__))+os.sep
    return path


def create_temp(cores,bregion,lf): # OUTSIDE
        gsetup.init(gisbase, gisdbase, location, 'PERMANENT')
        for count in range(0,cores,1):
                temp = 'temp'+str(count).zfill(2)
                temp_path = gisdbase+'/'+location+'/'+temp
                if(os.path.exists(temp_path) == False):
                        grass.run_command("g.mapset",flags="c", mapset=temp, quiet=1)
                        set_region(bregion,C)
                        printout(temp+" mapset created.",lf)
                else:
                        printout(temp+" mapset already exists. skipping...",lf)


def remove_temp(cores): # OUTSIDE
        # setup is in the target mapset, not temp mapsets
        gsetup.init(gisbase, gisdbase, location, 'PERMANENT')
        # Delete the temp mapset
        for count in range(0,cores):
                mapset_temp = 'temp'+str(count).zfill(2)
                grass.run_command("g.mapsets", removemapset=mapset_temp)
                temp_path = gisdbase+'/'+location+'/'+mapset_temp
                shutil.rmtree(temp_path)
                

def copy_fromtemp(cores,mapset_to,suffixes,overwrite,lf):  # OUTSIDE
        gsetup.init(gisbase, gisdbase, location, mapset_to)
        for count in range(0,cores):
                # Switch to temp mapset
                mapset_temp = 'temp'+str(count).zfill(2)
                grass.run_command("g.mapset", mapset=mapset_temp, quiet=1)
                # list contents of temp mapset
                raster_list = grass.list_pairs(type = 'rast')
                # Switch to target mapset and copy rasters over
                grass.run_command("g.mapset", mapset=mapset_to,quiet=0)
                for regfilter in suffixes:
                        for rast in raster_list:
                                if(rast[1] != 'PERMANENT' and re.search(regfilter,rast[0])):
                                        old = rast[0]+ '@' + rast[1]
                                        new = rast[0]
                                        cmd = old+","+new
                                        printout("g.copy, rast="+cmd+", overwrite="+str(overwrite),lf)
                                        grass.run_command("g.copy", rast=cmd, overwrite=overwrite)


def copy_mapset(mapset_from,mapset_to,regfilter,overwrite,lf):      # OUTSIDE
        gsetup.init(gisbase, gisdbase, location, mapset_from)
        #grass.run_command("g.mapset", mapset=mapset_from, quiet=1)
        # list contents of temp mapset
        raster_list = grass.list_pairs(type = 'rast')
        # Switch to target mapset and copy rasters over
        grass.run_command("g.mapset", mapset=mapset_to,quiet=0)
        for rast in raster_list:
                if(rast[1] != 'PERMANENT' and re.search(regfilter,rast[0])):
                        old = rast[0]+ '@' + rast[1]
                        new = rast[0]
                        cmd = old+","+new
                        printout("g.copy, rast="+cmd+", overwrite="+str(overwrite),lf)
                        grass.run_command("g.copy", rast=cmd, overwrite=overwrite)


