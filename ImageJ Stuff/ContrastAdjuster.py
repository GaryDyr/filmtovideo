#Python code run under ImageJ to find the projector shutter Image (PSI) center position on 
#video frames in an AVI movie sequence. 

#OUTPUT OF THIS FILE IS TO STACK4.AVI

# code is based on Fiji implementation, which uses Python 2.5 and ImageJ 1.49
#Fiji-ImageJ does not recognize latest Python 3.x print function change using
#paranthesis and does not allow numpy package, which would simply the matrix
#code substantially.

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
from ij.gui import Roi
from ij.plugin.frame import RoiManager
from ij.plugin import AVI_Reader # added June, 2014 after upgrading to Imagej2, needed explicitly
from ij.gui import ProfilePlot # had to add in ImageJ2
import ij.measure
from ij.measure import Measurements
from ij.measure import ResultsTable
#from numpy import * not allowed in Jython.
#SET ALL PARAMETERS HERE
#SET ALL GLOBAL PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
nstart = 1 # starting frame to pick up only white leader frames PSIs 
nstop = -1 #10 # set to -1 means do all frames
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#NOTE THAT IN THIS SPECIFIC CASE RIGHT NOW WE ARE SKIPPING FIRST FRAME BECAUSE IT 
#IS NOT A VALID MOVIE FRAME, JUST A HEADER TO INDICATE 100s
#change the range from 2 back to 1 for real data.
#++++++++++++++++++++++++++++++++++++++++
#CRITICAL INFO THAT MUST BE SUPPLIED FROM OTHER METHODS
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
stdWidth = 1358			# width of the normalized PSI
              # width to use for entire stack if desired.
NewWidth = stdWidth
B1 = 1166.910722 #Blanking interval obtained from rotating camcorder info
ImgHt = 1080
ImgWidth = 1920
#next four values used to create final rectangle, usually will mirror values used for finding centers in template script.
topPt =0 #60				# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240					# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020          # bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680 				# rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
IBase=255

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#FOR PRODUCTION RUNS WILL NEED TO IMPLEMENT OPENDIALOG, SAVEDIALOG AND PROBABLY GENERICDIALOG METHODS
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
	if gd.wasCanceled():   
		print "User canceled dialog!"  
		print 'default_drivepath',default_drivepath
		print 'default_path', default_path
		print 'avi_inpath', avi_inpath 
		print 'avi_outpath', avi_outpath 
		print 'imagepath', imagepath 
		print 'templatefiles', templatefiles 
	  	return default_path, imagepath, avi_inpath, avi_outpath, templatefiles

#+++++++++++++++ End getPaths+++++++++++++++++++++++++++++++++++++++++++++++++
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
	avi_inpath = default_drivepath+"avi_in\\"
	avi_outpath = default_drivepath+"avi_out\\"

print default_path, templatefiles,imagepath, avi_inpath, avi_outpath 

print avi_inpath
#os.chdir(avi_inpath) does not work anymore!!!!!!!!!
d1 = os.getcwd()  
print d1
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def getParameters(ImgWidth, ImgHt):   
	gd = GenericDialog("Parameters")   
	#gd.addMessage("")
	gd.addNumericField("Image Width", ImgWidth, 0)  # show no decimals
	gd.addNumericField("Image Height", ImgHt, 0)  
	gd.addNumericField("Standard PSI width of normalized PSI profile", stdWidth, 0)  # show 2 decimals   
	#gd.addCheckbox("", True)   
	gd.showDialog()   
 	if gd.wasCanceled():   
		print "User canceled dialog!"
		sys.exit() 
	ImgWidth = gd.getNextNumber()
	ImgHt = gd.getNextNumber()	   
  	print ImgWidth, ImgHt 
	return ImgWidth, ImgHt
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#Check or set parameters
gp = getParameters(ImgWidth, ImgHt)
HB = ImgHt + B1
ImgWidth, ImgHt =gp

#CHOOSE THE AVI FILE NOW SO CAN GET PROPER CENTERS FILE.
#avi_file = OpenDialog("Choose the AVI file to fix", None)
od = OpenDialog("Choose the avi file",avi_outpath, None)   
filename = od.getFileName() 
if filename is None:   
	print "User canceled the dialog.Exiting!"  
	sys.exit()
else:   
	directory = od.getDirectory()   
	avi_file = directory + filename   
	print "Selected file path:", avi_file   
	(file_name, file_ext) = os.path.splitext(filename) 

