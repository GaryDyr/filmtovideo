#Python code run under ImageJ to remove the projector shutter Image (PSI) on 
#video frames in an AVI movie sequence. 

#THIS VERSION DOES NOT CORRECT WELL FOR THE REDUCED CONTRAST FOUND AFTER REMOVING THE PSI.
#ITS MAIN REASON FOR STILL EXISTING IS HISTORICAL AS THE BASIS FOR MOST INITIAL ATTEMPTS TO REMOVE
#THE PSI. THUS, IT REPRESENTS AN IMPORTANT HISTORICAL STEP TO THE FINAL SCRIPT.

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
	avi_inpath = default_drivepath+"avi_in\\"
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
PSILightFactor =  0.928 #0.40
ImgHt = 1080
ImgWidth = 1920
#csize = ImgHt + int(0.25*float(ImgHt)) # variable used to expand row size when PSI width > stdWidth
CorrectLuminance = True # If true, use PSI profile corrected for luminace, normally set to True

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
#	PSI = [x[0] for x in csv.reader(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 

print PSIf
# read in luminance file if going to correct for it
if CorrectLuminance: 
	print 'using corr_file'
	#with open(default_path+corrf,'r') as f: python >2.5
	f = open(corrf,'r') #python 2.5
	lumcorr = [x[0] for x in csv.reader(open(corrf), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
	print 'Lum Corr size', len(lumcorr)

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
	Centersf = avi_inpath+"Cntrs_"+file_name+".csv"

#override above for testing
#avi_file = avi_inpath+"Leader Tests 1.avi"
#Centersf = avi_inpath+"Cntrs_Leader Tests 1.csv"
print file_name

f = open(Centersf,'r') #python 2.5
rdr = csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)
#slices, FramePos, raw, pcc, pn, pw, pcnp, pnw,pma = zip(*rdr) 
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

#convert the tuples to lists
#pwa =list(pw)
r2 = list(pcc)
slices =list(slices)
#FramePos = list(FramePos) This would use original PSI centers, 
#use modified PSI centers from pnw
#WE WILL USE PCN AS BEST VALUES
FramePos = list(pcn)
pma = list(pma)
flc = list(flc)
print FramePos



#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
PSI = [x[0] for x in csv.reader(open(PSIf), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
print'rows:',len(PSI)
#print 'PSI',PSI

def computeStdDev(pixels, mean): # not used here
	#usage  stdDev = computeStdDev(ip.getPixels(), mean) this would do it for the entire image, but will not work for rgb image.
	for i in range(len(pixels)):
		s += pow(pixels[i] - mean, 2)
	return sqrt(s / float(len(pixels) -1))

#---------------------TEMPLATE GENERATOR FUNCTION ------------------------------------------
def GetTemplate(PCntr,NewW,stdW,P,pcase):
	#NewW can vary depending on choices for width;
	#P is already either a PSI of stdWidth, or a vector of size NewW.
	
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
	if NewW != stdW:
		#----------PSI HISTOGRAM INTERPOLATOR-----------------------------------------------------------------------
		from bisect import bisect_left
		from bisect import bisect_right
		#Set up new x intervals and fractions between rows lists; this is done by
		#just multiplying the PSI and row arrays by a fraction of old/new or new/old
		#we do not necessarily have to multiply PSI values by a factor; doing this assumes
		#the integrated amount of total light in the PSI envelope must remain the same as in a
		#histogram of constant units (photons in our case). If we do not do this it is equivalent 
		#to saying that the photons yield is independent of PSI width and photon yield. must remain the same
		#However, in any case the correction is no more than about 10% anyway.
		xfactor = float(NewW)/float(stdW) #must convert int-> float or produces only 0
		yfactor = float(stdW)/float(NewW)  # we know from system dynamics new PSI values must be larger on a compressed scale.
		#yfactor = 1 if photon collection not a constant
		if NewW > stdW:
			xstdrows = [x for x in range(NewW)] #gen. integer list against the new PSI width
		else:
			xstdrows = [x for x in range(stdW)] #gen. integer list against the std PSI width
		PSIfrac = [0]*len(xstdrows)
		PSIfrac = [y*yfactor for y in P]
		x_frac_new = [0]*len(xstdrows)
		x_frac_new = [x*xfactor for x in xstdrows]
		#print 'PSI length', len(P)
		#generate new x integer array to interpolate against fractional x list
		for i in range(xNewSize-1):
 	    #find the new x values that bracket the integer value of the integer x range 
			if i > 0:
				x1 = bisect_left(x_frac_new,xstdrows[i]) -1
			else:
				x1 = bisect_left(x_frac_new,xstdrows[i])
			x2 = bisect_right(x_frac_new,xstdrows[i]) #get index on x_new just greater than our x_new integer
			print 'x1,',x1,'x2',x2,'xNewSize',xNewSize
			y1 = PSIfrac[x1]
			y2 = PSIfrac[x2]
			#interpolate the x value to find the new PSI value at the new x integer value
			PSIIntX = y1 + (xstdrows[i]-x_frac_new[x1])*(y2-y1)/(x_frac_new[x2]-x_frac_new[x1])
			PSIy.append(int(PSIIntX)) #add the y value to the new PSI vector
			PSIy = PSIy[:xNewSize]
			#-----------END PSI INTERPOLATOR----------------------------------------------------------------------
	else: # if PSI is only case left, do not need to change width
		PSIy = P[:xNewSize]
		#print 'in else and PSIy = ', PSIy, 'xNewSize', xNewSize

	#CORRECT THE ROW OF PSIy data for luminance distortion
	if CorrectLuminance: #that is, do not use just the normalized PSI. correct for any frame lum. distortion.
		PSInew =[0]*xNewSize
#		#correct profile so that template black (rgb 0) represents no correction
		Pnmax = max(PSIy)
		PSInew = [round(Pnmax - x) for x in PSIy] #reversed composite filter profile based on 255 (white; no change)
		#Pnmin = min(PSInew)
		# Found that adjusting a factor helped improve the leveling operations. No leveling is 1.0 and found 
		# for test avi 1.3 worked reasonably well
		#PSInew = [(x - Pnmin)*PSILightFactor for x in PSInew] old and wrong
		PSInew = [x*PSILightFactor for x in PSInew] 
		# Careful! Adjusting only first 1080 rows of the data.
		for j in range(len(lumcorr)):
			PSInew[j] = PSInew[j] + lumcorr[j]
		template = PSInew
	else: #not correcting luminance of template PSI
		# just reverse Luminances to get mask
		Pnmax =max(PSIy)
		PSIy = [(Pnmax-x) for x in PSIy]
		Pnmin = min(PSIy)
		PSIy = [(IBase - (IBase -x)*PSILightFactor) for x in PSIy]  
		template = PSIy
		#take out all but 1080 rows
	del template[ImgHt+1:len(template)]
	return template
#----------------END TEMPLATE GENERATOR FUNCTION---------------------------------------

#--------------------PIXEL CORRECTOR----------------------------------------------------
def correctPixel(p,W, H, lp, rp, tP,pixtype):
# p = pixel type, r,g, or b. 
# W = width of the image in pixels, typcially 2
#ImgHt = image height, or list/vector size
#lp = starting column of pixels to correct (typically 0)
#rp = pixel column to correct (usually w-1), which means col 1
#tP = template profile list (vector)
# pixtype = r, g, b, or x used to denote channel being corrected for human eye grey level response; x = do not correct
#As Cardona indicates- "The ImageProcessor.getPixels() method called on a ByteProcessor returns a java.lang.Object, 
#but it is magically usable as the byte[] that it actually is Good for python. The byte array in ip.getPixels()
#is quite odd: from 0 to 127 is 0-127 in integer 0-255 space, from -128 to -1 is 128-255 in integer 0-255 space"
# see https://www.mcdb.ucla.edu/Research/Hartenstein/software/imagej/Add_Noise.py
#gray = (red + green + blue) / 3 or gray = 0.299 �  red + 0.587 �  green + 0.114 �  blue 
#This def retains the possibility for generating a more than 1 column change as required for direct pixel by
#pixel conversion.
	if rp > 1:
		for y in range(H):
			for x in range(lp, rp):
				offset =y*W
				xoff = offset+x
				if p[xoff] <0:
					ap = p[xoff]+256 
				else:
					ap = p[xoff]	
				ap += int(tP[y]) 
				ap = max(0,ap)
				ap = min(255,max(0,ap))
				if ap > 127: ap = ap - 256 # back to -128 to -1
				p[xoff] = ap
	else:
		for y in range(H):
			offset=y*W
			if p[offset] <0:
				ap = p[offset]+256 
			else:
				ap = p[offset]	
			ap += int(tP[y]) 
			ap = max(0,ap)
			ap = min(255,max(0,ap))
			if ap > 127: ap = ap - 256 # back to -128 to -1
			p[offset] = ap
			#can apply gray visual correction rather than implicit 0.3*y:
			#0.299*TPSI[y] for r
			#0.587*TPSI[y] for b
			#0.114*TPSI[y] for g
	if pixtype != 'x':
		if pixtype == 'r':
			grey_correction = (0.333 - 0.299)
			p = [int(x+x*grey_correction) for x in p if x > 1 ]
		elif pixtype == 'g':
			grey_correction = (0.587 - 0.333)
			for x in p:
				if x < 181:
					p = int(x-x*grey_correction)
				else:
					p = 255
		elif pixtype	== 'b':
			grey_correction = (0.333 - 0.114)
			p = [int(x + x*grey_correction)  for x in p if x > 1]
	else:
		pass
		
	return p
	
	#how to rebuild a 24 bit byte value if working on pixel bytes directly
	#cp[offset+x] = ((r[offset+x] & 0xff) << 16) + ((g[offset+x] & 0xff) << 8) + (b[offset+x] & 0xff) 	
#----------------------------END PIXEL CORRECTOR DEF----------------------------

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WORK THE AVI IMAGES.
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# with the help of Wayne Rasband on the listserver, this is the way 1.47 opens the
#avi stack for reading the slices etc

#AVI FILE WAS CHOSEN EARLIER...JUST OPEN IT
#must use a virtual stack, i.e, the process extracts individual frames from the avi file, 
#and not creating memory issues. Operates slower, but much larger files/images can be handled than
#using ImageStack.
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

#set up lists for the new csv output file; output only necessry parameters.
NewSlices = [0]*(maxslices+1)
NewFramePos = [0]*(maxslices+1)
Newpma = [0]*(maxslices+1)
Newflc = [0]*(maxslices+1)
kk = 0

slices = [int(x) for x in slices]
FramePos = [int(x) for x in FramePos]

#PROCESS IMAGES LOOP
#--------------------------------------------------------------------------------
# This is the start of the loop to run through all frames of the video sequence
#because the data is sorted we will just 
starttime = time.time()
count = 0
t_ID = 0
OldWidth = stdWidth
OldPSICenter = -1 #a PSICenter may start at zero or greater.
pcase = 3

print 'starting frame:', nstart, 'stop frame:', nstop

#++++++++++++++++++++MAIN IMAGE PROCESSING LOOP++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#set nstart so it is reading only the true frame numand not following just an index.

print 'frames numbers to process:'+str(nstart)+' to '+str(nstop)
#Run through all slices to remove PSI on frame
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

for i in range(nstart,nstop):
	#What width will we use
	if lock_PSI_width == 2:
		NewWidth = pma[i]
	indx = slices[i] # i may not be the same as slice number, be sure to ref index to get slice
	PSICenter = FramePos[i]
	# What was the indx slice in original is now on a new index, so we need to associate the parameters with this new slice 
	# the old nstart index, whatever it was, is now the new index 1, and the new csv stream will reflect that 
	#reset the csv file that will be created to represent the new slice configuartion in stack2 and restrict its scope.
	NewSlices[i] = indx
	NewFramePos[i] = FramePos[i]
	Newpma[i] = pma[i]
	Newflc[i] = flc[i]
	
	#Grab the PSI list starting at the known center column
	#The section of PSI to grab depends on how the PSI profile file PSI_norm_1358.csv is arranged. 
	#By convention, index 0 of the PSI csv file starts at the PSI peak minimum (peak center). 
	#PSI_avi_Leader_Template_Processor.py "moves" this profile "backward" until a fit is found. The PSI 
	#center is the difference between starting row (0) and number of steps (row interval jumps) to the best 
	#corr. coef. fit. To get the profile for a frame, the next std PSI profile center situated stdWidth rows
	#away is subtracted from the frame PSICenter position; this provides the starting row of the sub profile we need.
	#print 'slice:', indx, 'PSICenter=',PSICenter,'OldPSICenter=', OldPSICenter, 'NewWidth',NewWidth
	# we will not worry about rare to non existant case of PSICenter = OldPSICenter:
	sPSI = PSI
	if NewWidth > stdWidth:
		sPSI.extend(PSI[0:(NewWidth-stdWidth+1)])
		Poffset = NewWidth - PSICenter
		sPSI = PSI[Poffset:(int(Poffset+NewWidth))] 
	else:
		Poffset = stdWidth - PSICenter
		sPSI = PSI[int(Poffset):(int(Poffset+stdWidth))] 
	#print 'PSICenter',PSICenter, 'Poffset', Poffset, len(sPSI), 'max PSI range', Poffset+stdWidth
		# PSI still 2*PSI cylces and starts at the std PSI in csv file until this point
		#sPSI will be variable in length, but can be no less than stdWidth 
		
	#Generate a Filter image: change only what needs to be changed from the std PSI
	#1. new width or new center - requires PSI interpolation and luminance correction (if set).
	#2. oldwidth and same center - no changes to the sub PSI are needed at all
	#Case 1

	if (NewWidth != OldWidth) or (PSICenter != OldPSICenter): #may need interpolation to new width and luminance corr.
		#print 'slice:', indx, 'PSICenter=',PSICenter, 'NewWidth', NewWidth, 'OldWidth=', OldWidth, 'len sPSI', len(sPSI)
		pcase = 1
		if t_ID < 0: imp_template.close() #remove old template if exists (IDs are always < 0)
  		tPSI = GetTemplate(PSICenter,NewWidth,stdWidth,sPSI,pcase) #returns a 1 x 1080 PSI profile list

		#if indx == 4:
		#	CentersPath = avi_outpath+"PSIProfiletest"+".csv"  		
  		#	f = open(CentersPath,'w') 
		#	writeout = csv.writer(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n' ) 
		#	for row in tPSI:
		#		writeout.writerow([row]) #had much trouble getting column output; "trick" is the brackets around -> [row]
		#	f.close()
		#	sys.exit()
 
	else:
		pcase = 2 
		#do nothing else

	OldWidth = NewWidth
	OldPSICenter = PSICenter
	#print 'tPSI', tPSI, 'minimum in tmeplate:', min(tPSI)	
	#print 'PSICenter', PSICenter,'NewWidth', NewWidth, 'frame #', indx
	#Each item in the index list represents a frame to be luminnace corrected using the single width 
	#adjusted PSI profile. The way this is set up, this will be a simple addition to each RGB pixel.
	#print '---------'+str(imp)+'slice'+str(k)+'-----------'
	#work with straight arrays as much as possible to save calculation time. 
	#Create the RBG filter image to subtract an RGB image and procesor 
	#with height and width of current open image and fill it with black (0)
	ImgWidth = stack.getWidth() 
	ImgHt = stack.getHeight()

	#make sure we get proper image from stack; a bit convoluted to isolate proper image from stack	
	imp = ij.WindowManager.getImage(stack_ID) #focus on stack
	ip=imp.getProcessor().duplicate() #gets processor from duplicate slice to check if RGB
	pixnum = ip.getPixelCount()		
	type = imp.getType()
	if ImagePlus.COLOR_RGB != type:	print 'Stack does not contain RGB images' 
	
	imp = ij.WindowManager.getImage(stack_ID) #focus on stack
	slice = stack.setSlice(indx) #indx taken directly from csv first column
	#The relationship of slice and stack is a bit confusing. regardless of slice called, the
	#id returned is always the stackID. Could not directly act on it, must duplicate. The good news is
	#that duplicate acts on the slice showing. 
	IJ.run("Duplicate...", "title=[slice_"+str(indx)+"]") #note how option set up for acceptable string
	ASlice = "slice_"+str(indx)

	#if new profile generated create new template
	if pcase < 2:
		#Create a color image that is two pixels wide and 1080 high, but we will generate one pixel wide template
		title = 'PSIImage'
		wpixels = 2
		#proImg has a fill with black only
		proImg = NewImage.createRGBImage(title, wpixels, ImgHt, 1, NewImage.FILL_BLACK)
		#process image into PSI profile
		prop = proImg.getProcessor()
		pixnum = prop. getPixelCount()
		r = zeros(pixnum, 'b')
		g = zeros(pixnum, 'b')
		b = zeros(pixnum, 'b')
		prop.getRGB(r,g,b) #split image into three byte arrays r, g, and b for processing
		# if the last argument is set to 'x' no human visual grey color correction will be applied
		# in other words, will assume grey = r/0.33, g/0.33, b/0.33
		
		correctPixel(r,wpixels,ImgHt,0,(wpixels-1),tPSI,'x') # modifies only first column (0)
		correctPixel(g,wpixels,ImgHt,0,(wpixels-1),tPSI,'x')
		correctPixel(b,wpixels,ImgHt,0,(wpixels-1),tPSI,'x')
		prop.setRGB(r, g, b) # rebuild the ip processor, subsituting the calculated values.
		
		#proImage now contains a 1x1080 image
		#proImg.show()
		#one way to duplicate an image, imp in this case
		#copy = Duplicator().run(imp)
		#for unknown reasons the resize function produces the desired profile as an expanded 
		#region and a black region of total size equal to width (1920), so profile was only
		#960. Could not figure out what was wrong, so make double wide and use ROI to select 
		#and build new image. prop is the double image from the resize
		n1 = prop.resize(3840,1080)
		imp_temp=ImagePlus("temp_template",n1)
		imp_temp.show()
		#alternate to do same thing: IJ.run(proImg, "Scale...", "x=1920 y=1 width=3840 height=1080 interpolation=None create title=n1")
		#roi1 = prop.setROI(0, 0, 1920, 1080) hmmm no such property in colorprocessor
		#imp_template = ij.WindowManager.getCurrentImage()	
		IJ.makeRectangle(0, 0, 1920, 1080)
		#print 'title',imp_temp.getTitle(), 'image ID',imp_temp.getID()
		IJ.run("Copy") #really kludgy, but nothing else seemed to work
		IJ.run("Internal Clipboard")		
		imp_temp.close()
		imp_template = ij.WindowManager.getCurrentImage()		
		imp_template.setTitle("template")
		
		#print 'title',imp_template.getTitle(), 'image ID',imp_template.getID()
		t_ID = imp_template.getID() # ID will be used to close if changed; is a negative value
		imp_template.show()

		#ij.WindowManager.getImage("template") #attribute can be an ID or title, but must include WindowManager to use
		#getMinAndMax(min, max) not available for RGB images only greylevel
		#print 'Min', min, 'Max:',max
		#set a new brightness contrast LUV on template to reduce flatness.
		
		#if indx==4: sys.exit()		#used to stop operation so can manually change brightness/contast with BrightnessContrastAdjuster.ijm
		#IJ.setMinAndMax(0,212)   #after much checking this was about the best I could do, and it still is not good for contrast.
		

		#How to rename a slice - setMetadata("Label", string)
	
	sip = imp.getProcessor().duplicate()  
	time.sleep(0.020)
	simp = ImagePlus("ASlice", sip)
	simp.show()

	#ASlice is already waiting
	IJ.run(simp, "Calculator Plus", "i1=ASlice i2=template operation=[Add: i2 = (i1+i2) x k1 + k2] k1=1 k2=0 create")

	#result file of calc.
	corImg = ij.WindowManager.getCurrentImage()
	corImg.setTitle("out_"+str(indx)+".png")
	simp.close()
			
	#imagestack can add a slice after a specifed slice. virtualstack cannot, but it reads file in a sequence. 
	#imp = ImagePlus(stack.getLabel(i), ip) 
	
	out_image = imagepath+corImg.getTitle()
	FileSaver(corImg).saveAsPng(out_image) 
	stack2.addSlice(corImg.getTitle())
	corImg.close()
	count+=1

	IJ.selectWindow(ASlice)
	ax=ij.WindowManager.getCurrentWindow()
	#problem develops with timing; not sure what is going on, but images
	 #sometimes get screwed up and i2 not template.	
	try :
		#print ax.getTitle()#'NoneType' object has no attribute 'getTitle'
		ax.close()
	except AttributeError, err1: 
		time.sleep(0.200)
		ax=ij.WindowManager.getCurrentWindow()
		ax.close()
	print 'frames done:',count+1
	#if count == 20: sys.exit()

print 'stack2 size', stack2.getSize()
#for list1 in range(1,count+1):
#	print 'stack2 file name', stack2.getFileName(list1)

ImagePlus("stack2",stack2).show()
IJ.selectWindow("stack2")

IJ.run("Input/Output...", "jpeg=90 gif=-1 file=.txt use_file copy_row save_column save_row")

AVI_file_name = "stack2"
AVI_file_out = AVI_file_name+".avi"
avi_Out = avi_outpath+AVI_file_out
#no common program I have reads this, including irfanview, or vitualdub64,use jpeg compression.
#IJ.run("AVI... ", "compression=PNG frame=30 save=["+avi_Out+"]") 
IJ.run("AVI... ", "compression=JPEG frame=30 save=["+avi_Out+"]")

PSICenterOutput = []
PSICenterOutput.append(NewSlices)
PSICenterOutput.append(NewFramePos) #PSICenterprec)
PSICenterOutput.append(Newpma)# PSIMovAvg)
PSICenterOutput.append(Newflc) #FrameLumCor)
print PSICenterOutput
PSICenterOutput =[list(i) for i in zip(*PSICenterOutput)] 

#Depending on slicecutter value, last row may not be filled. Need to check for deletion...
row_total = 0.0
if PSICenterOutput[len(PSICenterOutput)-1]:
	for x in PSICenterOutput[len(PSICenterOutput)-1]: 
		row_total += x
	if row_total==0:
	 	PSICenterOutput.pop(-1)
for row in PSICenterOutput:
	print row

csv_out = avi_outpath+'Cntrs_'+AVI_file_name+'.csv'
print 'csv out file', csv_out
f = open(csv_out,'w') 
fout = csv.writer(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n' ) 
for row in PSICenterOutput:
	fout.writerow(row)
f.close()
#if we were only copying centers
#Cntrs_Out = avi_outpath+csv_out
#shutil.copy(Centersf, Cntrs_Out)
imp_template.close()	
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

