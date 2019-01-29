#@ File    (label = "Input directory", style = "directory") srcFile
#@ String  (label = "File extension", value=".dv") ext
#@ Integer  (label = "Number of beads", value=10) beads
#@ Float  (label = "Correction Factor (x)", value=1.186) corr_factor_x
#@ Float  (label = "Correction Factor (y)", value=1.186) corr_factor_y
#@ Float  (label = "Correction Factor (z)", value=1.186) corr_factor_z


"""

auto_PSF.py 
created by: Erick Martins Ratamero
date: 25/01/19
last updated: 24/01/19

Finds the relevant image with beads in the input
directory, crops a number of beads and uses MetroloJ
to generate resolution values.

Inputs:
- Input directory: where the input file is (the input image should contain the string "psf")
- File extension: self-explanatory
- Number of beads: how many beads should be analysed
- Correction factors: multiplying factor for the FWHM resolution output from MetroloJ, per dimension

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
min_separation = 15

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

# skip irrelevant filenames, do stuff for relevant ones
for counter in range(len(folders)):
	
	srcDir = folders[counter]
	
	for filename in filenamelist[counter]:
	
		if not filename.endswith(ext):
			continue
		if "psf" not in filename:
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
		
		# initialise variables for calculating in-focus slice
		maxstddev = 0
		infocus = 0
		
		# now we go through the original image and retrieve slices to
		# detect the maximum st dev for in-focus slice
		for i in range(1, image.getNSlices()+1):
	
			
			myslice = stack.getProcessor(i)
			
			stats = IS.getStatistics(myslice)
			if stats.stdDev > maxstddev:
			
				maxstddev = stats.stdDev
				infocus = i
				#print(i,infocus,maxstddev)
	
		# we set the relevant z-slice to be the maximum std dev one and get
		# that "stack" (it's a single slice)
		zslice = infocus
		findbeads = stack.getProcessor(zslice)
		
		# we create a new image from that z-slice and display it
		im_slice = ImagePlus("stack", findbeads)
		im_slice.show()

		# creating the output summary file and writing headers
		outputfile = open(str(srcFile)+"/summary_psfs.csv", "w")
		outputfile.write("bead_id,x_resolution,y_resolution,z_resolution \n")
		
		# make sure the results window is clear
		IJ.run("Clear Results")

		# detect beads and measure for intensity and x/y coords
		IJ.run("Find Maxima...", "noise=30 output=[Point Selection] exclude");
		IJ.run("Measure");

		rt = ResultsTable.getResultsTable()

		# "done" is a variable for the number of valid beads calculated - when it reaches
		# the number of beads we want to look at, we're done
		done = 0

		# this for loop goes over all beads
		for count in range(rt.size()):
			# break condition for the number of beads we want to see
			if (done >= beads):
				break
		
			im_slice.show()
			# we start from the bottom because we want the lowest intensities first
			order = rt.size()-count-1
			x = int(rt.getValue("X",order))
			y = int(rt.getValue("Y", order))

			# these are single points, so the intensity is the same as max intensity
			intensity = int(rt.getValue("Max", order))

			# consider valid as default, mark it as invalid if some condition is met
			valid = 1

			# the condition will be calculated in this for loop over all beads
			for other in range(rt.size()):

				# we start from the bottom again...
				order = rt.size()-other-1
				x_2 = int(rt.getValue("X",order))
				y_2 = int(rt.getValue("Y", order))
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
				done = done + 1

			IJ.selectWindow(title)
			# create a duplicate of the cropped original that will be cropped again
			IJ.run("Duplicate...", "duplicate")
			image_2 = IJ.getImage()
			image_2.setTitle("duplicate_spot")

			# we crop a 20x20px area centered at the bead
			IJ.run(image_2, "Specify...", "width=20 height=20 x="+str(x)+" y="+str(y)+" slice=1 centered")
			IJ.run("Crop")

			# just generating some useful string auxiliary variables
			filename = os.path.join(str(srcFile),"psf_bead_"+str(count)+".pdf")
			directory = os.path.join(str(srcFile),"psf_bead_"+str(count))

			# run automated MetroloJ, save results + PDF
			IJ.run("Generate PSF report", "microscope=WideField wavelength=500 na=1.40 pinhole=1 text1=[Sample infos:\n] text2=Comments:\n scale=5 save save=['"+filename+"']")

			# close the tiny crop
			IJ.selectWindow("duplicate_spot")
			image_2.close()

			# open output from MetroloJ
			f = open(directory + "/psf_bead_"+str(count) + "_summary.xls")
			text = f.readlines()

			# parses from XLS to a float, multiply by the correction factor
			x_res = float(text[1].split("\t")[1].split(" ")[0]) * corr_factor_x
			y_res = float(text[2].split("\t")[1].split(" ")[0]) * corr_factor_y
			z_res = float(text[3].split("\t")[1].split(" ")[0]) * corr_factor_z

			# writes new line to the summary output
			outputfile.write(str(count)+","+str(x_res)+","+str(y_res)+","+str(z_res)+"\n")
			f.close()

		# close everything else!
		im_slice.close()
		image.changes = False
		image.close()		
		IJ.selectWindow("Results"); 
		IJ.run("Close");
		

		outputfile.close()	
	