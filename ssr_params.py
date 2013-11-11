#!/usr/bin/env python
############################################################################
#
# MODULE:       ssr_params.py
# AUTHOR:       Collin Bode, UC Berkeley
#               
# PURPOSE:  Consolidate parameters for all SSR scripts and to provide some 
# 	    common functions.
#
# DEPENDENCIES:  requires function set_server_environment(server_name).
#           So import grass_setserver is needed.
#
# COPYRIGHT:    (c) 2012 Collin Bode
#		(c) 2006 Hamish Bowman, and the GRASS Development Team
#               (c) 2008 Glynn Clements, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#----------------------------------------------------------------------------
# Run Parts?  0 = do not run, 1 = run, but do not overwrite maps, 2 = run, overwrite maps
preprocessing_run = 2
lpi_run = 0
rsun_run = 0
algore_run = 0

#----------------------------------------------------------------------------
# GENERAL PARAMETERS
loc = "sfk"                     # location prefix, name of the GRASS directory, also 'P' and 'location'
C = "2"                         # cell size in meters
bregion = "b8k"		        # boundary used in g.region: b5k,b8k,b10,default
pref = bregion + C + 'm'        # used as name prefix when g.region is not default

#----------------------------------------------------------------------------
# SSR2: R.HORIZON PARAMETERS
maxdistance = '10000'           # maxdistance = 10000 meters (longer than the diagnal of the map)
inthstep = 1                    # horizonstep = 1 degree (causing 360 maps to be created)
hstep = str(inthstep)
dist = '0.5'                    # normal range (0.5 - 1.5) previous runs used 0.3 ?artifacting?
                                # dist=1.0 or greater uses simplified calculation that causes artifacts

#----------------------------------------------------------------------------
# SSR3: R.SUN Solar Model Parameters
# r.sun is designed to be run for 1 day, 24 hours.  script runs for 1 year, every week.
linke_array = "helios"          # various options of turbidity values, "helios" is default for Angelo.
tl = linke_array
start_day = 5                   # First Julian Day calculated
week_step = 7                   # run r.sun once every week
timestep = '0.1'                # 0.1 decimal hour = 6 minute timestep, default 0.5(30min), last run 0.5
calib = 'hd'                    # r.sun calibration code:  'hd' = 0.50 * Diffuse, 1.0 * Direct, reflection is ignored.
                                # calibration needs to be moved to algore script
#----------------------------------------------------------------------------
# SSR4: LIDAR IMPORT PARAMETERS
# LiDAR downloaded from http://opentopography.org.
# National Center for Airborne Laser Mapping (NCALM) distributes laser hits as 2 datasets:  total and ground filtered.
year = 'y09'	        		# Year the LiDAR was flown 2004 'y04', 2004 modified to match y09 'ym4',2009 'y09'
if(year == 'y09'):
    inPath='/data/source/LiDAR/2009_SFEel_LiDAR/'
    LidarPoints = [ 'filtered' , 'unfiltered' ]
else: # year == 'y04' or 'ym4' 
    inPath='/data/source/LiDAR/2004_SFEel_LiDAR/TerraScan_EEL/laser_export/'
    LidarPoints = [ 'ground' , 'all' ]
inSuffix='xyz'                          # filename suffix to filter for
sep = ' '				# separator in lidar files ' ' or ','
overlap = 10.00				# tile overlap in meters
pdensitypref = "pdensity_c"+str(C)+year	# prefix to the point density rasters
#if(year == 'y09'):
#    pdensitypref = "pdensity_c"+str(C)+year	# prefix to the point density rasters
#else:
#    pdensitypref = "pdensity_c"+str(C)+"y04" 

#----------------------------------------------------------------------------
# SSR5: LPI PARAMETERS
#Radius = 8				# Previous radius was 8, but that is actually 8 cells per side * 2meters per cell = 32 meters, and actually I used 31x31 cell square.
boxsize = '17'                          # Size is cell size of box for r.neighbors.  This is different than the actual box (9 cells x 2 meter cells = 18 meters)
scriptPath = '/ssd/collin_light/scripts/' #'/data/rsun/scripts/'
lpipref = 'lpi_c'+C+year+'s'+boxsize+'m' # add the month to the end, e.g. lpi_c2y09s17m10

#----------------------------------------------------------------------------
# SSR6: ALGORE PARAMETERS
halfdiff = True                            # Reduces the r.sun diffuse output by half. suffix 'half' on diffuse and global maps
keeptemp = True				    # Testing only. Should be false for production.
lpivsjune = False                           # Analysis only. Uses June LPI only
sky = 'cs'				    # cs 'clear sky' or rs 'real sky' which includes cloudiness index.
maxheight = '2'   			    # Vegetation height after which canopy is set to null
algore = 'gl'		                    # Options: 'pl' = Power Law, 'nl' = Natural Log, 'd' for old default value of 1, 
                                            # 'cl' = Cameau Linear, 'cn' = Cameau linear Normalized, nLPI = 1.428 * LPI, Diffuse = 0.94 * nLPI * HalfDiff
                                            # 'gn' = Gendron linear normalized, nLPI = 1.428 * LPI,  Diffuse =  0.01719 + 1.024 * nLPI * HalfDiff
                                            # 'gl' = Gendron linear.  no normalization.  It overestimates field radiation. Diffuse =  0.01719 + 1.024 * LPI
                                            #        Calibration of r.sun values is now handled seperately and should not be included here.
 
#if(halfdiff == True):
#    output_mapset = output_mapset+'_halfdiff'
# Map prefixes
#?dem = bregion + cell + 'mdem'
#?can = bregion + cell + 'mcan'


#----------------------------------------------------------------------------
# MAP NAMES
dem = loc + 'dem'              # source map: bare-earth dem
can = loc + 'can'              # source map: canopy dem
sloped = dem + 'slope'          # slope, bare-earth
slopec = can + 'slope'          # slope, canopy
aspectd = dem + 'aspect'        # aspect, bare-earth
aspectc = can + 'aspect'        # aspect, canopy
vegheight = loc + 'vegheight'  # vegetation height
albedo = loc + 'albedo'        # albedo by vegtype
demhor = dem + 'hor'            # horizon, bare-earth
canhor = can + 'hor'            # horizon, canopy


#----------------------------------------------------------------------------
# MAPSETS 
mhorizon = bregion+'_horizon'          # horizon mapset
#msun = bregion+linke_array+'_sun'     # r.sun output mapset old
msun = 'sun_'+bregion+'_'+calib        # r.sun mapset using calibration
mlpi = 'lpi'                           # lpi mapset  
mssr = 'ssr_'+bregion+'_'+algore       # ssr output mapset 
