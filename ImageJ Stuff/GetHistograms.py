#Python code run under ImageJ to get histograms of a single ROI over slices/frames in avi.
# slices set in parameters section below imports
#WORKS AS OF 07/25/2014

#Requires centers file of form: Cntrs_avi_file_name.avi

#CODE IS BARE BONES AT THIS STAGE, BUT SHOWS HOW TO GET THE INFO 
# code is based on Fiji implementation, which uses Python 2.5 and ImageJ 1.49
#Fiji-ImageJ does not recognize latest Python 3.x print function change using
#paranthesis and does not allow numpy package, which would simply the matrix
#code substantially.

#THIS CAN BE SPED UP BY RUNNING FROM THE COMMAND LINE, BUT REQUIRES A REWRITE SO THAT
#ALL INPUT IS EITHER AUTOMAITC OR FROM THE COMMAND LINE. THE FOLLOWING COMMAND LINE EXAMPLE 
#MAY BE USEFUL, ONCE EVERYTHING IS CONVERTED. REALLY THE ONLY CONVERSION SHOULD BE THAT FOR EACH 
#COMMAND LINE RUN THE AVI FILE NAME NEEDS TO BE CHANGED.

#fiji-linux64 --headless --jython ./scripts/PSI_avi_Processor.py -batch &

#Requies: 
# 	A csv file of two connected mormalized PSI profiles  (2 x wavelength)
	# Default file name: "PSI_norm_1358.csv"
#AND several specific folders under a single drive or folder:
	#
"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
FIJI - IMAGEJ PYTHON CODE 
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

#SET ALL PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#SET ALL GLOBAL PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
slicecutter = 1		# slices to skip
nstart = 0 # starting frame to pick up only white leader frames PSIs 
nstop =  3 #-1 #10 # set to -1 means do all frames
RowsToMeasure = 2
TopRowOfROI = 300
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#CRITICAL INFO THAT MUST BE SUPPLIED FROM OTHER METHODS
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
stdWidth = 1358			# width of the normalized PSI
NewWidth = stdWidth
B1 = 1166.910722 #Blanking interval obtained from rotating camcorder info
ImgHt = 1080 #Image vertical height in rows - default
ImgWidth = 1920 #Image with in pixels/columns - default
#next four values used to create final rectangle, usually will mirror values used for finding centers in template script.
topPt =0 #60				# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240					# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020          # bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680 # rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
IBase=255

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
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

def getParameters(ImgWidth, ImgHt):   
	gd = GenericDialog("Parameters")   
	gd.addMessage("Width, height")
	gd.addNumericField("Image Width", ImgWidth, 0)  # show no decimals
	gd.addNumericField("Image Height", ImgHt, 0)  
	gd.showDialog()   
 	if gd.wasCanceled():   
		print "User canceled dialog!"
		sys.exit() 
 	ImgWidth = gd.getNextNumber()
	ImgHt = gd.getNextNumber()	   
  	print 'ImgWidth',ImgWidth, 'ImgHt',ImgHt 
	return ImgWidth, ImgHt

#Check or set parameters from window
gp = getParameters(ImgWidth, ImgHt)
ImgWidth, ImgHt =gp
HB = ImgHt + B1 #total video frame visual+blanking region

#Excel stores numbers in a csv file without quotes, with a comma as separator
#the QUOTE_NUMERIC parameter converts to a float value internal to reader
#using 'with' is apparently safer code for cleanup on exceptions
#but next line not available in jython 2.5?? gives error about new keyword in 2.6
#with open(default_path+PSIf) as f:
	#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
#	PSI = [x[0] for x in csv.reader(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 

#CHOOSE THE AVI FILE NOW SO CAN GET PROPER CENTERS FILE.
#avi_file = OpenDialog("Choose the AVI file to fix", None)
#CENTERS FILE MUST HAVE SAME NAME AS AVI INPUT FILE, BUT IS OF FILENAME Cntrs_AVI_FILE_NAM.AVI
#e.g., Cntrs_stack2.avi

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
	Centersf = avi_inpath+"Cntrs_"+file_name+".csv"

#override above for testing
#avi_file = avi_inpath+"Leader Tests 1.avi"
#Centersf = avi_inpath+"Cntrs_Leader Tests 1.csv"
print file_name

f = open(Centersf,'r') #python 2.5
rdr = csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)
slices, FramePos, raw, pcc, pn, pw, pcn, pnw, pma, flc = zip(*rdr) 
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

