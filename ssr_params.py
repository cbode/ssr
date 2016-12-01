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
lidar_run = 2           # Imports point cloud as canopy and point density rasters
lpi_run = 0             # Creates Light Penetration Index (LPI) from point cloud
preprocessing_run = 0   # Creates derivative GIS products slope, aspect, tree height, albedo
rsun_run = 0            # Runs GRASS light model, r.sun
algore_run = 0          # Algorithm for combining all the parts into the SRR

#----------------------------------------------------------------------------
# GENERAL PARAMETERS
# GRASS GIS requires 4 inputs to start: 
gisbase = '/usr/lib64/grass-6.4.4'  # GIS BASE (GISBASE): path to GRASS binaries.
gisdbase = '/data/grass_workspace'  # DATABASE (GISDBASE): directory containing all GRASS layers. 
location = 'angelo2014'             # LOCATION: defined by coordinate system & bounding box.                     
mapset = 'PERMANENT'                # MAPSET: each GRASS session runs under a unique MAPSET. PERMANENT is default.

# Resolution and Bounding box
C = '2'                             # cell size in meters 2
bregion = 'default'                 # boundary used in g.region: b5k,b8k,b10, d = default. utilities needs to be changed for different regions.

# INPUT RASTER NAMES
demsource = 'angelo1m2014dem'
cansource = ''                     # If you do not have a canopy raster, leave this empty '' and ssr_lidar.py will create it automatically.

#----------------------------------------------------------------------------
# MAP NAMES
P = bregion + C + 'm'            # Prefix to raster maps and Mapsets.  This allows subsets of the total area to be run.
dem = P + 'dem'                  # source map: bare-earth dem
can = P + 'can'                  # source map: canopy dem
sloped = P + 'demslope'          # slope, bare-earth
slopec = P + 'canslope'          # slope, canopy
aspectd = P + 'demaspect'        # aspect, bare-earth
aspectc = P + 'canaspect'        # aspect, canopy
vegheight = P + 'vegheight'      # vegetation height
albedo = P + 'albedo'            # albedo by vegtype
demhor = P + 'demhor'            # horizon, bare-earth
canhor = P + 'demhor'            # horizon, canopy

#----------------------------------------------------------------------------
# SSR1: LIDAR IMPORT PARAMETERS
# LiDAR downloaded from http://opentopography.org.
# National Center for Airborne Laser Mapping (NCALM) distributes laser hits as 2 datasets:  total and ground filtered.
# Version 1.0 only processes ASCII files with ground filtered exported to a separate directory.  Future versions will 
# use .las files in a single directory.
year = 'y14'	        		            # Year the LiDAR was flown 2004 'y04', 2004 modified to match y09 'ym4',2009 'y09'
pdensitypref = 'pointdensity_c'+str(C)+year	    # prefix to the point density rasters
inSuffix='xyz'                                      # filename suffix to filter for
overlap = float(0)				    # tile overlap in meters  10.00 m (y04,y09), 0.00 m (y14)
sep = ','				            # separator in lidar files ' ' or ','
LidarPoints = [ 'filtered' , 'unfiltered' ]         # subdirectories under inPath.  y04 = [ 'ground' , 'all' ]
inPath='/data/source/LiDAR/2014_EelBathymetry_LiDAR/Angelo/Tiles_ASCII_xyz/'
#inPath='/data/source/LiDAR/2009_SFEel_LiDAR/ascii/'
#inPath='/data/source/LiDAR/2004_SFEel_LiDAR/TerraScan_EEL/laser_export/'

#----------------------------------------------------------------------------
# SSR2: LPI PARAMETERS
#Radius = 8				# Previous radius was 8, but that is actually 8 cells per side * 2meters per cell = 32 meters, and actually I used 31x31 cell square.
boxsize = '17'                          # Size is cell size of box for r.neighbors.  This is different than the actual box (9 cells x 2 meter cells = 18 meters)
lpipref = 'lpi_c'+C+year+'s'+boxsize   # add the month to the end, e.g. lpi_c2y09s17m10

#----------------------------------------------------------------------------
# SSR3: R.HORIZON PARAMETERS
maxdistance = '10000'           # maxdistance = 10000 meters (longer than the diagnal of the map)
hstep = '1'                     # horizonstep = 1 degree (causing 360 maps to be created)
dist = '0.5'                    # normal range (0.5 - 1.5) previous runs used 0.3 ?artifacting?
                                # dist=1.0 or greater uses simplified calculation that causes artifacts

#----------------------------------------------------------------------------
# SSR4: R.SUN Solar Model Parameters
# r.sun is designed to be run for 1 day, 24 hours.  script runs for 1 year, every week.
linke_array = 'helios'          # various options of turbidity values, "helios" is default for Angelo.
tl = linke_array
start_day = 5                   # First Julian Day calculated
week_step = 7                   # run r.sun once every week
timestep = '0.1'                # 0.1 decimal hour = 6 minute timestep, default 0.5(30min), last run 0.5
calib = 'hd'                    # r.sun calibration code:  'hd' = 0.50 * Diffuse, 1.0 * Direct, reflection is ignored.
                                # calibration needs to be moved to algore script

#----------------------------------------------------------------------------
# SSR5: ALGORE PARAMETERS
maxheight = '2'   			    # Vegetation height after which canopy is set to null
#halfdiff = True                            # Reduces the r.sun diffuse output by half. suffix 'half' on diffuse and global maps
keeptemp = True 			    # Testing only. Should be false for production.
lpivsjune = False                           # Analysis only. Uses June LPI only
sky = 'cs'				    # cs 'clear sky' or rs 'real sky' which includes cloudiness index.
algore = 'gl'		                    # Options: 'pl' = Power Law, 'nl' = Natural Log, 'd' for old default value of 1, 
                                            # 'cl' = Cameau Linear, 'cn' = Cameau linear Normalized, nLPI = 1.428 * LPI, Diffuse = 0.94 * nLPI * HalfDiff
                                            # 'gn' = Gendron linear normalized, nLPI = 1.428 * LPI,  Diffuse =  0.01719 + 1.024 * nLPI * HalfDiff
                                            # 'gl' = Gendron linear.  no normalization.  It overestimates field radiation. Diffuse =  0.01719 + 1.024 * LPI
                                            #        Calibration of r.sun values is now handled seperately and should not be included here.
 
#----------------------------------------------------------------------------
# MAPSETS 
mhorizon = bregion+'_horizon'          # horizon mapset
msun = 'sun_'+bregion+'_'+calib        # r.sun mapset using calibration
mlpi = 'lpi'                           # lpi mapset  
mssr = 'ssr_'+bregion+'_'+algore       # ssr output mapset 
