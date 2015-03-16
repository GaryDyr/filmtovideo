#Python code run under ImageJ that was an attempt to fix washed out images by using mean data on each line
#this turned out to not to work well, because the problem is r, g, b luminance dependent, which means 
#correction had to be on a pixel by pixel basis, not row by row basis.

#there is a lot of stuff here that was not implemented and was for testing purposes.
#about all that it helps is for how to use ROI to do stuff as examples.

#bto find and print means shutter Image (PSI) on 
#video frames in an AVI movie sequence. 
# code uses Python 2.5 (e.g., Jython) and ImageJ 1.49d
#Fiji-ImageJ does not recognize latest Python 3.x print function change using
#paranthesis and does not allow numpy package, which would simplify the matrix
#code substantially.

#THIS CAN BE SPED UP BY RUNNING FROM THE COMMAND LINE, BUT REQUIRES A REWRITE SO THAT
#ALL INPUT IS EITHER AUTOMAITC OR FROM THE COMMAND LINE. THE FOLLOWING COMMAND LINE EXAMPLE 
#MAY BE USEFUL, ONCE EVERYTHING IS CONVERTED. REALLY THE ONLY CONVERSION SHOULD BE THAT FOR EACH 
#COMMAND LINE RUN THE AVI FILE NAME NEEDS TO BE CHANGED.

#fiji-linux64 --headless --jython ./scripts/PSI_avi_Processor.py -batch &

#Requies two files: 
# 	1. 	A csv file of two connected mormalized PSI profiles  (2 x wavelength)
#		Default file name: "PSI_norm_1358.csv" in /templating_files/ folder
#	2. A csv file of correction coefficients with file name LumCorr.csv in /templating_files/
#See doc file for details on how to get these files.
#AND several specific folders under a single drive or folder:
	#