#Excel stores numbers in a csv file without quotes, with a comma as separator
#the QUOTE_NUMERIC parameter converts to a float value internal to reader
#using 'with' is apparently safer code for cleanup on exceptions
Centersf = avi_outpath+"Cntrs_"+file_name+".csv"
f = open(Centersf,'r') #python 2.5
rdr = csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)
#slices, FramePos, raw, pcc, pn, pw, pcn, pnw, pma, flc = zip(*rdr) 
slices, FramePos,pma, flc = zip(*rdr) 
# above a bit esoteric-> "*rdr" unpacks the elements of each line; zip takes tuple of each row such that successive 
#elements of each row are now tuples. The tuples can be accessed as lists by zip(*array)[column #, e.g. 0]
f.close()
# FramePos = from pcn is PSI predicted center based on n+1 and n-1 PSI width for n;
# pma =    moving average width based on moving average chunk of MovAvgRng, normally set to 1 s of film = 18 frames
# flc  =   frame luminance rgb correction value for entire frame;'
#print rdr # test check

HB = ImgHt + B1 	

FramePos = list(FramePos) #use the corrected PSI center values
pma = list(pma)      #use the moving average PSI widths
print FramePos

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WORK THE AVI IMAGES.
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
stack = AVI_Reader.openVirtual(avi_file) 
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

#Create a new virtual stack to hold modified images
stack4 = ij.VirtualStack(ImgWidth, ImgHt, None, imagepath)
#stack4ID = stack4.getID()

maxslices = int(AllSlices-nstart)
print 'AllSices', AllSlices,'maxslices', maxslices

#PROCESS IMAGES LOOP
#--------------------------------------------------------------------------------
# This is the start of the loop to run through all frames of the video sequence
#because the data is sorted we will just 
starttime = time.time()
count = 0
print 'starting frame:', nstart, 'stop frame:', nstop

#++++++++++++++++++++MAIN IMAGE PROCESSING LOOP++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#How many rows to adjust at one time via ROI:
RowsToAdjust = 2
lum_rel = [0]*(ImgHt)
#IJ.run("Set Measurements...", "mean standard min max stack redirect=None decimal=3")
#get statistics and histogram; getStatistics automatically makes histogram available.
#options = IS.MEAN | IS.MIN_MAX |IS.STD_DEV
#use the right region to find where the 
#stdROI =Roi(1810, 0, 80, 1080)
imp = ij.WindowManager.getImage(stack_ID) #focus on stack
ip=imp.getProcessor().duplicate() #gets processor from duplicate slice to check if RGB
pixnum = ip.getPixelCount()		
type = imp.getType()
if ImagePlus.COLOR_RGB != type:	print 'Stack does not contain RGB images' 
ImgWidth = stack.getWidth() 
ImgHt = stack.getHeight()

#get an RoiManager instance
#rm = RoiManager(True)
#Process frames
for i in range(nstart,nstop): #nstart based on stack slice numbering, which is 1, not array numbering which is 0
	#make sure we get proper image from stack; a bit convoluted to isolate proper image from stack	
	#we do not call the slice number here, because that reference is to the original video file, and 
	#not the stack2 video file, where the center value directly corresponds to the index number. Thus, 
	#we simply call i to find the center or frame.
	slice = stack.setSlice(i)
	#The relationship of slice and stack is a bit confusing. regardless of slice called, the
	#id returned is always the stackID. Could not directly act on it, must duplicate. The good news is
	#that duplicate acts on the slice showing. 
	img = ij.WindowManager.getCurrentImage()
	IJ.run("Duplicate...", "title=[slice_"+str(i)+"]") #note how option set up for acceptable string
	ASlice = "slice_"+str(i)
	#print 'slice indx', indx, 'PSIWidth',NewWidth,'PSI Center:', PSICenter, 'zeroRow',zeroRow
	# the convention we use for adjusting the luminance range is that the PSI center is 
	# at zero, with maximum value PSIwidth/2 
	#gnerate the lum_rel array we will use.
	PSICenter = FramePos[i-1] # slice 1 has cneter at FramePos[0] ,not [1]
	for k in range(ImgHt):
		if PSICenter <=1080:
			lum_rel[k] = abs(k - PSICenter)
		elif PSICenter > 1080:
			x0 = abs(pma[i-1] - PSICenter) #x0 is the PSI position at frame row 0
			if (x0 + k) <= int(pma[i-1]/2): #if the index is less than 650, just keep increasing until 650 reached
				lum_rel[k] = x0 + k
			else: # if 650 reached start decrementing from 650
				lum_rel[k] = pma[i-1] - (x0 + k)

	imp = ij.WindowManager.getCurrentImage()
	ip=imp.getProcessor()
	for n in range(0, ImgHt-1,RowsToAdjust):
		#Eqns for calculating min and maximum luminance corrections
		NewMax = int(0.0796920*lum_rel[n] + 212.2) #SEE \imageJ Stuff\HBath_BadLands stack2_brightness-contrast analysis.xlsx
		NewMin = int(-0.05046*lum_rel[n] + 41.8) 
		#NewMax = int(0.0658*lum_rel[n] + 212.2) OLDER SET; GOOD, BUT MORE POSTIVE SIDE THEN ABOVE
		#NewMin = int(-0.0643*lum_rel[n] + 41.8) 
		if NewMax > 255: NewMax = 255
		if NewMin < 0: MewMin = 0	
		#AnRoi = Roi(lftPt, n, ImgWidth - 2*lftPt, RowsToAdjust)
		#rm.addRoi(AnRoi)
		#roi_list = rm.getRoisAsArray() # get the full list of Rois on the Roi stack
		#print 'roi_list', roi_list #roi_list to check if roi being properly replaced
		# Put the ROI on the ip
		#ip.setRoi(AnRoi)
		IJ.makeRectangle(lftPt, n, ImgWidth - 2*lftPt, RowsToAdjust)
		IJ.setMinAndMax(NewMin,NewMax)

	#result file of calc.
	corImg = ij.WindowManager.getCurrentImage()
	corImg.setTitle("out_"+str(i)+".png")
	out_image = imagepath+corImg.getTitle()
	FileSaver(corImg).saveAsPng(out_image) 
	stack4.addSlice(corImg.getTitle())
	corImg.close()
	count+=1

