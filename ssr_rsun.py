#!/usr/bin/python
############################################################################
#
# MODULE:       ssr_rsun.py
# AUTHOR:       Collin Bode, UC Berkeley                March, 2011
#               Converted from BASH script to Python    March, 2012
#
# PURPOSE:      Run the entire sequence of processing for the r.sun model.
#               Threads a process per core for multicore processors (poor
#               man's multithreading).
#               NOTE: run ssr_lidar.py first!
#
# SOURCE MAPS:  bare-earth dem and canopy dem.  all else is calculated from them.
#
# DEPENDENCIES: ssr_params.py, ssr_lidar.py, ssr_utilities.py, GRASS GIS
#
# COPYRIGHT:    (c) 2012 Collin Bode
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

# MODULES REQUIRED
import traceback
import multiprocessing as mp
import numpy
from scipy.interpolate import interpolate

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


# FUNCTIONS
def preprocessing(mapset,ow):
        gsetup.init(gisbase, gisdbase, location, mapset)
        set_region(bregion,C)
	
	# Regrid from Input Raster to Target Cell size
	if(demsource != dem):
		grass.run_command("r.resample",input=demsource,output=dem,overwrite=ow)
	if(cansource != can):
		grass.run_command("r.resample",input=cansource,output=can,overwrite=ow)
	
        # Slope and Aspect
        grass.run_command("r.slope.aspect", elevation=dem, slope=sloped, \
                          aspect=aspectd, prec="float", zfactor=1, overwrite=ow)
        grass.run_command("r.slope.aspect", elevation=can, slope=slopec, \
                          aspect=aspectc, prec="float", zfactor=1, overwrite=ow)

        # Vegetation height
        grass.mapcalc("$vegheight = $can - $dem", overwrite = ow, \
                      vegheight = vegheight, can = can, dem = dem)

        # Albedo
        grass.run_command("r.recode",flags="a",input=vegheight,output=albedo,\
                           rules=gisdbase+'/scripts/albedo_recode.txt', overwrite=ow)

def worker_sun(cpu,julian_seed,step,demr,ow):
        mtemp = 'temp'+str(cpu).zfill(2)
        gsetup.init(gisbase, gisdbase, location, mtemp)
        set_region(bregion,C)

        # Input Maps
        if(demr == 'dem'):
            elevdem = dem+'@PERMANENT'
            horr = demhor
        else:
            elevdem = can+'@PERMANENT'
            horr = canhor

        # Run r.sun for each week of the year 366
        for doy in range(julian_seed,366,step):
                day = str(doy).zfill(3)
                linke = linke_interp(doy,linke_array)
                # Output maps
                beam = P+demr+day+'beam'
                diff = P+demr+day+'diff'
                refl = P+demr+day+'refl'
                dur = P+demr+day+'dur'
                #glob = P+demr+day+'glob'
                grass.run_command("r.sun", flags="s", elevin=elevdem, albedo=albedo, \
                                  horizonstep=hstep, \
                                  beam_rad=beam, insol_time=dur, \
                                  diff_rad=diff, refl_rad=refl, \
                                  day=doy, step=timestep, \
                                  lin=linke, overwrite=ow) 
                # horizon=horr, glob_rad=glob,

def linke_interp(day,turb_array):
        # put monthly data here
        # Angelo area LT from helios - cab
        # ltm1 and angelo-1 are identical, kept for backwards compatibility.  They are helios - 1
        if turb_array == 'helios':
                linke_data = numpy.array ([3.2,3.2,3.2,3.4,3.7,3.8,3.7,3.8,3.5,3.4,3.1,2.9])
        elif turb_array == 'angelo80':
                linke_data = numpy.array ([2.56,2.56,2.56,2.72,2.96,3.04,2.96,3.04,2.80,2.72,2.48,2.32])
        elif turb_array == 'angelo70':
                linke_data = numpy.array ([2.3,2.3,2.3,2.5,2.7,2.8,2.7,2.8,2.6,2.5,2.3,2.1])
        elif turb_array == 'angelo-1':
                linke_data = numpy.array ([2.2,2.2,2.2,2.4,2.7,2.8,2.7,2.8,2.5,2.4,2.1,1.9])
        elif turb_array == 'ltm1':
                linke_data = numpy.array ([2.2,2.2,2.2,2.4,2.7,2.8,2.7,2.8,2.5,2.4,2.1,1.9])
        else:
                linke_data = numpy.array ([1.5,1.6,1.8,1.9,2.0,2.3,2.3,2.3,2.1,1.8,1.6,1.5])

        linke_data_wrap = numpy.concatenate((linke_data[9:12],linke_data, linke_data[0:3]))
        monthDays = numpy.array ([0,31,28,31,30,31,30,31,31,30,31,30,31])
        midmonth_day = numpy.array ([0,0,0,0,0,0,0,0,0,0,0,0]) # create empty array to fill
        for i in range(1, 12+1):
                midmonth_day[i-1] = 15 + sum(monthDays[0:i])
        midmonth_day_wrap = numpy.concatenate((midmonth_day[9:12]-365, midmonth_day,midmonth_day[0:3]+365))
        linke = interpolate.interp1d(midmonth_day_wrap, linke_data_wrap, kind='cubic')
        lt = linke(day)
        return lt