#pstream = [0]*(len(pw)+1)
#pstream[0] = pw[0]
#pwa = [0]*(len(pw)+1)
#convert the tuples to lists
slices =list(slices)
FramePos = list(pcn) #PSI corrected centers
pma = list(pma)
flc = list(flc)
print FramePos
PSIf = templatefiles+"PSI_norm_1358.csv"
#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
PSI = [x[0] for x in csv.reader(open(PSIf), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
print'rows:',len(PSI)
#print 'PSI',PSI

# IJ.setBatchMode(True)

def computeStdDev(pixels, mean):
	#usage  stdDev = computeStdDev(ip.getPixels(), mean) this would do it for the entire image, but will not work for rgb image.
	for i in range(len(pixels)):
		s += pow(pixels[i] - mean, 2)
	return sqrt(s / float(len(pixels) -1))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WORK THE AVI IMAGES.
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
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

#set up lists
PSICenter = [0]*(maxslices+1)
#convert FramePos to integers for later use
slices = [int(x) for x in slices]
FramePos = [int(x) for x in FramePos]

#PROCESS IMAGES LOOP
#-----------------------------------------------------------------------------------------
# This is the start of the loop to run through all frames of the video sequence
#because the data is sorted we will just 
starttime = time.time()
count = 0
OldPSICenter = -1 #a PSICenter may start at zero or greater.

print 'starting frame:', nstart, 'stop frame:', nstop

#++++++++++++++++++++MAIN IMAGE PROCESSING LOOP++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#How many rows to adjust at one time via ROI:

IJ.run("Set Measurements...", "mean standard min max stack redirect=None decimal=3")
histogram_list=[]
hdr=[]
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
	ij.WindowManager.getCurrentImage()
	#Get moving average width
	NewWidth = pma[i+1] #on stack2 slice 1 is actualy slice 2 of original csv file (n in stack2 = n+1 in original csv file.
	PSICenter = FramePos[i+1] #on stack2 slice 1 is actually slice 3 of original csv file
	#check and fix negative centers; can happen; flaw in centers code somewhere 	
	if PSICenter < 0: PSICenter = NewWidth + PSICenter
	#get which PSI row is at frame row 0; multiple cases
	print 'slice indx', indx, 'PSIWidth',NewWidth,'PSI Center:', PSICenter
	ip=imp.getProcessor()
	roi = Roi(lftPt,TopRowOfROI, ImgWidth - 2*lftPt, RowsToMeasure)
	ip.setRoi(roi)
	#get statistics and histogram; getStatistics automatically makes histogram available.
	options = IS.MEAN | IS.MIN_MAX |IS.STD_DEV
	stats = IS.getStatistics(ip,options, imp.getCalibration()) 
	print "mean:", stats.mean, "median:", stats.median, "area:", stats.area,  "max",stats.max,"min", stats.min # area is always available
	#Next two lines get roi histogram of slice
	hm = ip.getHistogram()
	#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	#example of hm processing to get fractions rahter than absolute values
	#print hm
	#otalhm = sum(hm)
	#summinhm = 0
	#summaxhm = 0
	#nn = 0
	#nhigh = totalhm
	#sum the fraction and get 0.1 fraction indes and 0.9 fraction index
	#while summinhm >= 0.10:
	#	summinhm = summinhm + hm[nn]/totalhm
	#	nn = nn + 1
	#	nlow = nn
	#nn = totalhm
	#while summaxhm <= 0.10:
	#	summaxhm = summaxhm + hm[nn]/totalhm
	#	nn = nn -1
	#nhigh = nn
	#if NewMax > 255: NewMax = 255
	#if NewMin < 0: NewMin = 0
	#print 'zeroRow', zeroRow, 'zeroRow+n', zeroRow+n,'halfwidth', halfPSI,'ARow', ARow,'NewMin', NewMin, 'NewMax', NewMax
	#IJ.makeRectangle(lftPt, n, ImgWidth - 2*lftPt, RowsToMeasure)
	#IJ.setMinAndMax(NewMin,NewMax)
	#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	histogram_row = int(TopRowOfROI+round(RowsToMeasure/2.0,0)) #get nearest rounded row as average of ROI.
	hdr.append("s"+str(i)+"r"+str(histogram_row))
	histogram_list.append(hm)
	CurrentImage = ij.WindowManager.getCurrentImage()
	CurrentImage.close()
	count+=1
		
histograms = zip(*histogram_list) #turn rows to columns for typical output.
histograms.insert(0,hdr)
outf = "histograms_"+file_name+".csv"
histogram_path = avi_outpath+outf
f = open(histogram_path,'w') 
fout = csv.writer(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n' ) 
for h in histograms:
	fout.writerow(h)# note brackets around p - a separate list now

f.close()
stoptime = time.time()
print 'Elapsed time to process '+str(count-1)+" frames: "+ str((stoptime-starttime)/60)+' min.'
#for checking purposes set plot profile measuring orientation to verical and set an ROI
IJ.run("Profile Plot Options...", "width=450 height=200 minimum=0 maximum=0 vertical interpolate draw")
IJ.makeRectangle(lftPt, topPt, ImgWidth - 2*lftPt, ImgHt)

print "Done"
gdend = GenericDialog("Finished")
gdend.addMessage("Done.File saved as: "+histogram_path) 
gdend.showDialog()
sys.exit()
