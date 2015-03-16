#Python code to find the projector shutter Image (PSI) center position on 
#video frames in an AVI movie sequence. 
# code is based on Fiji implementation, which uses Python 2.5 and ImageJ 1.46
#note avi code will need to be changed for 1.47 imagej code.
#Fiji-ImageJ does not recognize latesst Python print function change using
#paranthesis and does not allow numpy package, which would simply the matrix
#code substantially.

#THIS CAN BE SPED UP BY RUNNING FROM THE COMMAND LINE, BUT REQUIRES A A REWRITE SO THAT
#ALL INPUT IS EITHER AUTOMAITC OR FROM THE COMMAND LINE. THE FOLLOWING COMMAND LINE EXAMPLE 
#MAY BE USEFUL, ONCE EVERYTHING IS CONVERTED. REALLY THE ONLY CONVERSION SHOULD BE THAT FOR EACH 
#COMMAND LINE RUN THE AVI FILE NAME NEEDS O BE CHANGED.

#‘fiji-linux64 --headless --jython ./scripts/PSI_avi_Processor.py -batch &

#Requies: 
# 	A csv file of two connected mormalized PSI profiles  (2 x wavelength)
	# Default file name: "PSI_norm_1358.csv"
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
from math import sqrt
import csv
import sys
import thread
import time
from ij.process import ImageStatistics as IS
#from ij.gui import GenericDialog   
from math import sqrt
from jarray import zeros #jarray is a Jython module that implements only two methods, zeros and array
from operator import itemgetter
import java.io.File.__dict__ 
from mpicbg.imglib.image.display.imagej import ImageJFunctions as IJF
#from numpy import * not allowed in Jython.
#SET ALL PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#FOR PRODUCTION RUNS WILL NEED TO IMPLEMENT OPENDIALOG, SAVEDIALOG AND PROBABLY GENERICDIALOG METHODS
#SEE http://www.ini.uzh.ch/~acardona/fiji-tutorial/#generic-dialog FOR STARTER IDEAS.

# set working drive and main folder if needed
DriveOption = "C" #either C, E, G, X is for dialogues to choose diectories

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
	os.chdir("C:\\")
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

if DriveOption == "C":
	default_drivepath = "C:\\Canon\\" 
elif DriveOption == "E":
	default_drivepath = "E:\\"  
elif DriveOption == "G":
	default_drivepath = "G:\\"
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
corrf = templatefiles+"Frame_Luminance_Correction_Coef.csv"
PSIf = templatefiles+"PSI_norm_1358.csv"

os.chdir(avi_inpath) #default_path)
d1 = os.getcwd()  
print d1

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

#SET ALL PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
slicecutter = 1		# slices to skip
nstart = 2 # starting frame to pick up only white leader frames PSIs 
nstop = -1 #
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#NOTE THAT IN THIS SPECIFIC CASE RIGHT NOW WE ARE SKIPPING FIRST FRAME BECAUSE IT 
#IS NOT A VALID MOVIE FRAME, JUST A HEADER TO INDICATE 100s
#change the range from 2 back to 1 for real data.
#++++++++++++++++++++++++++++++++++++++++
#CRITICAL INFO THAT MUST BE SUPPLIED FROM OTHER METHODS
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
stdWidth = 1358			# width of the normalized PSI
NewWidth = stdWidth
B1 = 1166.910722		#Blanking interval obtained from rotating camcorder info
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
ImgHt = 1080
ImgWidth = 1920
csize = ImgHt + int(0.25*float(ImgHt)) # variable used to expand row size when PSI width > stdWidth
CorrectLuminance = True 	# If true, use only base PSI;false- use PSI profile corrected for luminace.
corr_file = False			# True- use Imax, Imin, Idif luminance correction coefficients, from csv file; false- use values below (hardwired by user). 

#mext four values used to create final rectangle, usually will mirror values used for finding centers in template script.
topPt =0 #60				# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240					# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020          # bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680 				# rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ

IBase=255
# Default 3rd order coefficients
Imax = [-6.0772E-08,3.40639E-05,0.042506019,123.6491484]
Imin = [-2.5251E-08,2.84076E-05,-0.001742574,74.722009]
Idif = [-3.5521E-08,5.65627E-06,0.044248592,48.92713942]
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#Check or set parameters
gp = getParameters()
CorrectLuminance, corr_file =gp

