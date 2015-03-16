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
import ij.measure
from ij.measure import Measurements
from ij.measure import ResultsTable
from math import sqrt
from jarray import zeros #jarray is a Jython module that implements only two methods, zeros and array
from operator import itemgetter
from java.io import File 
import java.io.File.__dict__ 
from mpicbg.imglib.image.display.imagej import ImageJFunctions as IJF
import ij.VirtualStack 
from ij.gui import NewImage
from ij.gui import Roi
from ij.plugin import AVI_Reader # added June, 2014 after upgrading to Imagej2, needed explicitly
#from numpy import * not allowed in Jython.
#SET ALL PARAMETERS HERE
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

#Excel stores numbers in a csv file without quotes, with a comma as separator
#the QUOTE_NUMERIC parameter converts to a float value internal to reader
#using 'with' is apparently safer code for cleanup on exceptions


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
	#Finaly get corresponding centers file, which PSI_avi_Processor v3.py places in /avi_out/
	Centersf = avi_outpath+"Cntrs_"+file_name+".csv"

f = open(Centersf,'r') #python 2.5
rdr = csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)
#slices, FramePos, raw, pcc, pn, pw, pcn, pnw, pma, flc = zip(*rdr) 
slices, FramePos,pma, flc = zip(*rdr) 
# above a bit esoteric-> "*rdr" unpacks the elements of each line; zip takes tuple of each row such that successive 
#elements of each row are now tuples. The tuples can be accessed as lists by zip(*array)[column #, e.g. 0]
f.close()
# slice =	frame #; 
# cn  = 	PSI center row; 
# raw =    pattern recog. center (no corrections);
# pcc =    maximmum Pearson Corr. Coeff. of found PSI center;
# pn  =    number of PSI between last and current frame (pn will be zero if slice interval >1);
# pw  =    PSI width/frame;
# pcn =    predicted center based on n+1 and n-1 PSI width for n;
# pnw =    new width between predicted in n+1 and n-1 for n;
# pma =    moving average width based on moving average chunk of MovAvgRng, normally set to 1 s of film = 18 frames
# flc  =   frame luminance rgb correction value for entire frame;'

print rdr

HB = ImgHt + B1 	

slices =list(slices)
FramePos = list(FramePos) #use the corrected PSI center values
pma = list(pma)      #use the moving average PSI widths
flc = list(flc)
print FramePos

def computeStdDev(pixels, mean): # not used
	#usage  stdDev = computeStdDev(ip.getPixels(), mean) this would do it for the entire image, but will not work for rgb image.
	for i in range(len(pixels)):
		s += pow(pixels[i] - mean, 2)
	return sqrt(s / float(len(pixels) -1))

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WORK THE AVI IMAGES.
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# with the help of Wayne Rasband on the listserver, this is the way 1.47 opens the
#avi stack for reading the slices etc
#BRING IN STACK2 (STARTING) AVI FILE
#AVI FILE WAS CHOSEN EARLIER...JUST OPEN IT
stack = AVI_Reader.openVirtual(avi_file) 
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
#WE WILL LIKELY HAVE A PROBLEM READING IN A BIG FILE. IT WILL STOP AT SOME FILE SIZE LESS THAN THE TOTAL NUMBER OF 
#FRAMES.http://imagej.1557.n6.nabble.com/Not-able-to-open-full-length-of-large-AVI-file-td4496180.html REPORTED THAT A
# 36 GB FILE W/ 191 8000X8000 PIXEL IMAGES WOULD ONLY LOAD 9 IN THE FILE EVEN IN VIRTUAL MODE. APPARENTY, AVI READER WILL ONLY OUTPUT 
# 2.2 GB FILES MAXIMUM AS OF FEB 2012. SO WE MAY HAVE TO WATCH MEMORY AND PULL IN RANGES
#CAN CHANGE ALLOCATED MEMORY IN EDIT\OPTIONS\MEMORY AND THREADS.. SHOWS 4.6GB IS AUTOMATICALLY ALLOCATED ON 6GB MACHINE. THAT IS LIMIT THEN
if nstop == -1: 
	AllSlices = stack.getStackSize()
	nstop = AllSlices - 1
else:
	AllSlices = nstop
print 'slices to process:', nstop
ImgWidth = stack.getWidth() 
ImgHt = stack.getHeight()

stack4 = ij.VirtualStack(ImgWidth, ImgHt, None, imagepath)
stack4ID = stack.getID()
#stack2 = ImageStack(ImgWidth, ImgHt) #this opens an image stack, but not a virtual stack, so only can work off available RAM
#Future reference. Virtual stack is read only, to manipulate it, duplicate it. Does not make sense. why have an addslice if true.

maxslices = int((AllSlices-nstart)/slicecutter)
print 'AllSices', AllSlices,'maxslices', maxslices

