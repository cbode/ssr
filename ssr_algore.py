#!/usr/bin/env python
############################################################################
#
# MODULE:       ssr_algore.py
# AUTHOR:       Collin Bode, UC Berkeley
#
# PURPOSE:
# 		Al Gore Rhythm combines r.sun model with Light Penetration Index (LPI).
#		Merges all the r.sun solar radiation runs into a single estimate of
#		Total Solar Radiation in watt-hours per meter squared per day.
#		Optional clear sky vs real sky. <-- only clear sky for now.
#
# Modified:     Collin Bode, October, 2012
#               Migrated to unified parameter set.
#               Simplified all the tweaks: JuneLPI kept, removed normalization for LPI
#               R.sun calibration now serparated from algorithm ("HalfDiff")
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
    # Algorithms for combining Diffuse and Direct
    # 'd'  = old default value of 1, 
    # 'pl' = Power Law,Diffuse = 1.1224 * x^0.3157, R2 = 0.41.  Direct = = 1.2567 * x, R2 = 0.78
    # 'nl' = Natural Log,
    # 'cl' = Cameau Linear, 'cn' = Cameau linear Normalized, nLPI = 1.428 * LPI, Diffuse = 0.94 * nLPI 
    # 'gn' = Gendron linear normalized, nLPI = 1.428 * LPI,  Diffuse =  0.01719 + 1.024 * nLPI 
    # 'gl' = Gendron linear.  no normalization.  It overestimates field radiation.
    # Input bare-earth r.sun diffuse is too high. Instead of changing Linke Turbidity, modified here.
    # See weatherstations.xlsx for analysis.
    
    # Open log file
    tlog = dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d_h%Hm%M")
    lf = open(gisdbase+os.sep+'ssr_'+tlog+'_algore.log', 'a')
        
    # Overwrite files?
    ow = int(algore_run -1)

    # Print parameters
    printout('---------------------------------------',lf)
    printout('-- ALGORITHM FOR CLEAR SKY RADIATION --',lf)
    printout('          LPI year: '+year,lf)
    printout('          LPI pref: '+lpipref,lf)
    printout('            region: '+bregion,lf)
    printout('        sun mapset: '+msun,lf)
    printout(' SSR output mapset: '+mssr,lf)
    printout('    max veg height: '+maxheight,lf)
    printout('    Algorithm code: '+algore,lf)
    printout('keep intermediates: '+str(keeptemp),lf)
    printout('   overwrite files: '+str(ow),lf)
    printout('---------------------------------------',lf)

    # Run Algorithm
    r1start = dt.datetime.now()
    printout("Starting Al Gore Rhythm at "+str(r1start),lf)

    # Goto Correct Mapset and make sure Region is correctly set (ssr_utilities)
    mapset_gotocreate(mssr,bregion,C,lf)

    # For each week 
    for doyn in range(5,366,7):
        doy = str(doyn).zfill(3)
        month = dt.datetime.strftime(dt.datetime(2011,1,1) + dt.timedelta(doyn -1),"%m")
        printout("Processing Day of Year " + doy + " in month "+month,lf)

        # Input Raster Layers
        sundem = bregion + C + 'mdem'
        suncan = bregion + C + 'mcan'
        dembeam = sundem + doy + 'beam@'+msun
        demdiff = sundem + doy + 'diff@'+msun
        canbeam = suncan + doy + 'beam@'+msun
        candiff = suncan + doy + 'diff@'+msun
        canglob = suncan + doy + 'glob'
        veg = vegheight+'@PERMANENT'
        lpi = lpipref + 'm'+ month + '@' + mlpi   # lpi_c30y14s17m01
        if(lpivsjune == True):
            lpi = lpipref + '06@' + mlpi
            
        # Output Raster Layers
        lpipart = C + 'm' + year + 's' + boxsize + 'm' + algore
        if(lpivsjune == True):
            lpipart = C + 'm' + year + 's' + boxsize+'mjune' + algore
        ssr = 'ssr_'+ lpipart + doy
        opencanopy = 'opencanopy_' + lpipart + doy
        subcanopy = 'subcanopy_' + lpipart + doy
        lpibeam   = 'subbeam_' + lpipart + doy    
        lpidiff   = 'subdiff_' + lpipart + doy 

        ###################################################################
        #1. SUBCANOPY Merge LPI and Bare-earth by Algorithm
        printout("DOY "+doy+" 1. merging lpi and dem using: "+algore,lf)
        if(algore == 'cl'): # 'cl' Cameau Linear regression
            grass.mapcalc("$tmp_lpidiff = 0.94 * $lpi * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = ow)
            grass.mapcalc("$tmp_lpibeam = $beam * $lpi", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = ow)
        elif(algore == 'cn'): # 'cn' Cameau Normalized - assumes halfdiff is set to True
            grass.mapcalc("$tmp_lpidiff = 0.94 * (1.428 * $lpi) * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = ow)
            grass.mapcalc("$tmp_lpibeam = 1.428 * $beam * $lpi", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = ow)
        elif(algore == 'gn'): #gn Diffuse Gendron Linear Normalized. y =  0.01719 + 1.024 * nLPI 
            grass.mapcalc("$tmp_lpidiff = 0.01719 + 1.024 * (1.428 * $lpi) * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = ow)
            grass.mapcalc("$tmp_lpibeam = (1.428 * $lpi) * $beam", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = ow)
        elif(algore == 'gl'): #gl Diffuse Gendron Linear NON-normalized y =  0.01719 + 1.024 * LPI 
            grass.mapcalc("$tmp_lpidiff = 0.01719 + 1.024 * $lpi * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = ow)
            grass.mapcalc("$tmp_lpibeam = $lpi * $beam", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = ow)
        else:   # 'pl' power law
            grass.mapcalc("$tmp_lpidiff = 1.1224 * ($lpi^0.3157) * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = ow)
            grass.mapcalc("$tmp_lpibeam =  1.2567 * $beam * $lpi", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = ow)
        
        grass.mapcalc("$subcanopy = $tmp_lpibeam + $tmp_lpidiff", subcanopy = subcanopy, tmp_lpidiff = lpidiff, tmp_lpibeam = lpibeam, overwrite = ow)

        ###################################################################
        #2. OPEN CANOPY: Remove areas under tall trees (maxheight meters or higher)
        printout('DOY '+doy+' 2. set subcanopy values to -88',lf)
        grass.mapcalc("$canglob = $canbeam + $candiff",canglob = canglob, canbeam = canbeam, candiff = candiff,overwrite = ow)
        grass.mapcalc("$opencanopy = if($veg < $maxheight, $canglob,-88)",opencanopy = opencanopy, veg = veg, canglob = canglob, maxheight = maxheight,overwrite = ow)

        ###################################################################
        #3. Merge lpi*bare-earth with cleaned canopy, keeping whichever is higher.
        printout("DOY "+doy+" 3. Merge lpi*dem with canopy shade = "+ssr,lf)
        grass.mapcalc("$ssr = if($opencanopy > $subcanopy, $opencanopy, $subcanopy)", opencanopy = opencanopy, subcanopy = subcanopy,ssr = ssr,overwrite = ow)
        grass.run_command("r.colors",map = ssr, color = "bcyr")

        #4. Remove temp maps
        if(keeptemp == False):
            for raster in [lpibeam,lpidiff,opencanopy,subcanopy,canglob]:
                grass.run_command("g.remove",rast=raster)

    # Reset GRASS env values
    grass.run_command("g.mapset", mapset="PERMANENT")
    grass.run_command("g.region", flags = "d")

    r1end = dt.datetime.now()
    printout("Al can shake his booty, 'cause...",lf)
    printout("DONE! with Al Gore Rhythm at "+str(r1end),lf)
    printout("--------------------------------------",lf)

    lf.close()
    sys.exit("FINISHED.")

if __name__ == "__main__":
    main()
    """
    try:
	#options, flags = grass.parser()
	main()
    except:
        printout('ERROR! quitting.')
        print traceback.print_exc()
        traceback.print_exc(file=lf)
        traceback.print_exc(file=sys.stdout)
    finally:
        lf.close()
        sys.exit("FINISHED.")
    """