#Excel stores numbers in a csv file without quotes, with a comma as separator
#the QUOTE_NUMERIC parameter converts to a float value internal to reader
#using 'with' is apparently safer code for cleanup on exceptions
#but next line not available in jython 2.5?? gives error about new keyword in 2.6
#with open(default_path+PSIf) as f:
	#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
#	PSI = [x[0] for x in csv.reader(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 

print PSIf

#Read the csv file containing max and min 3rd order equations parameters if they exist
if corr_file: # Supplying file or static values in this script?
	#with open(default_path+corrf,'r') as f: python >2.5
	f = open(corrf,'r') #python 2.5
	corr = [x for x in csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)]
	f.close()
	Imax=[0]*4
	Imin=[0]*4
	Idif=[0]*4
	Imax=[corr[0][x] for x in range(4)]
	Imin=[corr[1][x] for x in range(4)]
	Idif=[corr[2][x] for x in range(4)]

#STEP 1 SMOOTH THE PSI WIDTHS
#WILL USE SIMPLE MOVING AVERAGE AS MAIN MTHOD.
#BRING IN FILE
#column order in csv file = ['slice','cn','raw','ri','pn','pw']
#slice is frame number; 
#cn = PSI center position relative to current slice or frame, 
#raw = value from pattern recognition w/ no corrections (latest version has no corrections, so raw = cn
#ri = inerval index where PSI center found. raw/ri = rows between points analyzed in original image
#pn = value of 1 or 2 PSIs between frames, only can be used if slicecutter =1 (every frame analyzed);
#pw = PSIw->PSIWidth between frames; 

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
slices, FramePos, raw, ri, pn, pw = zip(*rdr) 
# above a bit esoteric-> "*rdr" unpacks the elements of each line; zip takes tuple of each row such that successive 
#elements of each row are now tuples. The tuples can be accessed as lists by zip(*array)[column #, e.g. 0]
f.close()

print rdr

HB = ImgHt + B1 	

#STEP 2 GET THE MOVING AVERAGE
#STARTS WITH 2ND ENTRY; USE A 3 BIN AVERaGE

#pstream = [0]*(len(pw)+1)
#pstream[0] = pw[0]
pwa = [0]*(len(pw)+1)
#convert the tuples to lists

pwa =list(pw)
slices =list(slices)
FramePos = list(FramePos)

for k in range(1,(len(pw)-1)):
	pwa[k] = (pw[k-1]+pw[k]+pw[k+1])/3.0

#get overall average
pwAver = round(sum(pwa)/len(pwa))	
NewWidth = pwAver
print 'NewWidth aver.', NewWidth

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

