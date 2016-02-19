#!/usr/bin/env python
############################################################################
#
# MODULE:       ssr6_algore.py
# AUTHOR:       Collin Bode, UC Berkeley
#               modified from r.out.xyz
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
from ssr_params import *
from ssr_utilities import *

def printout(str_text):
		timestamp = dt.datetime.strftime(dt.datetime.now(),"%H:%M:%S")
		lf.write(timestamp+": "+str_text+'\n')
		print timestamp+": "+str_text

def main():
    global lf
    # Algorithms for combining Diffuse and Direct
    # 'd'  = old default value of 1, 
    # 'pl' = Power Law,Diffuse = 1.1224 * x^0.3157, R2 = 0.41.  Direct = = 1.2567 * x, R2 = 0.78
    # 'nl' = Natural Log,
    # 'cl' = Cameau Linear, 'cn' = Cameau linear Normalized, nLPI = 1.428 * LPI, Diffuse = 0.94 * nLPI 
    # 'gn' = Gendron linear normalized, nLPI = 1.428 * LPI,  Diffuse =  0.01719 + 1.024 * nLPI 
    # 'gl' = Gendron linear.  no normalization.  It overestimates field radiation.
    # Input bare-earth r.sun diffuse is too high. Instead of changing Linke Turbidity, modified here.
    # See weatherstations.xlsx for analysis.
    
    # Map prefixes
    lpipref = 'lpi_c'+cell+year+'s'+boxsize+'m' # add the month to the end, e.g. lpi_c2y09s17m10
 
    # Open log file
    tlog = dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d_h%Hm%M")
    lf = open('ssr_'+tlog+'_algore.log', 'a')
        
    # Print parameters
    printout('---------------------------------------')
    printout('-- ALGORITHM FOR CLEAR SKY RADIATION --')
    printout('          LPI year: '+year)
    printout('          LPI pref: '+lpipref)
    printout('            region: '+bregion)
    printout('        sun mapset: '+msun)
    printout(' SSR output mapset: '+mssr)
    printout('    max veg height: '+maxheight)
    printout('    Algorithm code: '+algore)
    printout('keep intermediates: '+str(keeptemp))
    printout('---------------------------------------')

    # Run Algorithm
    r1start = dt.datetime.now()
    printout("Starting Al Gore Rhythm at "+str(r1start))

    # Goto Correct Mapset and make sure Region is correctly set (ssr_utilities)
    mapset_gotocreate(mssr)
    set_region(bregion)

    # For each week 
    for doyn in range(5,366,7):
        doy = str(doyn).zfill(3)
        month = dt.datetime.strftime(dt.datetime(2011,1,1) + dt.timedelta(doyn -1),"%m")
        printout("Processing Day of Year " + doy + " in month "+month)

        # Input Raster Layers
        sundem = bregion + cell + 'm'+calib+'dem'
        suncan = bregion + cell + 'm'+calib+'can'
        dembeam = sundem + doy + 'beam@'+msun
        demdiff = sundem + doy + 'diff@'+msun
        canglob = suncan + doy + 'glob@'+msun
        veg = vegheight+'@PERMANENT'
        lpi = lpipref + month + '@' + mlpi
        if(lpivsjune == True):
            lpi = lpipref + '06@' + mlpi
            
        # Output Raster Layers
        lpipart = cell + 'm' + year + 's' + boxsize + 'm' + algore
        if(lpivsjune == True):
            lpipart = cell + 'm' + year + 's' + boxsize+'mjune' + algore
        ssr = 'ssr_'+ lpipart + doy
        opencanopy = 'opencanopy_' + lpipart + doy
        subcanopy = 'subcanopy_' + lpipart + doy
        lpibeam   = 'subbeam_' + lpipart + doy    
        lpidiff   = 'subdiff_' + lpipart + doy 

        #1. SUBCANOPY Merge LPI and Bare-earth by Algorithm
        printout("DOY "+doy+" 1. merging lpi and dem using: "+algore)
        if(algore == 'cl'): # 'cl' Cameau Linear regression
            grass.mapcalc("$tmp_lpidiff = 0.94 * $lpi * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = 1)
            grass.mapcalc("$tmp_lpibeam = $beam * $lpi", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = 1)
        elif(algore == 'cn'): # 'cn' Cameau Normalized - assumes halfdiff is set to True
            grass.mapcalc("$tmp_lpidiff = 0.94 * (1.428 * $lpi) * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = 1)
            grass.mapcalc("$tmp_lpibeam = 1.428 * $beam * $lpi", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = 1)
        elif(algore == 'gn'): #gn Diffuse Gendron Linear Normalized. y =  0.01719 + 1.024 * nLPI 
            grass.mapcalc("$tmp_lpidiff = 0.01719 + 1.024 * (1.428 * $lpi) * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = 1)
            grass.mapcalc("$tmp_lpibeam = (1.428 * $lpi) * $beam", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = 1)
        elif(algore == 'gl'): #gl Diffuse Gendron Linear NON-normalized y =  0.01719 + 1.024 * LPI 
            grass.mapcalc("$tmp_lpidiff = 0.01719 + 1.024 * $lpi * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = 1)
            grass.mapcalc("$tmp_lpibeam = $lpi * $beam", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = 1)
        else:   # 'pl' power law
            grass.mapcalc("$tmp_lpidiff = 1.1224 * ($lpi^0.3157) * $diff", tmp_lpidiff = lpidiff, diff = demdiff, lpi = lpi,overwrite = 1)
            grass.mapcalc("$tmp_lpibeam =  1.2567 * $beam * $lpi", tmp_lpibeam = lpibeam, beam = dembeam, lpi = lpi,overwrite = 1)
        
        grass.mapcalc("$subcanopy = $tmp_lpibeam + $tmp_lpidiff", subcanopy = subcanopy, tmp_lpidiff = lpidiff, tmp_lpibeam = lpibeam, overwrite = 1)

        #2. OPEN CANOPY: Remove areas under tall trees (maxheight meters or higher)
        printout('DOY '+doy+' 2. set subcanopy values to -88')
        grass.mapcalc("$opencanopy = if($veg < $maxheight, $canglob,-88)",opencanopy = opencanopy, veg = veg, canglob = canglob, maxheight = maxheight,overwrite = 1)

        #3. Merge lpi*bare-earth with cleaned canopy, keeping whichever is higher.
        printout("DOY "+doy+" 3. Merge lpi*dem with canopy shade = "+ssr)
        grass.mapcalc("$ssr = if($opencanopy > $subcanopy, $opencanopy, $subcanopy)", opencanopy = opencanopy, subcanopy = subcanopy,ssr = ssr,overwrite = 1)
        grass.run_command("r.colors",map = ssr, color = "bcyr")

        #4. Remove temp maps
        if(keeptemp == False):
            for raster in [lpibeam,lpidiff,opencanopy,subcanopy]:
                grass.run_command("g.remove",rast=raster)

    # Reset GRASS env values
    grass.run_command("g.mapset", mapset="PERMANENT")
    grass.run_command("g.region", flags = "d")

    r1end = dt.datetime.now()
    printout("Al can shake his booty, 'cause...")
    printout("DONE! with Al Gore Rhythm at "+str(r1end))
    printout("--------------------------------------")

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
