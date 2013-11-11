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
#
# SOURCE MAPS:  bare-earth dem and canopy dem.  all else is calculated from them.
#
# DEPENDENCIES: ssr_params.py, ssr_utilities.py, GRASS GIS
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
from ssr_params import *
from ssr_utilities import *
import traceback
import shutil
import multiprocessing as mp
import numpy
from scipy.interpolate import interpolate
#sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "python"))

# Identify which server python is running on and set specific paths
gisbase,gisdbase = set_server_environment()

# FUNCTIONS
def preprocessing(mapset,ow):
        gsetup.init(gisbase, gisdbase, loc, mapset)
        set_region(bregion)
	
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
        gsetup.init(gisbase, gisdbase, loc, mtemp)
        set_region(bregion)

        # Input Maps
        elevdem = loc+demr+'@PERMANENT'
        horr = loc+demr+'hor'

        # Run r.sun for each week of the year 366
        for doy in range(julian_seed,366,step):
                day = str(doy).zfill(3)
                linke = linke_interp(doy,linke_array)
                # Output maps
                beam = pref+demr+day+'beam'
                dur = pref+demr+day+'dur'
                diff = pref+demr+day+'diff'
                refl = pref+demr+day+'refl'
                glob = pref+demr+day+'glob'
                grass.run_command("r.sun", flags="s", elevin=elevdem, albedo=albedo, \
                                  horizonstep=hstep, \
                                  beam_rad=beam, insol_time=dur, \
                                  diff_rad=diff, refl_rad=refl, \
                                  glob_rad=glob, day=doy, step=timestep, \
                                  lin=linke, overwrite=ow) 
                # horizon=horr, 

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
        printout("STARTING R.SUN MODELING RUN")
        printout("LOCATION: "+location)
        printout("HORIZONS: NOT USED. JUST DOING -S ON THE FLY")
        printout("This computer has "+str(cores)+" CPU cores.")
        printout('pref: '+pref)
        printout('dem: '+dem)
        printout('can: '+can)
        #printout('horizon mapset: '+mhorizon)
        printout('horizonstep: '+hstep)
        printout('dist: '+dist)
        printout('maxdistance: '+maxdistance)
        printout('r.sun mapset: '+msun)
        printout('linke_array: '+linke_array)
        printout('timestep: '+timestep)
        printout('start julian day: '+str(start_day))
        printout('week step: '+str(week_step))
        printout('_________________________________')

        # Preprocessing
        if(preprocessing_run > 0):
                R1start = dt.datetime.now()
                R1starttime = dt.datetime.strftime(R1start,"%m-%d %H:%M:%S")
                printout(lf,'START preprocessing at '+ str(R1starttime))

                preprocesing('PERMANENT',int(preprocessing_run-1))

                R1end = dt.datetime.now()
                R1endtime = dt.datetime.strftime(R1end,"%m-%d %H:%M:%S")
                R1processingtime = R1end - R1start
                printout(lf,'END preprocessing at '+ R1endtime + ', processing time: '+str(R1processingtime))

        # R.SUN Start
	if(rsun_run > 0):
		R3start = dt.datetime.now()
		R3starttime = dt.datetime.strftime(R3start,"%m-%d %H:%M:%S")
		printout('START  '+ R3starttime)

		# Create one temp directory for each CPU core
		printout("Creating Temporary directories, one per cpu core.")
		create_temp(cores)
		
		# Spawn R.SUN processes
		step = cores * week_step
		for demr in ['dem','can']:
			julian_seed =  start_day
			jobs = []
			for cpu in range(0,cores):
				p = mp.Process(target=worker_sun, args=(cpu,julian_seed,step,demr,bregion))
				p.start()
				jobs.append(p)
				pid = str(p.pid)
				printout("r.sun: dem = "+demr+" cpu = "+str(cpu)+" julian_seed = "+str(julian_seed)+" pid = "+pid)
				julian_seed += week_step

			# Wait for all the Processes to finish
			for p in jobs:
				pid = str(p.pid)
				palive = str(p.is_alive)
				p.join()
				printout(demr+" on "+pid+" joined.")
			printout("R.Sun finished for "+demr)
		
		# Copy all the files back over to sun mapset
		suffixes = ['glob','beam','diff','refl','dur']
		copy_fromtemp(msun,suffixes,1)

		# Delete the temp mapsets
		remove_temp(cores)

		# Finish
		R3end = dt.datetime.now()
		R3endtime = dt.datetime.strftime(R3end,"%m-%d %H:%M:%S")
		R3processingtime = R3end - R3start
		printout('END  at '+ R3endtime+ ', processing time: '+str(R3processingtime))
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
