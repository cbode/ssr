#!/usr/bin/env python
############################################################################
#
# MODULE:       ssr_lpi.py
# AUTHOR:       Collin Bode, UC Berkeley
#               modified from r.out.xyz
# PURPOSE:
# 	1. Accept xyz LiDAR files (filtered & unfiltered) and import them into GRASS gis as raster.
#   	        This assumes filenames include an indicator that allows you to match filtered to unfiltered.
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
from ssr_params import *
from ssr_utilities import *

#from grass.script import core as grass

def main():
        # Set Environmental Variables
        #set_region(bregion)
        set_server_environment(server_name)
        mapset_gotocreate(mlpi)
        scriptPath = gisdbase+'/scripts/' 
        lpipref = "lpi_c"+str(C)+year+"s"+boxsize

        # LPI Weights Translation table
        weight_num = 4
        weight_name = 'lpi_box18x18_weight'
        month_weights = {1:1, 2:2, 3:2, 4:3, 5:4, 6:4, 7:4, 8:3, 9:3, 10:2, 11:2, 12:1}

        r2start = dt.datetime.now()
        grass.message("R2 Starting LPI Calculation using size("+str(boxsize)+") at "+str(r2start))

        # Set names for ground/filtered and all/unfiltered point density rasters
        pdensityfilt = pdensitypref + LidarPoints[0]
        pdensityunf = pdensitypref + LidarPoints[1]

        # Make sure we are at default extent of mapset
        grass.run_command("g.region", flags = "d") 

        # Iterate through all the neighborhood weights and calculate LPI
        for weight in range(1,(weight_num+1)):
                weight = str(weight)
                pneighfilt = pdensitypref + "w"+str(weight)+LidarPoints[0]
                pneighunf = pdensitypref + "w"+str(weight)+LidarPoints[1]
                lpi = lpipref + "w"+weight

                # LPI is calculated by running a neighborhood analysis on grids which contain a count of lidar points (ground filtered and raw - all points)
                # The neighborhood analysis uses a bounding box defined by month (4 possible boxes) and sums all the lidar points within range
                # LPI = Ground Filtered sum of LiDAR points / Raw All summed Points.  Result is a dimensionless ratio of Canopy Gap or Openness.
                # Ratios occasionally exceed 1.0 (100%), so additional cleaning step included to set those to 100%.
                grass.message("running neighborhood operation for ground filtered, weight"+weight+" at "+str(dt.datetime.now()))
                grass.run_command("r.neighbors", overwrite = "true", input= pdensityfilt, output = pneighfilt, method = "sum", size = boxsize, weight = scriptPath+weight_name+weight+'.txt')
                grass.run_command("r.neighbors", overwrite = "true", input= pdensityunf, output = pneighunf, method = "sum", size = boxsize, weight = scriptPath+weight_name+weight+'.txt')
                if(year == 'ym4'):
                        str_formula = "3.71 * ( A / B )^1.3455"
                elif(year == 'yr4'):
                        str_formula = "6.5 * ( A / B )^1.57 + 0.005"                                
                else:
                        str_formula = "A / B"
                grass.run_command("r.mapcalculator", overwrite = "true", amap = pneighfilt, bmap = pneighunf, formula = str_formula, outfile = lpi)	
                str_formula = "if( A > 1.0, 1.0, A)"
                grass.run_command("r.mapcalculator", overwrite = "true", amap =  lpi, formula = str_formula, outfile = lpi)	
                grass.message("finished creating "+lpi+" at "+str(dt.datetime.now()))
                
        # Copy/rename each weight to their respective months
        for month,weight in month_weights.items():
                wlpi = lpipref + "w"+str(weight)
                mlpi = lpipref+"m"+str(month).zfill(2)
                str_rasts = wlpi+","+mlpi
                grass.message("Copying "+wlpi+" to "+mlpi+" at "+str(dt.datetime.now()))
                grass.run_command("g.copy",overwrite = "true",rast = str_rasts)
        
        r2end = dt.datetime.now()
        grass.message("DONE with LPI Calculations at "+str(r2end))
        grass.message("--------------------------------------")

	sys.exit("FINISHED.")

if __name__ == "__main__":
	#options, flags = grass.parser()
	main()
