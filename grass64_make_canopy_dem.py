#!/usr/bin/env python
############################################################################
#
# MODULE:       grass_make_canopy_dem.py
# AUTHOR:       Collin Bode, UC Berkeley
#               based on ssr_lidar.py
# PURPOSE:
# 	1. Accept xyz unfiltered LiDAR files and import them into GRASS gis as
#          raster tiles.  Uses max value (elevation) for aggregation.
# 	2. Merge tiles into single raster and delete tiles.
#       NOTE: this is intended to be a standalone script. It does not use the
#       parameter file from ssr.
#
# DEPENDENCIES: ssr_utilities.py
#
# COPYRIGHT:    (c) 2015 Collin Bode
#		(c) 2006 Hamish Bowman, and the GRASS Development Team
#               (c) 2008 Glynn Clements, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
# GLOBALS
global lf
global cores
global gisbase
global gisdbase

#----------------------------------------------------------------------------
# GENERAL PARAMETERS
# GRASS GIS requires 4 inputs to start: 
# GIS BASE (GISBASE): path to GRASS binaries. Set automatically in ssr_utilities.py
gisbase = '/usr/lib64/grass-6.4.4'		# Ios: Grass 6.4.1 from RPM
# DATABASE (GISDBASE): A directory (folder) on disk to contain all GRASS maps and data. 
#                     Set automatically in ssr_utilities.py
gisdbase = '/data/grass_workspace'               # Eddy-the-server: GRASS GIS workspace
# LOCATION (loc): This is the name of a geographic location. It is defined by a
#          co-ordinate system and a rectangular boundary.  This is the name of the directory.
loc = location = 'angelo2014'                     

# MAPSET:   Each GRASS session runs under a particular MAPSET. This consists of
#          a rectangular REGION and a set of maps. See bottom of params for mapsets.
C = '1' #'30' #'2'              # cell size in meters
P = loc+C+'m'                   
bregion = 'default'		        # boundary used in g.region: b5k,b8k,b10,default
pref = bregion + C + 'm'        # used as name prefix when g.region is not default
	
#----------------------------------------------------------------------------
# LIDAR IMPORT PARAMETERS
# LiDAR downloaded from http://opentopography.org.
# National Center for Airborne Laser Mapping (NCALM) distributes laser hits as 2 datasets:  total and ground filtered.
year = 'y14'	        # Year the LiDAR was flown 2004 'y04', 2004 modified to match y09 'ym4',2009 'y09'
inPath='/data/source/LiDAR/2014_EelBathymetry_LiDAR/Angelo/Tiles_ASCII_xyz/unfiltered/' # y14
#inPath='/data/source/LiDAR/2009_SFEel_LiDAR/ascii/unfiltered/'                         # y09
#inPath='/data/source/LiDAR/2004_SFEel_LiDAR/TerraScan_EEL/laser_export/all/'           # y04
inSuffix='xyz'                          # filename suffix to filter for
sep = ','				# separator in lidar files ' ' or ','
overlap = float(0.00)			# tile overlap in meters
pmaxpref = 'pmax_c'+str(C)+year		# prefix to the point rasters

#----------------------------------------------------------------------------
# MAP NAMES
dem = P + 'dem'              # source map: bare-earth dem
can = P + 'can'              # source map: canopy dem
vegheight = P + 'vegheight'  # vegetation height

#----------------------------------------------------------------------------
# MAPSETS 
mapset = mlpi = 'canopy'                           # lpi mapset  


# MODULES
# GRASS & SSR environment setup for external use
import os
import sys
import re
import shutil
import platform
import datetime as dt
gisdbase = os.path.abspath(gisdbase)
os.environ['GISBASE'] = gisbase
sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "python"))
import grass.script as grass
import grass.script.setup as gsetup
# ssr_utilities must go after grass.script imports
#from ssr_utilities import *

def printout(str_text,lf):
    timestamp = dt.datetime.strftime(dt.datetime.now(),"%H:%M:%S")
    lf.write(timestamp+": "+str_text+'\n')
    print timestamp+": "+str_text

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

def set_region(bregion,C):
    # remove g.region for normal runs
    if(bregion == "default"):
        grass.run_command("g.region", flags="d")            
    elif(bregion == "b5k"):
        grass.run_command("g.region", n=4400220.4, s=4395220.4, e=447761.8, w=442761.8,ewres=C,nsres=C) # b5k
    elif(bregion == "b8k"):
        grass.run_command("g.region", n=4400800.00, s=4392800.00, e=451000.00, w=443000.00,ewres=C,nsres=C) #b8k
    elif(bregion == "b9k"):
        grass.run_command("g.region", n=4401000.00, s=4392000.00, e=451000.00, w=442000.00,ewres=C,nsres=C) #b9k
    elif(bregion == "b10k"):
        grass.run_command("g.region", n=4401000.00, s=4391000.00, e=450000.00, w=440000.00,ewres=C,nsres=C) # b10k
    elif(bregion == "cahto"):
        grass.run_command("g.region", n=4398000.00, s=4392000.00, e=451000.00, w=448000.00,ewres=C,nsres=C) # cahto
    else:
        grass.run_command("g.region", flags="d")
        grass.run_command("g.region",ewres=C,nsres=C)


