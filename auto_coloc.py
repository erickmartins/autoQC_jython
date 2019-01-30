#@ File    (label = "Input directory", style = "directory") srcFile
#@ String  (label = "File extension", value=".dv") ext
#@ Integer  (label = "Number of beads", value=1) beads
#


"""

auto_coloc.py 
created by: Erick Martins Ratamero
date: 29/01/19
last updated: 30/01/19

Finds the relevant image with beads in the input
directory, crops a number of beads and uses MetroloJ
to generate colocalization/drift values.

Inputs:
- Input directory: where the input file is (the input image should contain the string "psf")
- File extension: self-explanatory
- Number of beads: how many beads should be analysed

"""




import os
from java.io import File

from ij import IJ, ImageStack, ImagePlus
from ij.plugin.frame import RoiManager
import math
from ij import WindowManager
from ij.measure import ResultsTable
from loci.plugins import BF
from ij.io import FileSaver 
from ij.process import ImageStatistics as IS  



#get absolute path of the input folder
srcDir = srcFile.getAbsolutePath()

#define minimum separation between beads in pixels


# the the list of file names in the input directory
folders = []
filenamelist = []

#create a list of subfolders
for root, directories, filenames in os.walk(srcDir):
    folders.append(root)
    filenames.sort()
    filenamelist.append(filenames)


#we make sure that certain measurements are set
IJ.run("Set Measurements...", "min centroid integrated redirect=None decimal=3");

outputfile = open(str(srcFile)+"/summary_coloc.csv", "w")
outputfile.write("file_id,bead_id,red-green,green-blue,red-blue \n")