#---------------------TEMPLATE GENERATOR FUNCTION ------------------------------------------
def GetTemplate(PCntr,NewW,stdW,PSI,cs, pcase):
	#To compensate for inevitable frequency shift, calculate a bigger range than necessary
	#by 25% i.e.,1350 instead of 1080.
	#More detailed explanation on template building can be found in PSI_avi_Leader_Template_Processor.py
	MaxPSIrows = csize
	template=[]
	print 'PCntr',PCntr,'NewW',NewW,'stdW',stdW

	xNewSize = int(round(NewW)) 	 #number of integer bins to generate
	Rowrng = int(round(MaxPSIrows,0))  #number of rows to genarate
	#The values in the PSIy array are cut in at intervals of total row range/interval over the extra range (1320)
	PSInew =[0]*xNewSize
	#Set up new x intervals and fractions between rows lists
	#There will be a problem if newwidth > old width, so first expand PSI by expanding sPSI, if needed.
	if NewW > stdW:
		sPSI.extend(sPSI[0:(NewW-stdW+1)])
		NewW = len(sPSI)
	
	if NewW != stdW:
		xfactor=float(NewW)/float(stdW) #must convert int-> float or produces only 0
		xoldrows = [x for x in range(stdW)] #gen. integer list
		xfractionrows = [x*xfactor for x in xoldrows] 
		#generate new x integer array to interpolate against fractonal x list
		xnew = [x for x in range(0,NewW)] 
		xfractiondif = xfractionrows[1]-xfractionrows[0] # =(X2-X1) below
		
		#INTERPOLATE PSI RGB VALUES FROM FRACTIONAL TO INTEGER VALUES
		#There is an interpolation function in numpy and scipy, but alas, not in Jython
		nPSI = len(sPSI)
		#Generate two lists one index off from each other and get difference between lists
		#the next operation also slices sPSI down to the width we want
		sPSIy1 = sPSI[:xNewSize] 
		sPSIy2 = sPSI[1:xNewSize+1]
		ydif = [(x - y) for x,y in zip(sPSIy2,sPSIy1)] # =(Y2-Y1)
		#Each x value in the xfractionrows needs to be subtracted from the nearest integer.
		#In turn, that integer value was alraedy formed from the index number by multiplying by the interval
		xndif = [(x - int(y)) for x,y in zip(xfractionrows,xfractionrows)] #X-X(nearest int)
		#Put the interpolation lists together to get the new PSI values
		#Not sure if this is any faster than just referencing individual elements
		yOVERx = [(x/xfractiondif) for x in ydif]	 #(Y2-Y1)/(X2-X1)
		Addy = [(x*y) for x,y in zip(xndif,yOVERx)]  #(X-X1)(Y2-Y1)/(X2-X1)
		PSIy = [(x+y) for x,y in zip(sPSIy1,Addy)] 	 #Y1+(X-X1)(Y2-Y1)/(X2-X1)
		#PSIy is now an expanded or condensed row of PSI values
	else: # if PSI is only case left, do not need to change width
		PSIy = sPSI[:xNewSize]
	
	#CORRECT THE ROW OF PSIy data for luminance distortion
	if CorrectLuminance: #that is, do not use just the normalized PSI
		Ir0 = Imax[3]-Imin[3]	
		for j in range(0,len(PSIy)):
			Imaxr = Imax[0] * j**3 + Imax[1] * j**2 + Imax[2] * j + Imax[3]
			Iminr = Imin[0] * j**3 + Imin[1] * j**2 + Imin[2] * j + Imin[3]
			Idif = Imaxr - Iminr 
			#Calculate luminance corrected value by getting difference from 255 and adding to current value 
			PSInew[j] = Imaxr + (((PSIy[j] - IBase) * Idif) / Ir0) # Imax,o-Imin,o from dif between Imax and Imin & 
		#correct profile so that when we add pixels "whitest" pixel will now be a zero correction value
		Pnmax =max(PSInew)
		PSInew = [round(Pnmax-x) for x in PSInew] #reversed composite filter profile 
		template = PSInew
	else: #not correcting luminance
		# just reverse to get mask
		Pnmax =max(PSIy)
		PSIy = [Pnmax-(x+y) for x,y in zip(sPSIy1,Addy)] 	
		template = PSIy
		#take out all but 1080 rows	
	del template[ImgHt+1:len(template)]
	return template
#----------------END TEMPLATE GENERATOR FUNCTION---------------------------------------

#--------------------PIXEL CORRECTOR----------------------------------------------------
def correctPixel(p,W, H, lp, rp, tP):
#As Cardona indicates- "The ImageProcessor.getPixels() method called on a ByteProcessor returns a java.lang.Object, 
#but it is magically usable as the byte[] that it actually is Good for python. The byte array in ip.getPixels()
#is quite odd: from 0 to 127 is 0-127 in integer 0-255 space from -128 to -1 is 128-255 in integer 0-255 space"
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
			#could apply gray visual correction rather than implicit 0.3*y:
			#0.299*TPSI[y] for r
			#0.587*TPSI[y] for b
			#0.114*TPSI[y] for g
	return p
	
	#how to rebuild a 24 bit byte value if working on pixel bytes directly
	#cp[offset+x] = ((r[offset+x] & 0xff) << 16) + ((g[offset+x] & 0xff) << 8) + (b[offset+x] & 0xff) 	
#----------------------------END PIXEL CORRECTOR DEF----------------------------

#alternate method when Jython catches up with 64 bit Pyhton loadtxt is a numpy function
#PSI = numpy.loadtxt(open(PSIf,"r"),delimiter=",",skiprows=0, dtype=int)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WORK THE AVI IMAGES.
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# with the help of Wayne Rasband on the listserver, this is the way 1.47 opens the
#avi stack for reading the slices etc

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
AllSlices = stack.getStackSize()

ImgWidth = stack.getWidth() 
ImgHt = stack.getHeight()

stack2 = VirtualStack(ImgWidth, ImgHt, None, imagepath)
stack2ID = stack.getID()
#stack2 = ImageStack(ImgWidth, ImgHt) #this opens an image stack, but not a virtual stack, so only can work off available RAM
#Future reference. Virtual stack is read only, to manipulate it, duplicate it. Does not make sense. why have an addslice if true.

maxslices = int((AllSlices-nstart)/slicecutter)
print 'AllSices', AllSlices,'maxslices', maxslices
#pre-calc the camcorder total row cycle vert.blanking region + video frame height
#Ftotrows = B1+ImgHt