#convert FramePos to integers for later use
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

print 'starting frame:', nstart, 'stop frame:', nstop

#++++++++++++++++++++MAIN IMAGE PROCESSING LOOP++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#How many rows to adjust at one time via ROI:
RowsToAdjust = 2
IJ.run("Set Measurements...", "mean standard min max stack redirect=None decimal=3")
#Make sure we are following correct slice rahter than the index i

for i in range(nstart,nstop):
	ImgWidth = stack.getWidth() 
	ImgHt = stack.getHeight()
	#make sure we get proper image from stack; a bit convoluted to isolate proper image from stack	
	imp = ij.WindowManager.getImage(stack_ID) #focus on stack
	ip=imp.getProcessor().duplicate() #gets processor from duplicate slice to check if RGB
	pixnum = ip.getPixelCount()		
	type = imp.getType()
	if ImagePlus.COLOR_RGB != type:	print 'Stack does not contain RGB images' 
	indx = slices[i] # i may not be the same as slice number, be sure to ref index to get slice
	slice = stack.setSlice(indx) #indx taken directly from cvs first column
	#The relationship of slice and stack is a bit confusing. regardless of slice called, the
	#id returned is always the stackID. Could not directly act on it, must duplicate. The good news is
	#that duplicate acts on the slice showing. 
	IJ.run("Duplicate...", "title=[slice_"+str(indx)+"]") #note how option set up for acceptable string
	ASlice = "slice_"+str(indx)
	NewWidth = pma[i] 
	PSICenter = FramePos[i] 
	#check and fix negative centers; can happen 	
	if PSICenter < 0: PSICenter = NewWidth + PSICenter
	#get which PSI row is at frame row 0; multiple cases
	halfPSI = NewWidth/2
	if PSICenter > halfPSI: 
		zeroPSI = PSICenter - halfPSI #but this only takes us to zero for for PSI, not ZeroRow value
		zeroRow  = int(NewWidth- zeroPSI)
	else:
		zeroRow = int(halfPSI - PSICenter)

	#print 'slice indx', indx, 'PSIWidth',NewWidth,'PSI Center:', PSICenter, 'zeroRow',zeroRow
	for n in range(0, ImgHt-1,RowsToAdjust):
		#get the intercept and slope that describe rows unique RGB limits to change as fcn of position on PSI
		#could avoid if statement with second loop once at PSICenter Row
		ARow = zeroRow + n
		ARown = ARow
		#messy stuff
		if ARow > 2*NewWidth + halfPSI:  #e.g. between ~2601 and 3250 = 5/2*w (if PSI width = 1300)
			ARow = ARown - 2*NewWidth	 #read rows up from 0
		elif ARow > NewWidth + halfPSI: 		 #e.g. between 1951 and 2600
			ARow = 2*NewWidth - ARown 	 #read down from 650
		elif ARow > NewWidth: 			 #e.g between 1300 and 1950
			ARow = ARown - NewWidth  	 #read up from 0
		elif ARow > halfPSI: 			 #e.g. between 651 and 1300
			ARow = NewWidth - ARown 	 #read down from halfPSI; else read up using original z+n
		
		NewMax = int(-0.0820*ARow + 255) 
		NewMin = int(0.0795*ARow) 
		
		#NewMax = int(-0.0594*ARow + 244.86) 
		#NewMin = int(0.0588*ARow + 9.2688) 
		ip=imp.getProcessor()
		roi = Roi(lftPt, n, ImgWidth - 2*lftPt, RowsToAdjust)
		ip.setRoi(roi)
		if NewMax > 255: NewMax = 255
		if NewMin < 0: NewMin = 0
		#print 'zeroRow', zeroRow, 'zeroRow+n', zeroRow+n,'halfwidth', halfPSI,'ARow', ARow,'NewMin', NewMin, 'NewMax', NewMax
		#print "mean:", stats.mean, "min", stats.min,"max",stats.max, 'NewMin', NewMin, 'NewMax', NewMax
		#Apply to the row.
		#ip=imp.getProcessor()
		#roi = Roi(lftPt, n, ImgWidth - 2*lftPt, RowsToAdjust)
		#ip.setRoi(roi)
		IJ.makeRectangle(lftPt, n, ImgWidth - 2*lftPt, RowsToAdjust)
		IJ.setMinAndMax(NewMin,NewMax)
	#if indx == 4: sys.exit()
	#if i == 6: # slices are 0 to end -1 so 6 is slice 7
	#	sys.exit()	
		#result file of calc.
	corImg = ij.WindowManager.getCurrentImage()
	corImg.setTitle("out_"+str(indx)+".png")
		
	#imagestack can add a slice after a specifed slice. virtualstack cannot, but it reads file in a sequence. 
	#imp = ImagePlus(stack.getLabel(i), ip) 
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
#imp_template.close()	
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

