#!/usr/bin/env python
############################################################################
#
# MODULE:       ssr_lidar.py
# AUTHOR:       Collin Bode, UC Berkeley
#               ssr_lpi and ssr_lidar used to be merged. Now separated.
# PURPOSE:
# 	1. Accept ASCII xyz LiDAR files (filtered & unfiltered) and import them into GRASS gis as raster.
#   	   This assumes filenames include an indicator that allows you to match filtered to unfiltered.
# 	2. Calculate point density using an asymetric nearest neighbor box.
#       3. Calculate Canopy raster using point maximum.  Requires cansource = '' in ssr_parameter file.
#
# COPYRIGHT:    (c) 2011 Collin Bode
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

# MODULES
# GRASS & SSR environment setup for external use
from ssr_params import *
import os
import sys
gisdbase = os.path.abspath(gisdbase)
os.environ['GISBASE'] = gisbase
sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "python"))
import grass.script as grass
import grass.script.setup as gsetup
# ssr_utilities must go after grass.script imports
from ssr_utilities import *


def main():
    gsetup.init(gisbase, gisdbase, location, 'PERMANENT')
    ##################################
    # Light Penetration Index (LPI)
    ##################################
    # Open log file
    tlog = dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d_h%H")
    lf = open(gisdbase+os.sep+'ssr_'+tlog+'_lidar.log', 'a')
    #mlpi = 'lpi'    # <-- debug remove
    boocan = False
    if(cansource == ''):
        boocan = True

    printout("STARTING LPI RUN",lf)
    printout("LOCATION: "+location,lf)
    printout("LiDAR year: "+year,lf)
    printout('Prefix: '+P,lf)
    printout("LPI pref: "+lpipref,lf)
    printout('LPI mapset: '+mlpi,lf)
    printout("Point Cloud ",lf)
    printout("Point Cloud Path: "+inPath,lf)
    printout("Point Cloud Ground,Total Directories: "+LidarPoints[0]+" , "+LidarPoints[1],lf)
    printout("Point Cloud File Prefix: "+pdensitypref,lf)
    printout("Point Cloud File Suffix: "+inSuffix,lf)
    printout("Point Cloud File Separator: "+sep,lf)
    printout("Point Cloud Tile Overlap (meters): "+str(overlap),lf)
    printout("Create Canopy Raster: "+str(boocan),lf)
    printout('_________________________________',lf)
	
    # LiDAR import
    if(lidar_run > 0):
        L2start = dt.datetime.now()
        printout('START LiDAR point cloud import',lf)
        
        # Mapset and Region Defined
        mapset_gotocreate(mlpi,'default',C,lf)

        ow = int(lidar_run - 1)   # overwrite files? 0 = no, 1 = yes

        #################################################
        for pref in LidarPoints:
            i = 0
            # Canopy Raster can only be created from unfiltered points
            if(cansource == '' and (pref == 'unfiltered' or pref == 'all')):
                boocan = True
            else:
                boocan = False
            printout('Will canopy raster will be created using '+pref+'?:'+str(boocan),lf)
            
            inDir = inPath+pref+"//"
            for strFile in os.listdir(inDir):
                print "checking "+strFile
                t = strFile.split('.')
                if(len(t) > 1 and t[1] == inSuffix):
                    tile=t[0]
                    cantile = 'can_'+tile
                    fstart = dt.datetime.now()
                    printout("Importing: "+strFile+" as "+tile,lf)
                    # n=4399092 s=4396972 e=446782 w=444662 b=365 t=754
                    str_boundary = grass.read_command("r.in.xyz", flags = "sg", input = inDir+strFile, fs = sep, output = "temp")
                    boundary = str_boundary.split(' ')
                    tn = (boundary[0].split('='))[1]
                    ts = (boundary[1].split('='))[1]
                    te = (boundary[2].split('='))[1]
                    tw = (boundary[3].split('='))[1]
                    tb = (boundary[4].split('='))[1]
                    tt = (boundary[5].split('='))[1]
                    grass.run_command("g.region", overwrite = ow, n=tn, s=ts, e=te, w=tw, b=tb, t=tt)
                    grass.run_command("r.in.xyz", overwrite = ow, input = inDir+strFile, output = tile,type="FCELL", fs= sep, method="n")
                    if(boocan == True):
                        grass.run_command("r.in.xyz", overwrite = ow, input = inDir+strFile, output = cantile,type="FCELL", fs= sep, method="max")
                    
                    # Some LiDAR Tiles overlap. These need to be clipped before merging together
                    ctile = 'c'+tile
                    ccantile = 'c'+cantile
                    if(overlap == 0):
                        grass.run_command("g.rename",rast=tile+","+ctile)
                        if(boocan == True):
                            grass.run_command("g.rename",rast=cantile+","+ccantile)
                    else:
                        # clip tile, remove overlap
                        otn = float(tn) - overlap
                        ots = float(ts) + overlap
                        ote = float(te) - overlap
                        otw = float(tw) + overlap
                        grass.run_command("g.region", n = otn, s = ots, w = otw, e = ote)
                        grass.mapcalc("$ctile = float($tile)",ctile = ctile, tile = tile, overwrite = ow)
                        grass.run_command("g.remove", flags = "f", rast = tile)
                        if(boocan == True):
                             grass.mapcalc("$ccantile = float($cantile)",ccantile = ccantile, cantile = cantile, overwrite = ow)
                             grass.run_command("g.remove", flags = "f", rast = cantile)
                    
                    # append list of tiles to merge
                    if(i == 0):
                        patch_list = ctile
                        can_patch_list = ccantile
                    else:
                        patch_list += ","+ctile
                        can_patch_list += ","+ccantile
                    i += 1
            
            # Reset the mapset from tile size to default (with proper cell size)
            set_region('lpi',C)

            ##################
            # Point Density Map
            # Mosaic all the tiles into one map
            pointdensity = pdensitypref+pref
            grass.run_command("r.patch", overwrite = ow, input = patch_list, output= pointdensity)
            printout('point density raster '+pointdensity+' has been created.',lf)
            
            # Delete the clipped tiles, leaving only a completed point densitymap
            ctile_list = patch_list.split(',')
            for ctile in ctile_list:
                grass.run_command("g.remove", flags = "f", rast = ctile)

            ##################
            # Canopy Map
            if(boocan == True):
                # Mosaic all the tiles into one map
                grass.run_command("r.patch", overwrite = ow, input = can_patch_list, output = can)
                printout('Canopy raster '+can+' has been created.',lf)
         
                # Delete the clipped tiles, leaving only a completed canopy map
                ccantile_list = can_patch_list.split(',')
                for cctile in ccantile_list:
                    grass.run_command("g.remove", flags = "f", rast = cctile)

            printout("Done with "+pref,lf)

        #################################################
        # Finish
        # Reset mapset and region 
        mapset_gotocreate('PERMANENT','default',C,lf)
     
        # Move canopy raster to PERMANENT
        if(boocan == True):
            str_rasts = can+"@"+mlpi+","+can
            grass.run_command("g.copy", rast = str_rasts)
            #grass.run_command("g.remove", rast = can)
            printout('Canopy raster '+can+' moved to PERMANENT',lf)    
        
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
