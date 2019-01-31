#@ File    (label = "Input directory", style = "directory") srcFile
#@ String  (label = "File extension", value=".dv") ext




"""

auto_stagerepro.py 
created by: Erick Martins Ratamero
date: 31/01/19
last updated: 31/01/19

Finds the relevant images with beads in the input
directory, crops a bead per image and uses TracKMate
to generate maximum X/Y drift values.

Inputs:
- Input directory: where the input file is (the input image should contain the string "psf")
- File extension: self-explanatory
- Number of beads: how many beads should be analysed

"""










def track(imp):	
	
	
	from fiji.plugin.trackmate import Model
	from fiji.plugin.trackmate import Settings
	from fiji.plugin.trackmate import TrackMate
	from fiji.plugin.trackmate import SelectionModel
	from fiji.plugin.trackmate import Logger
	from fiji.plugin.trackmate.detection import LogDetectorFactory
	from fiji.plugin.trackmate.tracking.sparselap import SparseLAPTrackerFactory
	from fiji.plugin.trackmate.tracking import LAPUtils
	from ij import IJ
	import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
	import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
	import sys
	import fiji.plugin.trackmate.features.track.TrackDurationAnalyzer as TrackDurationAnalyzer
	    
	# Get currently selected image
	#imp = WindowManager.getCurrentImage()
	#imp = IJ.openImage('http://fiji.sc/samples/FakeTracks.tif')
	#imp.show()
	
	
	    
	    
	#----------------------------
	# Create the model object now
	#----------------------------
	    
	# Some of the parameters we configure below need to have
	# a reference to the model at creation. So we create an
	# empty model now.
	    
	model = Model()
	    
	# Send all messages to ImageJ log window.
	model.setLogger(Logger.IJ_LOGGER)
	    
	    
	       
	#------------------------
	# Prepare settings object
	#------------------------
	       
	settings = Settings()
	settings.setFrom(imp)
	       
	# Configure detector - We use the Strings for the keys
	settings.detectorFactory = LogDetectorFactory()
	settings.detectorSettings = { 
	    'DO_SUBPIXEL_LOCALIZATION' : True,
	    'RADIUS' : 3.0,
	    'TARGET_CHANNEL' : 1,
	    'THRESHOLD' : 1.,
	    'DO_MEDIAN_FILTERING' : False,
	}  
	    
	# Configure spot filters - Classical filter on quality
	filter1 = FeatureFilter('QUALITY', 30, True)
	settings.addSpotFilter(filter1)
	     
	# Configure tracker - We want to allow merges and fusions
	settings.trackerFactory = SparseLAPTrackerFactory()
	settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap() # almost good enough
	settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = True
	settings.trackerSettings['ALLOW_TRACK_MERGING'] = True
	    
	# Configure track analyzers - Later on we want to filter out tracks 
	# based on their displacement, so we need to state that we want 
	# track displacement to be calculated. By default, out of the GUI, 
	# not features are calculated. 
	    
	# The displacement feature is provided by the TrackDurationAnalyzer.
	    
	settings.addTrackAnalyzer(TrackDurationAnalyzer())
	    
	
	    
	    
	#-------------------
	# Instantiate plugin
	#-------------------
	    
	trackmate = TrackMate(model, settings)
	       
	#--------
	# Process
	#--------
	    
	ok = trackmate.checkInput()
	if not ok:
	    sys.exit(str(trackmate.getErrorMessage()))
	    
	ok = trackmate.process()
	if not ok:
	    sys.exit(str(trackmate.getErrorMessage()))
	    
	       
	#----------------
	# Display results
	#----------------
	     
	selectionModel = SelectionModel(model)
	displayer =  HyperStackDisplayer(model, selectionModel, imp)
	displayer.render()
	displayer.refresh()
	    
	# Echo results with the logger we set at start:
	#model.getLogger().log(str(model))
	
	
	
	
	fm = model.getFeatureModel()
	norm_x = []
	norm_y = []
	for id in model.getTrackModel().trackIDs(True):
		track = model.getTrackModel().trackSpots(id)
		for spot in track:
			t=spot.getFeature('FRAME')
			
			if (t == 0.0):
				min_x = spot.getFeature('POSITION_X')
				min_y = spot.getFeature('POSITION_Y')
		for spot in track:
			
			norm_x.append(spot.getFeature('POSITION_X')-min_x)
			norm_y.append(spot.getFeature('POSITION_Y')-min_y)
	
	
	
	max_x = abs(max(norm_x, key=abs))
	max_y = abs(max(norm_y, key=abs))
	
	return max_x, max_y
		




