"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
FIJI - IMAGEJ PYTHON CODE 
STREAMLINE METHOD - IGNORE DISTORTION
This process ignores the known distortion that is observed in the video frames and compares the 
image sub section against the base or normalized PSI at th specified interval rows. 
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
A critcal tutorial for Fiji/ImageJ and Python is:http://www.ini.uzh.ch/~acardona/fiji-tutorial/#s2
"""
from ij import IJ, ImagePlus, ImageStack
import ij.io
import ij.gui 
import math
import csv
import operator
import os
import shutil
from math import sqrt
import csv
import sys
import thread
import time
from ij.process import ImageStatistics as IS
from ij.io import OpenDialog
from ij.gui import GenericDialog 
from ij.io import FileSaver
from math import sqrt
from jarray import zeros #jarray is a Jython module that implements only two methods, zeros and array
from operator import itemgetter
from java.io import File 
import java.io.File.__dict__ 
from mpicbg.imglib.image.display.imagej import ImageJFunctions as IJF
import ij.VirtualStack 
from ij.gui import NewImage
from ij.plugin import AVI_Reader # added June, 2014 after upgrading to Imagej2, needed explicitly
from ij.gui import NewImage
from ij.gui import Roi
import ij.plugin.frame.RoiManager 
from ij.gui.Roi import drawPixels
from ij.plugin import AVI_Reader # added June, 2014 after upgrading to Imagej2, needed explicitly
from ij.gui import ProfilePlot # had to add in ImageJ2
import ij.measure
from ij.measure import Measurements
from ij.measure import ResultsTable
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#SET ALL DRIVE AND FOLDER PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#SEE http://www.ini.uzh.ch/~acardona/fiji-tutorial/#generic-dialog FOR STARTER IDEAS.
# set working drive and main folder if needed
DriveOption = "F" #either C, E, G, X is for dialogues to choose diectories
default_path = "ImageJ Stuff\\" 
def getPaths():   
	#used if not hardwiring some paths
	#java.io.File would not work to get drives. but going through dict works
	#to get java.io.File functions; they are many; saw this in jython tutorials
	#next not used, but good to know
	#driveslist =java.io.File.__dict__['listRoots']()
	#driveslist is an array, not list
	#driveslist=list(driveslist)
	#gd.addChoice("pick drive:", driveslist, drivelist[1]) 
	os.chdir("F:\\")
	default_drivepath = DirectoryChooser("Choose Top Level Drive or Drive:/Directory").getDirectory()
	os.chdir(default_drivepath)
	default_path = DirectoryChooser("Folder containing python files-usually ImageJ stuff").getDirectory()
	avi_inpath = DirectoryChooser("Choose folder of inbound avi").getDirectory()
	avi_outpath = DirectoryChooser("Choose folder where new avi file will be placed").getDirectory()
	imagepath = DirectoryChooser("Choose folder for storage of separate avi image files").getDirectory()
	templatingfiles = DirectoryChooser("Choose folder where PSI & luminance csv files located.").getDirectory()
	gd = GenericDialog("Paths")   
	gd.addStringField("Starting Drive:/ or Drive/Folder",default_drivepath,40)
	gd.addStringField("Main ImageJ Stuff directory",default_path,40) 
	gd.addStringField("avi inbound folder",avi_inpath,40) 
	gd.addStringField("avi outbound folder",avi_outpath,40)
	gd.addStringField("png stack files folder",imagepath,40)
	gd.addStringField("CSV PSI & luminance correction values folder",templatingfiles,40)
	
	os.chdir(default_drivepath) 

	# Read out the files    	
	default_drivepath = gd.getStringFields().get(0).getText()
	default_path = gd.getStringFields().get(1).getText()	
	avi_inpath = gd.getStringFields().get(2).getText()
	avi_outpath = gd.getStringFields().get(3).getText()
	imagepath = gd.getStringFields().get(4).getText()	
	templatefiles = gd.getStringFields().get(5).getText()
	gd.showDialog()   
	#   
	if gd.wasCanceled():   
		print "User canceled dialog!"  
		print 'default_drivepath',default_drivepath
		print 'default_path', default_path
		print 'avi_inpath', avi_inpath 
		print 'avi_outpath', avi_outpath 
		print 'imagepath', imagepath 
		print 'templatefiles', templatefiles 
	  	return default_path, imagepath, avi_inpath, avi_outpath, templatefiles


#Set all drive and f
if DriveOption == "C":
	default_drivepath = "C:\\Canon\\" 
elif DriveOption == "F":
	default_drivepath = "F:\\Canon\\"
elif DriveOption == "X":
	thepaths=getPaths() #uses dialogue
	default_path,  avi_inpath, avi_outpath, imagepath, templatefiles = thepaths

#set directory paths
if DriveOption != "X":
	default_path = default_drivepath+"ImageJ Stuff\\" # use forward slashes or 2 back slashes for these
	templatefiles = default_drivepath+"templating_files\\"
	imagepath = default_drivepath+"imagedump\\"
	avi_inpath = default_drivepath+"avi_out\\"
	avi_outpath = default_drivepath+"avi_out\\"

print default_path, templatefiles,imagepath, avi_inpath, avi_outpath 

#get path to standard PSI profile and luminanance correction coef.
corrf = templatefiles+"LumCorr.csv"
PSIf = templatefiles+"PSI_norm_1358.csv"
print avi_inpath
#os.chdir(avi_inpath) does not work anymore!!!!!!!!!
d1 = os.getcwd()  
print d1
#+++++++++++++++ End Drive and Folder Stuffs++++++++++++++++++++++++++++++++++++++++++

# Dialog to set some parameters, not really used; parameters hard set
def getParameters():   
	gd = GenericDialog("Parameters")   
	gd.addMessage("Width, height, and standard PSI starting width are hardwired values. Shown for reference only.")
	gd.addNumericField("Image Width", ImgWidth, 0)  # show no decimals
	gd.addNumericField("Image Height", ImgHt, 0)  
	gd.addNumericField("Standard PSI width of normalized PSI profile", stdWidth, 0)  # show 2 decimals   
	gd.addCheckbox("Correct row luminance distortion", True)   
	gd.addCheckbox("use csv file for luminance correction factors", True)   
	gd.showDialog()   
 	if gd.wasCanceled():   
		print "User canceled dialog!"
		sys.exit() 
	CorrectLuminance = gd.getNextBoolean()
	corr_file = gd.getNextBoolean()	   
  	print CorrectLuminance, corr_file 
	return CorrectLuminance, corr_file

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#SET ALL GLOBAL PARAMETERS HERE 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
slicecutter = 1		# slices to skip
nstart = 0 # starting frame to pick up only white leader frames PSIs 
nstop = -1 #10 # set to -1 means do all frames
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#NOTE THAT IN THIS SPECIFIC CASE RIGHT NOW WE ARE SKIPPING FIRST FRAME BECAUSE IT 
#IS NOT A VALID MOVIE FRAME, JUST A HEADER TO INDICATE 100s
#change the range from 2 back to 1 for real data.
#++++++++++++++++++++++++++++++++++++++++
#CRITICAL INFO THAT MUST BE SUPPLIED FROM OTHER METHODS
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
stdWidth = 1358		# width of the normalized PSI
UserWidth = 1358	# user chosen override width; use lock_PSI_width = 3
AverWidth = 1358    # just a holder AverWidth is determined if lock_PSI_width.
NewWidth = stdWidth	# place holder width. NewWidth is determinted by lock_PSIwidth
lock_PSI_width = 2 #Values are: 0 use stdwidth; 1 - lock to overall average of pma widths; 2 use moving average frame width; 3 - lock to user chosen width
B1 = 1166.910722 #Blanking interval obtained from rotating camcorder info
#
# Next factor is appled to PSI template as an experimental factor to improve light variance
# between PSI and image; 1.0 is no multiplier factor; > 1.0 is an increase in whiteness for each pixel, 
# which has the effect of enhancing the PSI values of the template correction; applied in GetTemplate
PSILightFactor = 0.40
ImgHt = 1080
ImgWidth = 1920
#csize = ImgHt + int(0.25*float(ImgHt)) # variable used to expand row size when PSI width > stdWidth
CorrectLuminance = True # If true, use PSI profile corrected for luminace, normally set to True
CorrectLuminance2 = True # if true correct for sinusodal frame luminance distortion.

#next four values used to create final rectangle, usually will mirror values used for finding centers in template script.
topPt =0 #60				# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240					# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020          # bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680 				# rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
IBase=255 # not used directly

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#Check or set parameters
gp = getParameters()
HB = ImgHt + B1
CorrectLuminance, corr_file =gp

#Excel stores numbers in a csv file without quotes, with a comma as separator
#the QUOTE_NUMERIC parameter converts to a float value internal to reader
#using 'with' is apparently safer code for cleanup on exceptions
#but next line not available in jython 2.5?? gives error about new keyword in 2.6
#with open(default_path+PSIf) as f:
	#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
#CHOOSE THE AVI FILE NOW SO CAN GET PROPER CENTERS FILE.
#avi_file = OpenDialog("Choose the AVI file to fix", None)
od = OpenDialog("Choose the avi file",avi_inpath, None)   
filename = od.getFileName() 
if filename is None:   
	print "User canceled the dialog.Exiting!"  
	sys.exit()
else:   
	directory = od.getDirectory()   
	avi_file = directory + filename   
	print "Selected file path:", avi_file   
	(file_name, file_ext) = os.path.splitext(filename) 
	#Finaly get corresponding centers file
	Centersf = avi_outpath+"Cntrs_"+file_name+".csv"

#override above for testing
#avi_file = avi_inpath+"Leader Tests 1.avi"
#Centersf = avi_inpath+"Cntrs_Leader Tests 1.csv"
print 'Base file name:',file_name

f = open(Centersf,'r') #python 2.5
rdr = csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)
#slices, FramePos, raw, pcc, pn, pw, pcnp, pnw,pma = zip(*rdr) 
slices, pcn, pma, flc = zip(*rdr) 
# above a bit esoteric-> "*rdr" unpacks the elements of each line; zip takes tuple of each row such that successive 
#elements of each row are now tuples. The tuples can be accessed as lists by zip(*array)[column #, e.g. 0]
f.close()
# slice =	frame #; 
# pcn =    predicted center based on n+1 and n-1 PSI width for n;
# pma =    moving average width based on moving average chunk of MovAvgRng, normally set to 1 s of film = 18 frames
# flc  =   frame luminance rgb correction value for entire frame;'

HB = ImgHt + B1 	

#convert the tuples to lists
slices =list(slices)
#WE WILL USE PCN AS BEST VALUES
FramePos = list(pcn)
pma = list(pma)
flc = list(flc)
print FramePos

def computeStdDev(pixels, mean): # not used here
	#usage  stdDev = computeStdDev(ip.getPixels(), mean) this would do it for the entire image, but will not work for rgb image.
	for i in range(len(pixels)):
		s += pow(pixels[i] - mean, 2)
	return sqrt(s / float(len(pixels) -1))


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WORK THE AVI IMAGES.
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# with the help of Wayne Rasband on the listserver, this is the way 1.47 opens the
#avi stack for reading the slices etc

#AVI FILE WAS CHOSEN EARLIER...JUST OPEN IT
stack = AVI_Reader.openVirtual(avi_file) 
#alternate method when Jython catches up with 64 bit Pyhton loadtxt is a numpy function
#PSI = numpy.loadtxt(open(PSIf,"r"),delimiter=",",skiprows=0, dtype=int)
#openVirtual does this: (taken from http://imagej.nih.gov/ij/source/ij/plugin/AVI_Reader.java)
	#public static ImagePlus open(String path, boolean virtual) {
	#AVI_Reader reader = new AVI_Reader();
	#ImageStack stack = reader.makeStack (path, 1, 0, virtual, false, false);
	#if (stack!=null)
	#return new ImagePlus((new File(path)).getName(), stack);
#     * @param path             Directoy+filename of the avi file
#     * @param firstFrame  		Number of first frame to read (first frame of the file is 1)
#     * @param lastFrame   		Number of last frame to read or 0 for reading all, -1 for all but last...
#     * @param isVirtual        Whether to return a virtual stack
#     * @param convertToGray    Whether to convert color images to grayscale
#     * @return  Returns the stack; null on failure.
#    *  The stack returned may be non-null, but have a length of zero if no suitable frames were found
#print "size="+imp.getStackSize(); 
#Note imp is now the stack name in this method

stack.show() 
stack_ID = stack.getID() 

print 'stack_ID', stack_ID, 'stack_title', stack.getTitle

if nstop == -1: 
	AllSlices = stack.getStackSize()
	nstop = AllSlices - 1
else:
	AllSlices = nstop
print 'slices to process:', nstop
ImgWidth = stack.getWidth() 
ImgHt = stack.getHeight()

stack2 = ij.VirtualStack(ImgWidth, ImgHt, None, imagepath)
stack2ID = stack.getID()
#stack2 = ImageStack(ImgWidth, ImgHt) #this opens an image stack, but not a virtual stack, so only can work off available RAM
#Future reference. Virtual stack is read only, to manipulate it, duplicate it. Does not make sense. why have an addslice if true.

maxslices = int((AllSlices-nstart)/slicecutter)
print 'AllSices', AllSlices,'maxslices', maxslices
#pre-calc the camcorder total row cycle vert.blanking region + video frame height
#Ftotrows = B1+ImgHt

#set up lists for the new csv output file; output only necessary parameters.
#NewSlices = [0]*(maxslices+1)
#NewFramePos = [0]*(maxslices+1)
#Newpma = [0]*(maxslices+1)
#ewflc = [0]*(maxslices+1)
kk = 0

#convert FramePos to integers for later use
#WE WILL NOT DO THIS SORTING BECAUSE THE PROCESS CAN GO AWRY AND WE END UP WITH OUT OF SEQUENCE FRAMES
#WE CANNOT REASSEMBLE. aLSO, WE DEPEND ON THE PREVIOUS WIDTH VALUE TO BE CORRECT, IT WILL NOT BE IF WE
#SKIP AROUND.
#REDUCE CALC TIME - DOUBLE SORT DATA, FIRST BY MONVING AVER. PSI WIDTHS, THEN BY PSI CENTER POSITION.
#Round PSI widths to nearest thenth row and convert to integer
#- reduces number of unique PSI widths at some expense of accuracy
slices = [int(x) for x in slices]
FramePos = [int(x) for x in FramePos]
#PROCESS IMAGES LOOP
#--------------------------------------------------------------------------------
# This is the start of the loop to run through all frames of the video sequence
#because the data is sorted we will just 
starttime = time.time()
count = 0
#GETTING STUCK AS FRAME 1 AFTER FIRST FRAME
t_ID = 0
OldWidth = stdWidth
OldPSICenter = -1 #a PSICenter may start at zero or greater.
pcase = 3

print 'starting frame:', nstart, 'stop frame:', nstop

#++++++++++++++++++++MAIN IMAGE PROCESSING LOOP++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#set nstart so it is reading only the true frame numand not following just an index.

print 'frames numbers to process:'+str(nstart)+' to '+str(nstop)
IJ.run("Set Measurements...", "mean standard min max stack redirect=None decimal=3")
#get statistics and histogram; getStatistics automatically makes histogram available.
#options = IS.MEAN | IS.MIN_MAX |IS.STD_DEV
imp = ij.WindowManager.getImage(stack_ID) #focus on stack
ip=imp.getProcessor().duplicate() #gets processor from duplicate slice to check if RGB
pixnum = ip.getPixelCount()		
type = imp.getType()
if ImagePlus.COLOR_RGB != type:	print 'Stack does not contain RGB images' 
# Set the range of frames to get the ROI on either side of the frame being analysed.
Frame_Rng = 6
stdROI = Roi(1810, 0, 80, 1080)
ImgWidth = stack.getWidth() 
ImgHt = stack.getHeight()
#stats = IS.getStatistics(ip,options, imp.getCalibration()) 
#print "mean:", stats.mean, "median:", stats.median, "area:", stats.area,  "max",stats.max,"min", stats.min # area is always available
#lum_mean = stats.min
PSICntr = FramePos[1]
#rt = ResultsTable()
rt = ResultsTable.getResultsTable()
IJ.run("Measure")
rt.setValue("Center",0, PSICntr) # automatically will create col and add value to it
		#showPixels(ip) does not work
rt.show("Results")
Rrow = 0
for i in range(nstart,nstop):
	PSICntr = FramePos[i]
	if 0 <= PSICntr < 1080:	#make sure we get proper image from stack; a bit convoluted to isolate proper image from stack	
		slice = stack.setSlice(i) #indx taken directly from cvs first column
		#The relationship of slice and stack is a bit confusing. regardless of slice called, the
		#id returned is always the stackID. 
		
		# no idea what the following is really measuring, but it has nothing to do with the roi I set
		# and puts up no roi boundary lines on image; maybe need to create instance of ROI manager, or work
		#with the floatprocessor?
		#img = ij.WindowManager.getCurrentImage()
		#ip=img.getProcessor()
		#CntrROI = Roi(400, PSICntr, 1120, 40)
		#bounds = CntrROI.getBounds()
  		#print bounds.x, bounds.y,bounds.width, bounds.height
		#stats = IS.getStatistics(ip,options, img.getCalibration())
		#print "mean:", stats.mean, "median:", stats.median, "area:", stats.area,  "max",stats.max,"min", stats.min
		# standard makeRectangle comes to the rescue.
		IJ.makeRectangle(400, PSICntr, 1120, 40)
		#rt.setValue("Center",Rrow, PSICntr) # automatically will create col and add value to it
		Rrow = Rrow+1
		IJ.run("Measure")
		rt.setValue("Center",Rrow, PSICntr)
		rt.show("Results")
		#showPixels(ip) does not work
		#typically look for a maximum in the stddev 
		if int(Frame_Rng/2) <= i < maxslices - int(Frame_Rng/2):
			si = i - int(Frame_Rng/2)
			ei = i + int(Frame_Rng/2)
		elif i <= int(Frame_Rng/2):
			si = 1
			ei = 5
		elif i > maxslices-Frame_Rng:
			si = maxslices - Frame_Rng
			ei = maxslices
		else:
			pass
		for k in range(si,ei):
			slice = stack.setSlice(k)
			IJ.run("Measure")
			Rrow = Rrow + 1
			rt.setValue("Center",Rrow, PSICntr)
			rt.show("Results")
			#rt.setValue("Center",Rrow, PSICntr)

sys.exit()
#see for ResultsTable class: http://rsbweb.nih.gov/ij/developer/api/ij/measure/ResultsTable.html


#rt.incrementCounter()
#if rt.columnExists(1): 
#	print 'was created'
#else:
#	print 'cant find column'
#for i in range(len(profile)):
#	rt.incrementCounter() #must use this internal counter;add value does not work as might think from docs.
#rt.addValue(1, profile[i]) # using name as header name.
	#rt.setValue(0,i,profile[i]) #adds to specific row
	#rt.show("Average")
	
	
	#NewMax = int(-0.0594*ARow + 244.86) 
	#NewMin = int(0.0588*ARow + 9.2688) 
#	ip=imp.getProcessor()
#	roi = Roi(lftPt, n, ImgWidth - 2*lftPt, RowsToAdjust)
#	ip.setRoi(roi)
#	if NewMax > 255: NewMax = 255
#		if NewMin < 0: NewMin = 0
		#print 'zeroRow', zeroRow, 'zeroRow+n', zeroRow+n,'halfwidth', halfPSI,'ARow', ARow,'NewMin', NewMin, 'NewMax', NewMax
		#print "mean:", stats.mean, "min", stats.min,"max",stats.max, 'NewMin', NewMin, 'NewMax', NewMax
		#Apply to the row.
		#ip=imp.getProcessor()
		#roi = Roi(lftPt, n, ImgWidth - 2*lftPt, RowsToAdjust)
		#ip.setRoi(roi)
#		IJ.makeRectangle(lftPt, n, ImgWidth - 2*lftPt, RowsToAdjust)
#		IJ.setMinAndMax(NewMin,NewMax)
	#if indx == 4: sys.exit()
	#if i == 6: # slices are 0 to end -1 so 6 is slice 7
	#	sys.exit()	
		#result file of calc.
#	corImg = ij.WindowManager.getCurrentImage()
#	corImg.setTitle("out_"+str(indx)+".png")
		
	#imagestack can add a slice after a specifed slice. virtualstack cannot, but it reads file in a sequence. 
	#imp = ImagePlus(stack.getLabel(i), ip) 
#	out_image = imagepath+corImg.getTitle()
#	FileSaver(corImg).saveAsPng(out_image) 
#	stack4.addSlice(corImg.getTitle())
#	corImg.close()
#	count+=1
#more test stuff - works and shows blurred file as new.png
	#ip = dimage.getProcessor()
	#sliceFileName = default_path+"new.png"   
	#FileSaver(dimage).saveAsPng(sliceFileName)    
	#test stuff end
	#profile = ProfilePlot(img, True)	
	#Prof = profile.getProfile()


#selectWindow("stack3.avi");
#run("Duplicate...", "title=stack3-1.avi");
#//run("Brightness/Contrast...");
#selectWindow("stack3.avi");
#selectWindow("stack3-1.avi");
#setMinAndMax(21, 233);
#run("Apply LUT");
#// Copies the display range of the active 
#// image to all open images.
#macro "Propagate Display Range..." {
 #   getMinAndMax(min2, max2);
#    ok = getBoolean("The display range ("+min2+"-"+max2+") of the current\n"
 #       +"image will be propagated to all open images.");
#    if (!ok) exit();
#    for (i=1; i<=nImages; i++) {
#       selectImage(i);
 #       setMinAndMax(min2, max2);
 #   }
#}
#setMinAndMax(min, max, channels) ALTERNATE CALL TO SET INDIVIDUAL CHANNELS
# Sets the display range of specified channels in an RGB image, where 4=red, 2=green, 1=blue, 6=red+green, etc.
# Note that the pixel data is altered since RGB images, unlike composite color images, do not have a LUT for each channel. 
#jython example: imp.getProcessor().setMinAndMax(0, w-1) where imp is an ImagePlus object. see Cardona
#it appears the set does the operation as well as sets the LUT (look up table limits.
#To get parameters do this, where imp again is the ImagePlus object:  should work on ROI if exists
#stats = imp.getStatistics(Measurements.MEAN | Measurements.MEDIAN | Measurements.AREA)
#print "mean:", stats.mean, "median:", stats.median, "area:", stats.area
 
	#if i == 6: # slices are 0 to end -1 so 6 is slice 7
	#	sys.exit()	


print "Done"
gdend = GenericDialog("Finished")
gdend.addMessage("Done.File saved as: "+AVI_file_out) 
gdend.showDialog()
sys.exit()

#CAN AND CAN'T DOES WITH VIRTUAL STACKS
#YOU CAN BRING IN AVI FILES AS A VIRTUALSTACK.
#I COULD NOT FIND A WAY TO BRING IN AN AVI FILE AS A BFVIRTUALSTACK.
#BFVIRTUALSTACK CALLS WILL NOT OPEN AVI FILES?
#YOU CAN SAVE A VIRTUAL STACK AS AN AVI- BUT YOU MUST GENERATE AND PUT OUT ON DISK EACH IMAGE IN A NUMBERED SEQUENCE
#TAKES LONG TIME TO CONVERT A DISK BASED STACK TO AN AVI FILE WHEN DISK FILES ARE PNG & PROBABLY JPEG.
#YOU CANNOT SUBSTITUE AN IMAGE IN A VIRTUALSTACK addSlice() METHOD HERE DUMPS ONLY TO DISK
#addSlice() METHOD WITH IMAGESTACKS ALLOWS ARRANGING SLICES OF STACK, BUT LIMITED BY MEMORY FOR LARGE OR MANY FILES.
#IMPORT BIOFORMATS INSISTS ON OPENING UP FILES, EVEN PNG FILES, WITH STACK OF THREE CHANNELS. IF
#YOU INDICATE USE VIRTUALSTACK IT OPENS UP 4 CHANNELS THREE IN COLOR AND ONE THAT PROBABLY REPRESENTS TRANSPARENCY.
#IF YOU OPEN A PNG WITH VIRTUAL STACK NOT CHECKED, YOU GET FOUR GREY IMAGES.
#BASICALLY, STAY AWAY FROM BIOFORMATS FOR THE WORK HERE, IF WE CONTINUE TO USE AVI FILES. IF WE FIRST BREAK OUT INTO 
#PNG FILES, THEN THE AUTOBREAK OUT INTO CHANNELS TO DIRECTLY SUBTRACT FROM THE TEMPLATE MIGHT HAVE SOME WORTH.