#set up lists
PSICenter = [0]*(maxslices+1)
SliceNum = [0]*(maxslices+1)
pn = [0]*(maxslices+1)
PSIFramePos = [0]*(maxslices+1)
Ck=[0]*(maxslices+1)
PSIraw=[0]*(maxslices+1)
PSIw=[0]*(maxslices+1)
PSIRowIndex=[0]*(maxslices+1)
kk = 0

#convert FramePos to integers for later use
FramePos = [int(x) for x in FramePos] #form csv file

#REDUCE CALC TIME - DOUBLE SORT DATA, FIRST BY MONVING AVER. PSI WIDTHS, THEN BY PSI CENTER POSITION.
#Round PSI widths to nearest thenth row and convert to integer
#- reduces number of unique PSI widths at some expense of accuracy
slices = [int(x) for x in slices]
FramePos = [int(x) for x in FramePos]
pwa = [int(round(x,-1)) for x in pwa]
#form a tuple of critical input values and sort
regroup = zip(slices, FramePos,pwa)
sgroup = sorted(regroup, key=itemgetter(2, 1)) 
#convert tuples to lists
slices, FramePos, pwa = zip(*sgroup) 

slices = list(slices)
FramePos = list(FramePos)
pwa = list(pwa)

for item in sgroup:
	print item

#FIND UNIQUE PSI WIDTHS
uniques = set(pwa) #Set finds unique values in a list and acts like a list.(NewWdith != OldWidth) ans(PSICenter != OldPSICenter)
uniques = list(uniques) #list of unique widths; for some reason needed to convert to list
print 'uniques', uniques
print 'unique items count', len(uniques)

#PROCESS IMAGES LOOP
#--------------------------------------------------------------------------------
# This is the start of the loop to run through all frames of the video sequence
#because the data is sorted we will just 
startime = time.time()
count = 0
#GETTING STUCK AS FRAME 1 AFTER FIRST FRAME
t_ID = 0
OldWidth = 0
OldPSICenter = 0
pcase = 3

#MAIN IMAGE PROCESSING LOOP