def main():
    gsetup.init(gisbase, gisdbase, location, 'PERMANENT')
    ##################################
    # Import ASCII files
    ##################################
    # Open log file
    tlog = dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d_h%H")
    lf = open('rsun_'+tlog+'.log', 'a')
    
    printout("STARTING CANOPY DEM CREATION",lf)
    printout("LOCATION: "+loc,lf)
    printout("LiDAR year: "+year,lf)
    printout('pref: '+pref,lf)
    printout('LPI mapset: '+mlpi,lf)
    printout("Point Cloud Path: "+inPath,lf)
    printout("Point Cloud ",lf)
    printout("Point Cloud File Prefix: "+pmaxpref,lf)
    printout("Point Cloud File Suffix: "+inSuffix,lf)
    printout("Point Cloud File Separator: "+sep,lf)
    printout("Point Cloud Tile Overlap (meters): "+str(overlap),lf)

    printout('_________________________________',lf)
	
    # Point to raster import
    L2start = dt.datetime.now()
    printout('START LiDAR point cloud import',lf)
    
    # Mapset and Region Defined
    mapset_gotocreate(mlpi,'default',C,lf)

    #################################################
    patch_list = ''
    i = 0
    for strFile in os.listdir(inPath):
        printout("checking "+strFile,lf)
        t = strFile.split('.')
	#printout("t[0]="+t[0]+", t[1] = "+t[1],lf)
        if(len(t) > 1 and t[1] == inSuffix):
            tile=t[0]
            fstart = dt.datetime.now()
            printout("Importing: "+strFile+" as "+tile,lf)
            # n=4399092 s=4396972 e=446782 w=444662 b=365 t=754
            str_boundary = grass.read_command("r.in.xyz", flags = "sg", input = inPath+strFile, fs = sep, output = "temp")
            printout("boundary: "+str_boundary,lf)
            boundary = str_boundary.split(' ')
            tn = (boundary[0].split('='))[1]
            ts = (boundary[1].split('='))[1]
            te = (boundary[2].split('='))[1]
            tw = (boundary[3].split('='))[1]
            tb = (boundary[4].split('='))[1]
            tt = (boundary[5].split('='))[1]
            grass.run_command("g.region", overwrite = "true", n=tn, s=ts, e=te, w=tw, b=tb, t=tt)
            printout("set region to boundary",lf)
            grass.run_command("r.in.xyz", overwrite = "true", input = inPath+strFile, output = tile,type="FCELL", fs= sep, method="max")
            printout("r.in.xyz import finished for "+tile,lf)
            
            # clip tile, remove overlap
            otn = float(tn) - overlap
            ots = float(ts) + overlap
            ote = float(te) - overlap
            otw = float(tw) + overlap
            grass.run_command("g.region", n = otn, s = ots, w = otw, e = ote)
            printout("set region to clip",lf)
            
            ctile = 'c'+tile
            grass.run_command("g.rename",rast=tile+","+ctile)
            #grass.run_command("r.mapcalc", overwrite = "true", expression = ctile+" = "+tile)
            #printout("clipped "+tile,lf)

	    # delete unclipped tile
            #grass.run_command("g.remove", flags = "f", rast = tile)
            #printout("deleted unclipped tile, "+tile,lf)
            
            # append list of tiles to merge
            if(i == 0):
                patch_list = ctile
            else:
                patch_list += ","+ctile
            i = i + 1
            printout("Finished importing XYZ tiles!",lf)
                
    # Mosaic all the tiles into one map
    printout("Mosaic all tiles into one map",lf)
    grass.run_command("g.region", flags = "d") # go back to default mapset
    pointdensity = pmaxpref+pref
    grass.run_command("r.patch", overwrite = "true", input = patch_list, output= pointdensity)
    # Delete the clipped tiles, leaving only a completed point densitymap
    ctile_list = patch_list.split(',')
    for ctile in ctile_list:
        grass.run_command("g.remove", flags = "f", rast = ctile)
    printout("Done with "+pref,lf)
    
    
    #################################################
    # Finish
    set_region('default',C)
    
    L2end = dt.datetime.now()
    L2processingtime = L2end - L2start
    printout("DONE with LiDAR import, processing time: "+str(L2processingtime),lf)
    printout("--------------------------------------",lf)
    sys.exit("FINISHED.")

if __name__ == "__main__":
    main()
    '''
        try:
                #options, flags = grass.parser()
                main()
        except:
                printout('ERROR! quitting.')
                print traceback.print_exc()
                traceback.print_exc(file=lf)
                
        finally:
                lf.close()
                sys.exit("FINISHED.")
    '''
