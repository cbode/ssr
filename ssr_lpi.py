#!/usr/bin/env python
############################################################################
#
# MODULE:       ssr_lpi.py
# AUTHOR:       Collin Bode, UC Berkeley
#               modified from r.out.xyz
# PURPOSE:
# 	2. Calculate point density using an asymetric nearest neighbor box.
# 	3. Calculate LPI as the ratio of filtered to unfiltered.
#
# COPYRIGHT:    (c) 2011 Collin Bode
#				(c) 2006 Hamish Bowman, and the GRASS Development Team
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
    lf = open(gisdbase+os.sep+'ssr_'+tlog+'_lpi.log', 'a')
    #mlpi = 'lpi'    # <-- debug remove
    
    printout("STARTING LPI RUN",lf)
    printout("LOCATION: "+loc,lf)
    printout("Source DEM: "+demsource,lf)
    printout("Source CAN: "+cansource,lf)
    printout('pref: '+pref,lf)
    printout("LPI pref: "+lpipref,lf)
    printout('LPI mapset: '+mlpi,lf)
    printout("Boxsize: "+boxsize,lf)
    printout('_________________________________',lf)
	
    # LPI
    if(lpi_run > 0):
        L2start = dt.datetime.now()
        L2starttime = dt.datetime.strftime(L2start,"%m-%d %H:%M:%S")
        printout('START LPI at '+ str(L2starttime),lf)
        
        # Mapset and Region Defined
        mapset_gotocreate(mlpi,'default',C,lf)

        # LPI Weights Translation table
        weight_num = 4
        weight_name = 'lpi_box18x18_weight'
        month_weights = {1:1, 2:2, 3:2, 4:3, 5:4, 6:4, 7:4, 8:3, 9:3, 10:2, 11:2, 12:1}
        scriptPath = get_path()

        printout("R2 Starting LPI Calculation using size("+str(boxsize)+")",lf)

        # Set names for ground/filtered and all/unfiltered point density rasters
        pdensityfilt = pdensitypref + LidarPoints[0]
        pdensityunf = pdensitypref + LidarPoints[1]

        # Iterate through all the neighborhood weights and calculate LPI
        for weight in range(1,(weight_num+1)):
                weight = str(weight)
                weight_file = scriptPath+weight_name+weight+'.txt'
                pneighfilt = pdensitypref + "w"+weight+LidarPoints[0]
                pneighunf = pdensitypref + "w"+weight+LidarPoints[1]
                lpi = lpipref + "w"+weight

                # LPI is calculated by running a neighborhood analysis on grids which contain a count of lidar points (ground filtered and raw - all points)
                # The neighborhood analysis uses a bounding box defined by month (4 possible boxes) and sums all the lidar points within range
                # LPI = Ground Filtered sum of LiDAR points / Raw All summed Points.  Result is a dimensionless ratio of Canopy Gap or Openness.
                # Ratios occasionally exceed 1.0 (100%), so additional cleaning step included to set those to 100%.
                printout("running neighborhood operation for ground filtered, weight"+weight,lf)
                grass.run_command("r.neighbors", overwrite = "true", input= pdensityfilt, output = pneighfilt, method = "sum", size = boxsize, weight = weight_file)
                grass.run_command("r.neighbors", overwrite = "true", input= pdensityunf, output = pneighunf, method = "sum", size = boxsize, weight = weight_file)
                if(year == 'ym4'):
                        str_formula = "3.71 * ( A / B )^1.3455"
                elif(year == 'yr4'):
                        str_formula = "6.5 * ( A / B )^1.57 + 0.005"                                
                else:
                        str_formula = "A / B"
                grass.run_command("r.mapcalculator", overwrite = "true", amap = pneighfilt, bmap = pneighunf, formula = str_formula, outfile = lpi)	
                str_formula = "if( A > 1.0, 1.0, A)"
                grass.run_command("r.mapcalculator", overwrite = "true", amap =  lpi, formula = str_formula, outfile = lpi)	
                printout("finished creating "+lpi,lf)
                
        # Copy/rename each weight to their respective months
        for month,weight in month_weights.items():
                wlpi = lpipref + "w"+str(weight)
                monthlpi = lpipref+"m"+str(month).zfill(2)
                str_rasts = wlpi+","+monthlpi
                grass.message("Copying "+wlpi+" to "+monthlpi+" at "+str(dt.datetime.now()))
                grass.run_command("g.copy",overwrite = "true",rast = str_rasts)
        
        # Finish
        set_region('default',C)
        
        L2end = dt.datetime.now()
        L2endtime = dt.datetime.strftime(L2end,"%m-%d %H:%M:%S")
        L2processingtime = L2end - L2start
        printout('END  at '+ L2endtime+ ', processing time: '+str(L2processingtime),lf)
        printout("DONE with LPI Calculations",lf)
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