#Run through all slices to remove PSI on frame
for i in range(len(pwa)):
	NewWidth = pwa[i]
	indx = slices[i]
	PSICenter = FramePos[i]
	#Grab the PSI list starting at the known center column
	#The section of PSI to grab depends on how the PSI profile file PSI_norm_1358.csv is arranged. 
	#By convention, index 0 of the PSI csv file starts atthe PSI peak minimum (peak center). 
	#PSI_avi_Leader_Template_Processor.py "moves" this profile backward until a fit is found. The PSI 
	#center is the difference between starting row (0) and number of steps (row interval jumps) to the best 
	#corr. coef. fit. To get the profile for a frame, the next std PSI profile center situated stdWidth rows
	#away is subtracted from the frame PSICenter position; this provides the starting row of the sub profile we need.
	if PSICenter != OldPSICenter:
		Poffset = stdWidth - PSICenter
		sPSI = PSI[Poffset:(Poffset+stdWidth)] # PSI is still 2*PSI cylces and starts at the std PSI in csv file until this point

		#Generate a Filter: change only what needs to be changed from the std PSI
		#2 cases:
			#1. new width or new center - requires PSI interpolation and luminance correction (if set).
			#2. oldwidth and same center - no changes to the sub PSI are needed at all
	if (NewWidth != OldWidth) or(PSICenter != OldPSICenter): #need interpolation to new width and luminance corr.
		pcase = 1
		if t_ID < 0: imp_template.close() #close() #remove old template
		tPSI = GetTemplate(PSICenter,NewWidth,stdWidth,sPSI,csize,pcase) #returns a 1 x 1080 PSI profile list
	else:
		pcase = 2
	OldWidth = NewWidth
	OldPSICenter = PSICenter
	#print 'tPSI', tPSI	
	print 'PSICenter', PSICenter,'NewWidth', NewWidth, 'frame #', indx
	#Each item in the index list represents a frame to be luminnace corrected using the single width 
	#adjusted PSI profile. The way this is set up, this will be a simple addition to each RGB pixel.
	#print '---------'+str(imp)+'slice'+str(k)+'-----------'
	#work with straight arrays as much as possible to save calculation time. 
	#Create the RBG filter image to subtract an RGB image and procesor 
	#with height and width of current open image and fill it with black (0)
	ImgWidth = stack.getWidth() 
	ImgHt = stack.getHeight()

	#make sure we get proper image from stack; a bit convoluted to isolate proper image from stack	
	imp = WindowManager.getImage(stack_ID) #focus on stack
	ip=imp.getProcessor().duplicate() #gets processor from duplicate slice to check if RGB
	pixnum = ip.getPixelCount()		
	type = imp.getType()
	if ImagePlus.COLOR_RGB != type:	print 'Stack does not contain RGB images' 
	
	imp = WindowManager.getImage(stack_ID) #focus on stack
	slice = stack.setSlice(indx) 
	#The relationship of slice and stack is a bit confusing. regardless of slice called, the
	#id returned is always the stackID. Could not directly act on it, must duplicate. The good news is
	#that duplicate acts on the slice showing. 
	IJ.run("Duplicate...", "title=[slice_"+str(indx)+"]") #note how option set up for acceptable string
	ASlice = "slice_"+str(indx)

	#if new profile generated create new template
	if pcase<2:
		#Create a color image that is two pixels wide and 1080 high, but will generate one pixel wide template
		title = 'PSIImage'
		wpixels = 2
		proImg = NewImage.createRGBImage(title, wpixels, ImgHt, 1, NewImage.FILL_BLACK)
		prop = proImg.getProcessor()
		pixnum = prop. getPixelCount()
		r = zeros(pixnum, 'b')
		g = zeros(pixnum, 'b')
		b = zeros(pixnum, 'b')
		prop.getRGB(r,g,b) #split image into three byte arrays r, g, and b for processing
		correctPixel(r,wpixels,ImgHt,0,(wpixels-1),tPSI) # modifies only first column (0)
		correctPixel(g,wpixels,ImgHt,0,(wpixels-1),tPSI)
		correctPixel(b,wpixels,ImgHt,0,(wpixels-1),tPSI)
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
		#imp_template = WindowManager.getCurrentImage()	
		IJ.makeRectangle(0, 0, 1920, 1080)
		#print 'title',imp_temp.getTitle(), 'image ID',imp_temp.getID()
		IJ.run("Copy") #really kludgy, but nothing else seemed to work
		IJ.run("Internal Clipboard")		
		imp_temp.close()
		
		imp_template = WindowManager.getCurrentImage()		
		
		imp_template.setTitle("template")
		#if indx==9: sys.exit()
		#print 'title',imp_template.getTitle(), 'image ID',imp_template.getID()
		t_ID = imp_template.getID() # ID will be used to close if changed; is a negative value
		imp_template.show()

		#How to rename a slice - setMetadata("Label", string)
	
	sip = imp.getProcessor().duplicate()  
	simp = ImagePlus("ASlice", sip)
	simp.show()
	
	#ASlice is already waiting
	IJ.run(simp, "Calculator Plus", "i1=ASlice i2=template operation=[Add: i2 = (i1+i2) x k1 + k2] k1=1 k2=0 create")
	
	#result file of calc.
	corImg = WindowManager.getCurrentImage()
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
	ax=WindowManager.getCurrentWindow()
	
	try :
		#print ax.getTitle()#'NoneType' object has no attribute 'getTitle'
		ax.close()
	except AttributeError, err1: 
		time.sleep(0.200)
		ax=WindowManager.getCurrentWindow()
		ax.close()
	print 'frames done:',count-1
print 'stack2 size', stack2.getSize()
for list1 in range(1,count+1):
	print 'stack2 file name', stack2.getFileName(list1)

ImagePlus("stack2",stack2).show()
IJ.selectWindow("stack2")

IJ.run("Input/Output...", "jpeg=90 gif=-1 file=.txt use_file copy_row save_column save_row")
AVI_file_out = "stack2.avi"
avi_Out = avi_outpath+AVI_file_out
#no common program I have reads this, including irfanview, or vitualdub64,use jpeg compression.
#IJ.run("AVI... ", "compression=PNG frame=30 save=["+avi_Out+"]") 
IJ.run("AVI... ", "compression=JPEG frame=30 save=["+avi_Out+"]")
#imp_template.close()	
#WindowManager.getCurrentWindow()
stoptime = time.time()
print 'Elapsed time to process '+str(count-1)+" frames: "+ str((starttime-stoptime)/60)+' min.'
#for checking purposes set plot profile measuring orientation to verical and set an ROI
IJ.run("Profile Plot Options...", "width=450 height=200 minimum=0 maximum=0 vertical interpolate draw")
IJ.makeRectangle(lftPt, topPt, ImgWidth, ImgHt)
print "Done"
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