# skip irrelevant filenames, do stuff for relevant ones
for counter in range(len(folders)):
	
	srcDir = folders[counter]
	
	for filename in filenamelist[counter]:
	
		if not filename.endswith(ext):
			continue
		if "coloc" not in filename:
			continue 
			
		# generate full file path for opening
		print(os.path.join(srcDir, filename))
		
		path = os.path.join(srcDir, filename)
	
		# use the Bioformats importer to open image
		IJ.run("Bio-Formats Importer", "open='" + path + "' autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");
		
		directory = srcDir
		
		
		# get stack from current image, cropping the centre of it
		
		IJ.run("Specify...", "width=300 height=300 x=512 y=512 slice=1 centered");
		IJ.run("Crop");
		image = IJ.getImage()
		stack = image.getStack()
		title = image.getTitle()
		print(image.getTitle())
		min_separation = 15 * image.getCalibration().getX(1)
		
		
		# initialise variables for calculating in-focus slice
		maxstddev = 0
		infocus = 0
		
		# now we go through the original image and retrieve slices to
		# detect the maximum st dev for in-focus slice
		for i in range(1, image.getNSlices()+1):
	
			
			myslice = stack.getProcessor(i)
			
			stats = IS.getStatistics(myslice)
			#print(stats.stdDev)
			if stats.stdDev > maxstddev:
			
				maxstddev = stats.stdDev
				infocus = i
				#print(i,infocus,maxstddev)
	
		# we set the relevant z-slice to be the maximum std dev one and get
		# that stack (multiple channels)
		IJ.run("Duplicate...", "duplicate slices="+str(infocus))
		im_slice = IJ.getImage()
		
		
		# creating the output summary file and writing headers
		
		
		# make sure the results window is clear
		IJ.run("Clear Results")

		# detect beads and measure for intensity and x/y coords
		IJ.run("Find Maxima...", "noise=30 output=[Point Selection] exclude");
		#IJ.run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel");
		IJ.run("Measure");
		

		rt = ResultsTable.getResultsTable()

		# "done" is a variable for the number of valid beads calculated - when it reaches
		# the number of beads we want to look at, we're done
		done = 0

		im_slice.changes = False
		im_slice.close()

		image.changes = False
		image.close()
		# this for loop goes over all beads
		for count in range(rt.size()):
			# break condition for the number of beads we want to see
			if (done >= beads):
				break
		
			
			# we start from the bottom because we want the lowest intensities first
			order = rt.size()-count-1
			x = float(rt.getValue("X",order))
			y = float(rt.getValue("Y", order))

			# these are single points, so the intensity is the same as max intensity
			intensity = int(rt.getValue("Max", order))

			# consider valid as default, mark it as invalid if some condition is met
			valid = 1

			# the condition will be calculated in this for loop over all beads
			for other in range(rt.size()):

				# we start from the bottom again...
				order = rt.size()-other-1
				x_2 = float(rt.getValue("X",order))
				y_2 = float(rt.getValue("Y", order))
				# calculate distance between this bead and the one from the main loop...
				dist_sq = (x - x_2)**2 + (y - y_2)**2
				
				# and if they are too close (and are not the same bead), mark is as invalid
				if (x_2 != x and y_2 != y and dist_sq < min_separation**2):
					valid = 0
			print(x,y,valid)
			# if this main loop bead is invalid, skip it
			if (valid == 0):
				continue
			# if it's valid, increase the done counter and actually generate PSF stuff
			else:
				done = done + 1
			IJ.run("Bio-Formats Importer", "open='" + path + "' autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");
			IJ.run("Specify...", "width=300 height=300 x=512 y=512 slice=1 centered");
			IJ.run("Crop");
			image = IJ.getImage()
			stack = image.getStack()
			title = image.getTitle()
			

			
			IJ.selectWindow(title)
			# create a duplicate of the cropped original that will be cropped again
			IJ.run("Duplicate...", "duplicate")
			image_2 = IJ.getImage()
			image_2.setTitle("duplicate_spot")

			# we crop a 20x20px area centered at the bead
			IJ.run(image_2, "Specify...", "width=50 height=50 x="+str(x/image.getCalibration().getX(1))+" y="+str(y/image.getCalibration().getY(1))+" slice=1 centered")
			IJ.run("Crop")

			# just generating some useful string auxiliary variables
			filename = os.path.join(str(srcFile),str(title)+"_coloc_bead_"+str(count)+".pdf")
			directory = os.path.join(str(srcFile),str(title)+"_coloc_bead_"+str(count))


			IJ.run("Split Channels");
			IJ.selectWindow("C4-duplicate_spot")
			IJ.getImage().close()

			image.changes = False
			image.close()
			
			# run automated MetroloJ, save results + PDF
			
			IJ.run("Generate co-alignement report", "title_of_report=[] stack_1=C1-duplicate_spot stack_2=C2-duplicate_spot stack_3=C3-duplicate_spot microscope=WideField wavelength_1=400 wavelength_2=500 wavelength_3=600 na=1.40 pinhole=1 text1=[Sample infos] text2=Comments save save=["+filename+"]");

			
			
			# close the tiny crop
			IJ.selectWindow("C1-duplicate_spot")
			IJ.getImage().close()
			IJ.selectWindow("C2-duplicate_spot")
			IJ.getImage().close()
			IJ.selectWindow("C3-duplicate_spot")
			IJ.getImage().close()
			#image_2.close()

			# open output from MetroloJ
			f = open(directory + "/"+str(title)+"_coloc_bead_"+str(count)+".xls")
			text = f.readlines()

			

			# parses from XLS to a float, multiply by the correction factor
			rg = float(text[14].split("\t")[2].split("(")[0]) 
			gb = float(text[15].split("\t")[3].split("(")[0]) 
			rb = float(text[14].split("\t")[3].split("(")[0]) 

			# writes new line to the summary output
			print(str(title)+","+str(count)+","+str(rg)+","+str(gb)+","+str(rb)+"\n")
			outputfile.write(str(title)+","+str(count)+","+str(rg)+","+str(gb)+","+str(rb)+"\n")
			f.close()

		# close everything else!
		
		image.changes = False
		image.close()		
		IJ.selectWindow("Results"); 
		IJ.run("Close");
		

outputfile.close()	
	