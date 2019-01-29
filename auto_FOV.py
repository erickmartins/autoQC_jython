#@ File    (label = "Input directory", style = "directory") srcFile
#@ String  (label = "File extension", value=".dv") ext



"""

auto_FOV.py 
created by: Erick Martins Ratamero
date: 29/01/19
last updated: 29/01/19

Finds the relevant images with FOV tests in the input
directory, and uses MetroloJ to generate intensity values.

Inputs:
- Input directory: where the input files are (the input images should contain the string "fov")
- File extension: self-explanatory


"""




import os
from ij import IJ
from loci.plugins import BF




#get absolute path of the input folder
srcDir = srcFile.getAbsolutePath()

# the the list of file names in the input directory
folders = []
filenamelist = []

#create a list of subfolders
for root, directories, filenames in os.walk(srcDir):
    folders.append(root)
    filenames.sort()
    filenamelist.append(filenames)

    
#creates output file and writes header
outputfile = open(str(srcFile)+"/summary_fovs.csv", "w")
outputfile.write("objective,intensity \n")



# skip irrelevant filenames, do stuff for relevant ones
for counter in range(len(folders)):
	
	srcDir = folders[counter]
	
	for filename in filenamelist[counter]:
		corners = []
		if not filename.endswith(ext):
			continue
		if "fov" not in filename:
			continue 
			
		# generate full file path for opening
		print(os.path.join(srcDir, filename))
		
		path = os.path.join(srcDir, filename)
	
		# use the Bioformats importer to open image
		IJ.run("Bio-Formats Importer", "open='" + path + "' autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");

		#creates a variable for the filename without extension that will be used as an "ID"
		filename_no_ext = filename.split(".")[0]
		
		directory = srcDir
		
		
		# get stack from current image
		
		image = IJ.getImage()
		stack = image.getStack()
		title = image.getTitle()

		# create aux variable with path/filename for the PDF output of MetroloJ
		pdf = os.path.join(str(srcFile),filename_no_ext+".pdf")

		# runs MetroloJ in field illumination mode		
		IJ.run("Generate field illumination report", "steps=10 microscope=WideField wavelength=500 na=1.40 pinhole=1 text1=[Sample infos:\n] text2=Comments:\n scale=5 save save=['"+pdf+"']");

		# close the image
		image.close()

		# open output from MetroloJ
		f = open(os.path.join(str(srcFile),filename_no_ext,filename_no_ext+"_stats.xls"))
		text = f.readlines()

		# parses the four corners of illumination from XLS 
		# to floats, put them in a list
		corners.append(float(text[7].split("\t")[2]))
		corners.append(float(text[8].split("\t")[2]))
		corners.append(float(text[9].split("\t")[2]))
		corners.append(float(text[10].split("\t")[2]))
		

		# writes new line to the summary output with min value of the list
		outputfile.write(filename_no_ext+","+str(min(corners))+"\n")
		

		
# closes output
outputfile.close()	
	