print 'frames done:',count-1
print 'stack4 size', stack4.getSize()
for list1 in range(1,count+1):
	print 'stack4 file name', stack4.getFileName(list1)

ImagePlus("stack4",stack4).show()
IJ.selectWindow("stack4")

IJ.run("Input/Output...", "jpeg=100 gif=-1 file=.txt use_file copy_row save_column save_row")
AVI_file_out = "stack4.avi"
avi_Out = avi_outpath+AVI_file_out
#no common program I have reads this, including irfanview, or vitualdub64,use jpeg compression.
#IJ.run("AVI... ", "compression=PNG frame=30 save=["+avi_Out+"]") 
IJ.run("AVI... ", "compression=JPEG frame=30 save=["+avi_Out+"]")
#ij.WindowManager.getCurrentWindow()
#IJ.resetMinAndMax()
stoptime = time.time()
print 'Elapsed time to process '+str(count-1)+" frames: "+ str((stoptime-starttime)/60)+' min.'
#for checking purposes set plot profile measuring orientation to verical and set an ROI
IJ.run("Profile Plot Options...", "width=450 height=200 minimum=0 maximum=0 vertical interpolate draw")
IJ.makeRectangle(lftPt, topPt, ImgWidth - 2*lftPt, ImgHt)

#Delete the file stream in the png dump directory

#AS NOTED IN MESSAGE, IF FILES DELETED, STACK5, A VIRTUAL STACK CANNOT BE DISPLAYED.
#removeimages = False
#gddelf = GenericDialog("Delete files?")
#gddelf.addMessage("Delete intermediate .png image files (recommended, but virtualstack stack5 will not be available for viewing, and will close)")
#gddelf.enableYesNoCancel("Delete", "Leave")
#gddelf.showDialog()
#if (gddelf.wasCanceled()):
#	print 'User canceled removal of png images from'+imagepath
#elif (gddelf.wasOKed()):
#	print 'User opted to delete images from '+imagepath
#	removeimages = True
#else:
#	print'User opted to not delete images from '+imagepath
#avipnglist = os.listdir(imagepath)
#print avipnglist
#if removeimages:
#	pattern = ".png"
#	for f in avipnglist:
#	for f in File(imagepath).listFiles():
#		if f.endswith(pattern):
#		if not os.path.isdir(f) and ".png" in f:
#			os.unlink(imagepath+f) #	File(str(f)).delete() # Notice str(f) is needed: Java types vs Python...
#	cw = ij.WindowManager.getCurrentWindow()
#	cw.close()

print "Done.File saved as: "+AVI_file_out
gdend = GenericDialog("Finished")
gdend.addMessage("Done.File saved as: "+AVI_file_out) 
gdend.showDialog()
sys.exit()

#Some old stuff that might be useful later...
#if indx == 4: sys.exit()
#selectWindow("stack3.avi");
#run("Duplicate...", "title=stack3-1.avi");
#//run("Brightness/Contrast...");
#selectWindow("stack3.avi");
#selectWindow("stack3-1.avi");
#setMinAndMax(21, 233);
#run("Apply LUT");
#// Copies the display range of the active image to all open images.
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
	