import os
from java.io import File

from ij import IJ, ImageStack, ImagePlus
from ij.measure import ResultsTable
from loci.plugins import BF
from ij.process import ImageStatistics as IS  



#get absolute path of the input folder
srcDir = srcFile.getAbsolutePath()

#we make sure that certain measurements are set
IJ.run("Set Measurements...", "min centroid integrated redirect=None decimal=3");

# the the list of file names in the input directory
folders = []
filenamelist = []

#create a list of subfolders
for root, directories, filenames in os.walk(srcDir):
    folders.append(root)
    filenames.sort()
    filenamelist.append(filenames)


# create output file, write header
outputfile = open(str(srcFile)+"/summary_stagerepro.csv", "w")
outputfile.write("file_id,max_x,max_y \n")

# skip irrelevant filenames, do stuff for relevant ones
for counter in range(len(folders)):
	
	srcDir = folders[counter]
	
	for filename in filenamelist[counter]:
	
		if not filename.endswith(ext):
			continue
		if "stage" not in filename:
			continue 
			
		# generate full file path for opening
		print(os.path.join(srcDir, filename))
		
		path = os.path.join(srcDir, filename)
	
		# use the Bioformats importer to open image
		IJ.run("Bio-Formats Importer", "open='" + path + "' autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");
		
		directory = srcDir
		
		
		# get stack from current image
		
		image = IJ.getImage()
		stack = image.getStack()
		title = image.getTitle()
		#print(image.getTitle())

		#define minimum separation between beads using the existing calibration (currently equivalent to 30px)
		min_separation = 30 * image.getCalibration().getX(1)
		
		
		# initialise variables for calculating in-focus slice
		maxstddev = 0
		infocus = 0
		
		# make sure the results window is clear
		IJ.run("Clear Results")

		# detect beads and measure for intensity and x/y coords
		IJ.run("Find Maxima...", "noise=30 output=[Point Selection] exclude");
		#IJ.run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel");
		IJ.run("Measure");
		rt = ResultsTable.getResultsTable()
		
		# this for loop goes over all beads
		for count in range(rt.size()):
					
			
			
			x = float(rt.getValue("X",count))
			y = float(rt.getValue("Y", count))

			
			# consider valid as default, mark it as invalid if some condition is met
			valid = 1

			# the condition will be calculated in this for loop over all beads
			for other in range(rt.size()):

				# we start from the bottom again...
				
				x_2 = float(rt.getValue("X",other))
				y_2 = float(rt.getValue("Y", other))
				
				# calculate distance between this bead and the one from the main loop...
				dist_sq = (x - x_2)**2 + (y - y_2)**2
				
				# and if they are too close (and are not the same bead), mark is as invalid
				if (x_2 != x and y_2 != y and dist_sq < min_separation**2):
					valid = 0
			
			# if this main loop bead is invalid, skip it
			if (valid == 0):
				continue
			# if it's valid, increase the done counter and actually generate PSF stuff
			else:
					

			
				IJ.selectWindow(title)
				# create a duplicate of the original that will be cropped again
				
				# we crop a 50x50px area centered at the bead
				IJ.run(image, "Specify...", "width=50 height=50 x="+str(x/image.getCalibration().getX(1))+" y="+str(y/image.getCalibration().getY(1))+" slice=1 centered")
				IJ.run("Crop")
	
				# just generating some useful string auxiliary variables
				filename = os.path.join(str(srcFile),str(title)+"_stagerepro.pdf")
				directory = os.path.join(str(srcFile),str(title)+"_stagerepro")
	
				max_x, max_y = track(image)
				image.changes = False
				image.close()
	
				# writes new line to the summary output
				
				outputfile.write(str(title)+","+str(max_x)+","+str(max_y)+"\n")

				break

		# close everything else!
		
		
		IJ.selectWindow("Results"); 
		IJ.run("Close");

		IJ.selectWindow("Log"); 
		IJ.run("Close");
		

outputfile.close()	


