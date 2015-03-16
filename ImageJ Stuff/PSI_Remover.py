#Python code run under ImageJ to remove the Projector Shutter Image (PSI)from each image
# in an uncompressed avi file.
#inputs required:
#	A background corrected avi file, usually generated from VirtualDub, targeted to remove the PSI. 
#	A corresponding PSI centers file generated from [PSI_avi_Difference_Template_Processor2.py] 
#   for the avi file with name Cntrs_avifilename.csv.
#	The PSI profile csv file [PSI_norm_1358.csv] in /templating_files/
#	A luminance correction file, lumcorr.csv in /templating_files/ generated from [F:\Canon\PSI 
#   and Lumnance Curves via Solver.xlsm] 

#OUTPUT:
#  stack2.AVI in folder /avi_out/

# Code is based on Fiji implementation, which uses Python 2.5 and ImageJ 1.49
#Fiji-ImageJ does not recognize latest Python 3.x print function change using
#paranthesis and does not allow numpy package, which would simply the matrix
#code substantially.

#Currently, the individual image files that make up the avi are not destroyed. They are in 
# Canon/imagedump. They should be removed before the averaging script is started.
"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
FIJI - IMAGEJ PYTHON CODE 
STREAMLINE METHOD - IGNORE DISTORTION
This process ignores the known distortion that is observed in the video frames and compares the 
image sub section against the base or normalized PSI at the specified interval rows. 
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
A critcal tutorial for Fiji/ImageJ and Python is:http://www.ini.uzh.ch/~acardona/fiji-tutorial/#s2
The file explaining this fle and all other opreations is: 
"""
from ij import IJ, ImagePlus, ImageStack
import ij.io
import ij.gui 
import math
import csv
import operator
import os
from math import sqrt
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
#from numpy import * not allowed in Jython
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#SET ALL PARAMETERS HERE
#SET ALL GLOBAL PARAMETERS HERE
nstart = 1 # starting frame to pick up only white leader frames PSIs 
nstop = -1 # set to -1 means do all frames
DoSmoothing = True #Setting to True invokes the 3x3 pixel smooting to reduce noise in altered PSI pixels areas.
lock_PSI_width = 2 #Values are: 0 use stdwidth; 1 - lock to overall average of pma widths; 2 use moving average frame width; 3 - lock to user chosen width
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#NOTE THAT IN THIS SPECIFIC CASE RIGHT NOW WE ARE SKIPPING FIRST FRAME BECAUSE IT 
#IS NOT A VALID MOVIE FRAME, JUST A HEADER TO INDICATE 100s
#change the range from 2 back to 1 for real data.
#++++++++++++++++++++++++++++++++++++++++
#CRITICAL INFO THAT MUST BE SUPPLIED FROM OTHER METHODS
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
stdWidth = 1358		# width of the normalized PSI
UserWidth = 1358	# user chosen override width; use lock_PSI_width = 3
AverWidth = 1358
NewWidth = stdWidth
B1 = 1166.910722 #Blanking interval obtained from rotating camcorder info
ImgHt = 1080
ImgWidth = 1920
#next four values used to create final rectangle, usually will mirror values used for finding centers in template script.
topPt =0 #60				# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240					# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020          # bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680 				# rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
IBase=255
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#FOR,PRODUCTION RUNS WILL,NEED TO IMPLEMENT OPENDIALOG, SAVEDIALOG AND PROBABLY GENERICDIALOG METHODS
#SEE http://www.ini.uzh.ch/~acardona/fiji-tutorial/#generic-dialog FOR STARTER IDEAS.

# set working drive and main folder if needed
DriveOption = "F" #either C, F, G, X is for dialogues to choose diectories

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

def GetTemplate(PCntr,NewW,stdW,P,pcase):
	#NewW can vary depending on choices for width;
	#P is already either a PSI of stdWidth, or a vector of size NewW, ajdusted to proper row center.
	template=[]
	PSIy = []
	#NewW will be 0 on first frame, so need to compensate for this
	if NewW == 0:
		NewW = stdW
	#To compensate for inevitable frequency shift, calculate a bigger range than necessary
	#by 25% i.e.,1350 instead of 1080.
	#More detailed explanation on template building can be found in PSI_avi_Leader_Template_Processor.py
	#The values in the PSIy array are cut in at intervals of total row range/interval over the extra range (1320)
	#There will be a problem if newwidth > old width, so first expand PSI by expanding sPSI, if needed.
	#print 'PCntr:',PCntr,'NewW:',NewW,'P len:', len(P)
	xNewSize = int(round(NewW)) 	 #number of integer bins to generate; will be => stdW
	if NewW != stdW: #create a PSI vector with the new width and interpolate old values on new width.
		#----------PSI HISTOGRAM INTERPOLATOR-----------------------------------------------------------------------
		from bisect import bisect_left
		from bisect import bisect_right
		#Set up new x intervals and fractions between rows lists; this is done by
		#multiplying the PSI and row arrays by a fraction of old/new or new/old.
		#We do not necessarily have to multiply PSI values by a factor; doing this assumes
		#the integrated amount of total light in the PSI envelope must remain the same as in a
		#histogram of constant units (photons in our case). If we do not do this, it is equivalent 
		#to saying that the photons yield is independent of PSI width and photon yield.
		#However, in any case the correction is no more than about 10%.
		xfactor = float(NewW)/float(stdW) #must convert int-> float or produces only 0
		yfactor = float(stdW)/float(NewW)  #from system dynamics new PSI values must be > on a compressed scale.
		#yfactor = 1 if photon collection not a constant
		#generate new x integer array to interpolate against fractional x list		
		if NewW > stdW:
			xstdrows = [x for x in range(NewW)] #gen. integer list against the new PSI width
		else:
			xstdrows = [x for x in range(stdW)] #gen. integer list against the std PSI width
		#set up the unnormalized fractional vector based on 1358 fractions
		PSIfrac = [0]*len(xstdrows)
		PSIfrac = [y*yfactor for y in P]
		x_frac_new = [0]*len(xstdrows)
		x_frac_new = [x*xfactor for x in xstdrows]
		#print 'PSI length', len(P)
		for i in range(xNewSize-1):
 	    #find the new x values that bracket the integer value of the integer x range
 	    #use python's bisect fcns 
			if i > 0:
				x1 = bisect_left(x_frac_new,xstdrows[i]) -1 #get value just to left of bisect point
			else:
				x1 = bisect_left(x_frac_new,xstdrows[i])
			x2 = bisect_right(x_frac_new,xstdrows[i]) #get index on x_new just greater than our x_new integer
			y1 = PSIfrac[x1]
			y2 = PSIfrac[x2]
			#interpolate the x value to find the new PSI value at the new x integer value
			PSIIntX = y1 + (xstdrows[i]-x_frac_new[x1])*(y2-y1)/(x_frac_new[x2]-x_frac_new[x1])
			PSIy.append(PSIIntX) #add the y value to the new PSI vector
			PSIy = PSIy[:xNewSize]
			#-----------END PSI INTERPOLATOR----------------------------------------------------------------------
	else: # if PSI is only case left, do not need to change width
		PSIy = P[:xNewSize]
	template = PSIy
		#take out all but 1080 rows
	#renomalize the fractions template to 0-1 based on template minmax.
	tmin = min(template)	
	tminmax = max(template) - tmin
	for i in range(len(template)):
		template[i] = (template[i]-tmin)/tminmax
	# cut template so it is proper imgHt size 
	del template[ImgHt+1:len(template)]
	return template
#----------------END TEMPLATE GENERATOR FUNCTION---------------------------------------

#+++++++++++++++ Start getPaths+++++++++++++++++++++++++++++++++++++++++++++++++
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

#get path to standard PSI profile and rgb correction values.
corrf = templatefiles+"LumCorr.csv"
#PSIf = templatefiles+"PSI_normn_1358.csv"
PSIf =  templatefiles+"PSI_fraction_1358.csv"

print default_path, templatefiles,imagepath, avi_inpath, avi_outpath 
#+++++++++++++++ End getPaths+++++++++++++++++++++++++++++++++++++++++++++++++
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

#Excel stores numbers in a csv file without quotes, with a comma as separator.
#The QUOTE_NUMERIC parameter converts to a float value internal to reader
#using 'with' is apparently safer code for cleanup on exceptions

#with open(default_path+corrf,'r') as f: (for python >2.5)
#lumcorr is a list of 256 fractional values used to attempt to correct each pixels color balance
#after the PSI is removed.
f = open(corrf,'r') #python 2.5
lumcorr = [x[0] for x in csv.reader(open(corrf), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
print 'Lum Corr size', len(lumcorr)
lumcorr = list(lumcorr)

#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
PSI = [x[0] for x in csv.reader(open(PSIf), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
print'rows:',len(PSI)
#print 'PSI',PSI

Centersf = avi_inpath+"Cntrs_"+file_name+".csv"
f = open(Centersf,'r') #python 2.5
rdr = csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)
slices, FramePos, raw, pcc, pn, pw, pcn, pnw, pma, flc = zip(*rdr) 
#"*rdr" unpacks the elements of each line; zip takes tuple of each row such that successive 
#elements of each row are now tuples. The tuples can be accessed as lists by zip(*array)[column #, e.g. 0]
f.close()
#  slices =	frame #;' 
#  cn  = 	PSI center row;' 
#  raw =    pattern recog. center (no corrections);'
#  pcc =    maximmum Pearson Corr. Coeff. of found PSI center;'
#  pn  =    number of PSI between last and current frame (pn will be zero if slice interval >1);'
#  pw  =    PSI width/frame;'
#  pcn =    predicted next center based on n+1 and n-1 for n width differences;' 
#  pnw =    new width between predicted in n+1 and n-1 for n;'
#  pma =    moving average width based on moving average chunk of ' + str(MovAvgRng) + ';'
#  flc  =   frame luminance rgb correction value for entire frame;'

#print rdr # test check

HB = ImgHt + B1 	

FramePos = list(FramePos) #use the corrected PSI center values
pma = list(pma)      #use the moving average PSI widths
#print FramePos

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++			
def AdjustROIPixels(pixels,yc,xo, pW, relfrac, lumcorr,pc,pm):
	#subroutine that removes PSI shadow (using relfrac) and rebalances the r,g, or b channel pixels of the image.
	#this is where processing time is longest, because it changes every pixel in the image.
	#needs to be compiled.
	#the range runs from xo and yo to xo + pwth - po
	#we have to start at xo and jump when we reach pwth-po to xo+ 1080-(pwith_xo)
	for k in range(xo,xo+pW):
		px = pixels[k] #this is the actual r, g, or b pixel value,not the average
		if px < 0: px = 256 + px # convert -128- -1 sequence to positive 127-255 px is already negative.
		#we base the luminance correction on the mean pixel value that is already associated with the lumcorr index
		paver = int(pm[k]*255) # this is the mean r,g,b average of the pixel k based on float processor, 0-1 value
		#the mean pixel value as target is given by the lum fraction (lumcorr) we found by experiment and trial 
		#and error = lumcorr[paver]*float(px)
		#See F:\Canon\ImageJ Stuff\PixelAdjuster_Analysls.xlsx for how lumcorr.csv data derived.
		pn = lumcorr[paver]*float(px) # this is the required addition to the pixel based on the factor.
		if px > 0:
			ptest = px
			px = int(float(px) + (relfrac)*pn) 
		else:
			px = 0
		if px > 255: px = 255
		if px < 0: px = 0
		if px > 127: px = px - 256
		pixels[k] = px 
	if yc == pc:
	  if 0 < pc < 1080:
	  	for k in range(xo-240,xo-40):
			pixels[k]= 0
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++	
def smoother(smooth_cycles,ixp):
	#Find the stages in the data.
	#noise develops in corrections due to large multiplier, so reduce noise by smoothing in std 3x3 in 
 	if smooth_cycles > 0:
 		for i in range(smooth_cycles):
 			IJ.run(ixp, "Smooth", "")  #may need to use impage process ip
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++				
# WORK THE AVI IMAGES.
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++	
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
stack2 = ij.VirtualStack(ImgWidth, ImgHt, None, imagepath)
#stack2ID = stack2.getID()  for testing

maxslices = int(AllSlices-nstart)
print 'AllSices', AllSlices,'maxslices', maxslices

#PROCESS IMAGES LOOP
#--------------------------------------------------------------------------------
# This is the start of the loop to run through all frames of the video sequence
starttime = time.time()
count = 0
print 'starting frame:', nstart, 'stop frame:', nstop

#++++++++++++++++++++MAIN IMAGE PROCESSING LOOP++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#How many rows to adjust at one time via ROI:
RowsToAdjust = 2
lum_rel = [0]*(ImgHt)
lum_index = [0]*(ImgHt)
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

#how to get an RoiManager instance
#rm = RoiManager(True)
OldWidth = stdWidth
OldPSICenter = -1 #a PSICenter may start at zero or greater.
pcase = 3
#What width will we use
if lock_PSI_width == 0:
	NewWidth = stdWidth
elif lock_PSI_width == 1:
	AverWidth = sum(pma)/len(pma)
	NewWidth = AverWidth
elif lock_PSI_width == 3:
	NewWidth = UserWidth
else:
	pass
#Process frames
for i in range(nstart+1,nstop): #nstart based on stack slice numbering, which is 1, not array numbering which is 0
	indx = slices[i-2] #indx will show 2, but should really be 1.
	#confusing: for some reason, the first value listed in the centers file starts with the i+1 slice,
	#the value for the first slice is missing in the center list. The index value in col 1 of 
	#the centers file is the true value. Thus, we need to start the loop here on the original avi file at frame 2
	#and the corresponding center is at FramePos[0]. Thus, orig. slice i has FramePos[i-2] under constraint
	#nstart >= 2. The output final file will have a different index though. When we compare the original and the 
	#filtered PSI file. stack2 slice 1 is equivalent to orginal avi slice 2, or in general orig[i+1] = stack2[i].
	
	if lock_PSI_width == 2:
		NewWidth = pma[i-2] # i-1 because slice 1 is actually index 0 for pma, center etc.	
	#Although pcn predicts value,stick with FramePos, errors on this seem to be less than predicted value, once
	#the problem of < 400 is considered.
	PSICenter = FramePos[i-2]
	print 'slice:', 'i', i, 'PSICenter=',PSICenter, 'NewWidth', NewWidth
		
	#Grab the PSI fraction list starting at the known center column
	#The section of PSI to grab depends on how the PSI profile file PSI_norm_1358.csv is arranged. 
	#By convention, index 0 of the PSI csv file starts at the PSI peak minimum (peak center). 
	#PSI_avi_Differencer_Template_Processor2.py "moves" this profile "backward" until a fit is found. The PSI 
	#center is the difference between starting row (0) and number of steps (row interval jumps) to the best 
	#corr. coef. fit. To get the profile for a frame, the next std PSI profile center situated stdWidth rows
	#away is subtracted from the frame PSICenter position; this provides the starting row of the sub profile we need.
	#print 'slice:', indx, 'PSICenter=',PSICenter,'OldPSICenter=', OldPSICenter, 'NewWidth',NewWidth
	# we will not worry about rare to non existant case of PSICenter = OldPSICenter:
	sPSI = PSI
	#create a corresponding 2x width PSI index list
	PSIstdW_Index = [x for x in range(stdWidth)]
	PSIstdW_Index.extend(PSIstdW_Index)
	#generate a profile list or vector with row at approprate PSI center
	if NewWidth > stdWidth:
		sPSI.extend(PSI[0:(NewWidth-stdWidth+1)])
 		#gen. integer list against NewWidth
		PSIstdW_Index.extend(PSIstdW_Index[0:(NewWidth-stdWidth+1)])
		Poffset = NewWidth - PSICenter
		sPSI = PSI[Poffset:(int(Poffset+NewWidth))]
	else:
		Poffset = stdWidth - PSICenter
		sPSI = PSI[int(Poffset):(int(Poffset+stdWidth))] 

	#generate a list showing PSI index width for shifted PSI profile.
	#redefine Poffset so relative to NewWidth
	Poffset = NewWidth - PSICenter
	Idx = list(range(int(NewWidth/2), NewWidth))
	Idx.extend(range(0,NewWidth))
	Idx.extend(range(0,NewWidth))
	print Poffset
	PSI_Indexer = Idx[int(Poffset):(int(Poffset+NewWidth))]
	print 'len(PSI_Indexer)', len(PSI_Indexer)
	# get only the image height truncated list.
	del PSI_Indexer[ImgHt + 1:len(PSI_Indexer)]
	print 'len(PSI_Indexer)', len(PSI_Indexer)

	# Now have full pma or stdWidth PSI fraction and corresponding index lists
	#must now interpolate values to the size of he new PSI width.
	#PSI_indexer is not changed to NewWidth index and still retains integers based on stdWidth.
	#as long as don't use the integers except for debugging, its okay.
	#print 'PSICenter',PSICenter, 'Poffset', Poffset, len(sPSI), 'max PSI range', Poffset+stdWidth
	# PSI still 2*PSI cylces and starts at the std PSI in csv file until this point
	#sPSI will be variable in length, but can be no less than stdWidth 
		
	#From sPSI, the vector (list) with std width and PSIcenter locked to final position get:
	#1. new width or new center - requires PSI interpolation of fractions
	#2. oldwidth and same center - no changes to the sub PSI are needed at all
	#Case 1
	if (NewWidth != OldWidth) or (PSICenter != OldPSICenter): #may need interpolation to new width and luminance corr.
		pcase = 1
		#get the new PSI profile vector already set for proper center position,normalize and cut to img height.
  		tPSI = GetTemplate(PSICenter,NewWidth,stdWidth,sPSI,pcase) #returns a 1 x 1080 PSI profile list
	#we know have a list of normalized fractions on the new width with the max at the proper center.
	#test if working; note that index will be based on original PSIwidth and not NewWith range

	#make sure we get proper image from stack; a bit convoluted to isolate proper image from stack	
	#we do not call the slice number here, because that reference is to the original video file, and 
	#not the stack2 video file, where the center value directly corresponds to the index number. Thus, 
	#we simply call i to find the center or frame.
	slice = stack.setSlice(i)

	#The relationship of slice and stack is a bit confusing. regardless of slice called, the
	#id returned is always the stackID. Could not directly act on it, must duplicate. The good news is
	#that duplicate acts on the slice showing. 
	imp = ij.WindowManager.getCurrentImage()
	
	IJ.run("Duplicate...", "title=[slice_"+str(i)+"]") #note how option set up for acceptable string
	ASlice = "slice_"+str(i)
	
	#print 'slice indx', indx, 'PSIWidth',NewWidth,'PSI Center:', PSICenter, 'zeroRow',zeroRow
	# the convention we use for adjusting the luminance range is that the PSI center is 
	# at zero, with maximum value PSIwidth/2 
	#gnerate the lum_rel array we will use.
	#adjust every pixel before doing luminance range correction.
	#these are always considered color images so must split channels of byte value	
	
	ip = imp.getProcessor()
	length = imp.width*imp.height
	#AnRoi = Roi(240, 0, 1440, 1080)
	r = zeros(length, 'b')
	g = zeros(length, 'b')
	b = zeros(length, 'b')
	ip.getRGB(r,g,b) #eequivalent to ip.getPixels for B/W
	pb = ip.getBrightness() #returns a float processor, but this is not an array of pixels..
	pmean = pb.getPixels() #this gets the pixel array as a float fraction array from 0 (0 binary) to 1 (255)
	#The average pixel is then 255*ptest[x]
	#for i in range(100):
	#	print ptest[i]

	pmaHalf = int(pma[i-2]/2)
	#deal with center located within or without 1080 frame size 
	print 'PSICenter', PSICenter
	if PSICenter <= imp.height:
		PSIc = PSICenter			
	else:
		PSIc = PSICenter - pma[i-2]
	
	#lum_rel is the relative row position of a row measured from the PSI peak with 0 at the left 
	#base point	
	#there are two cases, and two sub cases. First case is whether PSI Center beyond 1080, and 
	#second what occurs first, a PSI min. or PSI max. (PSI center)
	#We need to know the fraction of PSI represented by the current row. This depends on
	#the postion of the PSI Center. 					
	# this below will fail if pma < 1080
	if pma[i-2] < 1080:
		print "A PSI width is less than 1080, cannot obtain correct PSI luminance fraction...ABORTING"
		sys.exit()
	
	for y in range(imp.height):
		xo = y*imp.width + lftPt
		relfrac = tPSI[y]
		AdjustROIPixels(r, y, xo, 1440, relfrac, lumcorr,PSICenter, pmean)
		AdjustROIPixels(g, y, xo, 1440, relfrac, lumcorr,PSICenter,pmean)
		AdjustROIPixels(b, y, xo, 1440, relfrac, lumcorr,PSICenter,pmean)

	# for checking indexes
	#if 400 < PSICenter < 600:
	#	for k in range(imp.height):
	#		print 'row', k, 'lum_rel', lum_rel[k], 'pma/2', pma[i]/2, 'frac', 1- 2*(lum_rel[k]/pma[i])	
	#	sys.exit()

	ip.setRGB(r, g, b)
	#result file of calc.
	corImg = ImagePlus("out_"+str(i)+".png", ip).show()	
	imp = ij.WindowManager.getCurrentImage()
# ++++++++++ SMOOTHING OPERATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++	
# The reverse process, which first smoothed the original, then applied the luminance correction via
# PSI_remover_smoothfirst.py showed virtually the same result.
	if DoSmoothing:
		max_smooth = 5
		#Best to use only those value leading to exact fractions, e.g.
		# m must be 2, 4, 5, 8, 10, 16, 20, 25, 40, 50, 250, 400
		# this corresponsds to intervals 2,4,5 8,10
		# fc will contain fractional range of PSI for different smoothing cycles
		#the most smoothing must be done on the range around PSICenter
		# the loop size is determined by how may possible intervals can be fit over the row height of the image
		fc = [(n*1/float(max_smooth)) for n in range(round((imp.height*max_smooth/pmaHalf))+2)]
		#The generated fc values are for end of the intervals; we need interval mid values
		midrange= (fc[1]-fc[0])/2
		for n in range(1,len(fc)):
			fc[n] = fc[n] - midrange
		PSI_index_array = []
		PSI_low_index_array = []
		PSI_high_index_array = []
		smooth_level_array = []
		smooth_array = range(max_smooth+1)
		smooth_array.reverse() #for 3.x convert to a list() after generation
		tmp2 = [-i for i in range(1,max_smooth)]
		smooth_array.extend(tmp2)
		# we already know the PSICenter postion on a normal 0-NewWidth or img.height scale
		# work from the center out to find row indexes to use for smoothing based on developed fractions
		for n in range(1,len(fc)):
			# deal with PSI left of PSI center (low # rows)
			a_test = int(PSICenter - pmaHalf*fc[n])
			if 0 < a_test < 1079:
				PSI_low_index_array.append(a_test)
			else:
			# deal with PSI_right of PSI center
				a_test = int(PSICenter + pmaHalf*fc[n])
				if 0 < a_test < 1079:
					PSI_high_index_array.append(a_test)
		if len(PSI_low_index_array) == 0:
			PSI_low_index_array.append(0)		
		#if high side has no values make at least one so can catentate later	
		if len(PSI_high_index_array) == 0:
			PSI_high_index_array.append(1079)	
		#join the low and high index arrays; first reverse low index array so center left row pos. is last
		PSI_low_index_array.reverse() # because started from center; we want min left side to center
		#join low and high array ranges
		if len(PSI_low_index_array) > 0:
			PSI_index_array.extend(PSI_low_index_array)
			PSI_index_array.extend(PSI_high_index_array)
		# Now set the corresponding smoothing_level (# of smoothing iterations); values correspond to fi
		smooth_low_array = smooth_array[:(len(PSI_low_index_array))]
		smooth_low_array.reverse()
		smooth_level_array.extend(smooth_low_array)
		smooth_level_array.extend(smooth_array[1:len(PSI_high_index_array)])
		#Need to deal with image height min and max rows, e.g.,0 & 1079 
		if PSI_index_array[0] != 0: 
			PSI_index_array.insert(0,0)
			if smooth_level_array[0] > smooth_level_array[1]:
				smooth_level_array.insert(0, smooth_level_array[0]+1)
			else:
				smooth_level_array.insert(0, smooth_level_array[0]-1)
			if smooth_level_array[0] > max_smooth: smooth_level_array[0]= smooth_level_array[0]-2
		if PSI_index_array[len(PSI_index_array)-1] != 1079: 
			PSI_index_array.append(1079)
			if smooth_level_array[len(smooth_level_array)-1] > smooth_level_array[len(smooth_level_array)-2]:
				smooth_level_array.append(smooth_level_array[len(smooth_level_array)-1]+1)
			else:
				smooth_level_array.append(smooth_level_array[len(smooth_level_array)-1]-1)
			if smooth_level_array[len(smooth_level_array)-1] > max_smooth:
				smooth_level_array[len(smooth_level_array)-1] = smooth_level_array[len(smooth_level_array)-1]-2
		#may be negative smoothing levels, change them
		for n in range(len(smooth_level_array)): 
			if smooth_level_array[n] < 0: smooth_level_array[n] = -smooth_level_array[n]			
		# for testing purposes
		#print 'smooth_array', smooth_array
		print 'PSI_low_index_array',PSI_low_index_array
		print 'PSI_high_index_array',PSI_high_index_array
		#print 'smooth_level_array',smooth_level_array
		print 'PSI_index_array',PSI_index_array 

		#finally smooth the regions according to a linear model
		for n in range(len(PSI_index_array)-1): # will not smooth last set
			IJ.makeRectangle(lftPt,PSI_index_array[n], ImgWidth - 2*lftPt, PSI_index_array[n+1]-PSI_index_array[n]-1)
			smoother(smooth_level_array[n],imp)
#++++++++++END OF SMOOTHING OPERATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++			

	corImg = ij.WindowManager.getCurrentImage()
	out_image = imagepath+corImg.getTitle()
	FileSaver(corImg).saveAsPng(out_image) 
	stack2.addSlice(corImg.getTitle())
	corImg.close()
	IJ.selectWindow(ASlice)
	ax=ij.WindowManager.getCurrentWindow()
	#problem develops with timing; not sure what is going on, but images
	 #sometimes get screwed up and results in i2 not being the template.	
	try :
		ax.close()
	except AttributeError, err1: 
		time.sleep(0.200)
		ax=ij.WindowManager.getCurrentWindow()
		ax.close()
	count+=1

print 'frames done:',count-1
print 'stack2 size', stack2.getSize()
for list1 in range(1,count+1):
	print 'stack2 file name', stack2.getFileName(list1)

ImagePlus("stack2",stack2).show()
IJ.selectWindow("stack2")

IJ.run("Input/Output...", "jpeg=100 gif=-1 file=.txt use_file copy_row save_column save_row")
AVI_file_out = "stack2.avi"
avi_Out = avi_outpath+AVI_file_out
#no common program I have reads the PNG version below, including irfanview, or vitualdub64,use jpeg compression.
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
	