def main():
        ##################################
        # R.SUN SOLAR MODEL
        ##################################
        cores = mp.cpu_count() - 2

	# Open log file
        tlog = dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d_h%H")
        lf = open('rsun_'+tlog+'.log', 'a')
        
        printout("STARTING R.SUN MODELING RUN",lf)
        printout("LOCATION: "+location,lf)
        printout("HORIZONS: NOT USED. JUST DOING -S ON THE FLY",lf)
        printout("This computer has "+str(cores)+" CPU cores.",lf)
        printout("Source DEM: "+demsource,lf)
        printout("Source CAN: "+cansource,lf)
        printout('Prefix: '+P,lf)
        printout('dem: '+dem,lf)
        printout('can: '+can,lf)
        #printout('horizon mapset: '+mhorizon,lf)
        printout('horizonstep: '+hstep,lf)
        printout('dist: '+dist,lf)
        printout('maxdistance: '+maxdistance,lf)
        printout('r.sun mapset: '+msun,lf)
        printout('linke_array: '+linke_array,lf)
        printout('timestep: '+timestep,lf)
        printout('start julian day: '+str(start_day),lf)
        printout('week step: '+str(week_step),lf)
        printout('_________________________________',lf)
	
        # Preprocessing
        if(preprocessing_run > 0):
                R1start = dt.datetime.now()
                R1starttime = dt.datetime.strftime(R1start,"%m-%d %H:%M:%S")
                printout('START PREPROCESSING at '+ str(R1starttime),lf)

                preprocessing('PERMANENT',int(preprocessing_run - 1))

                R1end = dt.datetime.now()
                R1endtime = dt.datetime.strftime(R1end,"%m-%d %H:%M:%S")
                R1processingtime = R1end - R1start
                printout('END PREPROCESSING at '+ R1endtime + ', processing time: '+str(R1processingtime),lf)

        # R.SUN Start
	if(rsun_run > 0):
		R3start = dt.datetime.now()
		R3starttime = dt.datetime.strftime(R3start,"%m-%d %H:%M:%S")
		printout('START  '+ R3starttime,lf)

		# Create one temp directory for each CPU core
		printout("Creating Temporary directories, one per cpu core.",lf)
		create_temp(cores,lf)
		
		# Spawn R.SUN processes
		step = cores * week_step
		for demr in ['dem','can']:
			julian_seed = start_day
			jobs = []
			for cpu in range(0,cores):
				p = mp.Process(target=worker_sun, args=(cpu,julian_seed,step,demr,bregion))
				p.start()
				jobs.append(p)
				pid = str(p.pid)
				printout("r.sun: dem = "+demr+" cpu = "+str(cpu)+" julian_seed = "+str(julian_seed)+" pid = "+pid,lf)
				julian_seed += week_step

			# Wait for all the Processes to finish
			for p in jobs:
				pid = str(p.pid)
				palive = str(p.is_alive)
				p.join()
				printout(demr+" on "+pid+" joined.",lf)
			printout("R.Sun finished for "+demr,lf)
		
		# Copy all the files back over to sun mapset
		suffixes = ['glob','beam','diff','refl','dur']
		mapset_gotocreate(msun)
		copy_fromtemp(cores,msun,suffixes,1,lf)

		# Delete the temp mapsets
		remove_temp(cores)

		# Finish
		R3end = dt.datetime.now()
		R3endtime = dt.datetime.strftime(R3end,"%m-%d %H:%M:%S")
		R3processingtime = R3end - R3start
		printout('END  at '+ R3endtime+ ', processing time: '+str(R3processingtime),lf)
	# Done
	printout('ssr_rsun.py done',lf)
	lf.close()
                

if __name__ == "__main__":
        try:
                #options, flags = grass.parser()
                main()
        except:
                printout('ERROR! quitting.')
                print traceback.print_exc()
                traceback.print_exc(file=lf)
                
        finally:
                #lf.close()
                sys.exit("FINISHED.")

