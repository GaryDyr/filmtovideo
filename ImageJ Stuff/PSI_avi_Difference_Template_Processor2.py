#PSI_avi_Leader_Template_Processor.py
#Python code to find the projector shutter Image (PSI) center position on 
#video frames in an AVI file. 
# code is based on Fiji implementation, which uses Python 2.5 and ImageJ 1.49
#This code process and its content is copyright of Gary Dyrkacz and survivors. All rights reserved.
#It may be freely used for non commercial use only, without the author's permission. 
#Author: Gary Dyrkacz
#email: dyrgcmn@comcast.net
#date: 9/24/2012
#Last update: 03/06/2015

#Fiji-ImageJ does not recognize latesst Python print function change using
#paranthesis and does not allow numpy package, which would simply the matrix
#code substantially.

#Requies: 
# 	A csv file of two connected mormalized PSI profiles  (2 x wavelength)
	# Default file name: "PSI_norm_1358.csv"
#AND

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
from collections import deque
from itertools import *
import csv
import operator
import os
from math import sqrt
import csv
import sys
from ij.process import ImageStatistics as IS  
from math import sqrt
import thread
import time
from ij.io import OpenDialog
from ij.gui import GenericDialog 
import ij.VirtualStack # added June, 2014 to satisfy ImageJ2
from ij.plugin import AVI_Reader #  had to add n ImageJ2 code after looking at java class code
from ij.gui import ProfilePlot # had to add in ImageJ2


DriveOption = "F"

if DriveOption == "C":
	default_drivepath = "C:\\" 
elif DriveOption == "F":
	default_drivepath = "F:\\Canon\\"

default_path = default_drivepath+"ImageJ Stuff\\" # use forward slashes or 2 back slashes for these
templating_files = default_drivepath+"templating_files\\"
image_path = default_drivepath+"imagedump\\"
avi_inpath = default_drivepath+"avi_in\\"
avi_outpath = default_drivepath+"avi_out\\"

#+++++++++PARAMETERS SETTINGS - SET ALL PARAMETERS HERE+++++++++++++++++++++++++++++++
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

PSIf = templating_files+"PSI_2frame_diff_1358.csv"

nstart = 1 # starting frame frame labeled "1" is actually indexed at 0 
interval =10 			# row spacing between successive points; 1 = every row
slicecutter = 1			# slices to skip
#CRITICAL INFO THAT MUST BE SUPPLIED FROM OTHER METHODS
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
PSIWidth = 1358			# width of the normalized PSI
NewWidth = 1358
RunningWidth = 1313
B1 = 1166.910722		#Blanking interval obtained from rotating camcorder info
MovAvgRng = 18			#moving average range or chunk size to use for calculating PSIWidth moving average
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
ImgHt = 1080
ImgWidth = 1920
csize = 1320			# default row size of the vertical resolution, e.g., 1080, to account for compression or expansion of PSI
topPt =60		#0	    # top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240			    # left point of video frame that is the left edge of the Plot Profile measurement rectangle in ImageJ
botPt = 1020 #1080  	# bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680        	# right point of video frame that is the right edge of the Plot Profile measurement rectangle in ImageJ
IBase = 255
#TRIGGERS
renormPSI = True 		# True: Use the RunningWidth instead of standard 1358 width as starting PSIwidth
# Center_Correct should on be changed to False with great caution. The low numbers are very badly off and will yld
# frames with a lot of PSI subtractoin artifacts.
Center_Correct  = True #Correct the 0-400 Centers for bad center correlation; uses a 3 pt moving average.
BlurFilter = False	    # Use Gaussian Blur Filter to remove high frequency variation. Huge performance hit if true
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#Frame Luminance correction coefficients for 4th order eqn
n4 = 5.74692e-11	
n3 = -2.36532e-07	
n2 = 0.000298942	
n1 = -0.117250047	
n0 = 126.2787364	
AverNum = 121.133	

#define full frame size, which is our terms is visual frame and blankframe size in rows
HB = ImgHt + B1

print default_path

# os.chdir(default_path) errors out???? but used to work
d1 = os.getcwd()  
print d1

#Excel stores numbers in a csv file without quotes, with a comma as separator
#using the QUOTE_NUMERIC parameter converts to a float value internal to reader
#uaing 'with' is apparently safer code for cleanup on exceptions
#but next line not available in 2.5?? gives error about new keyword in 2.6
#with open(default_path+PSIf) as f:
	#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
#	PSI = [x[0] for x in csv.reader(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 

#print PSIf
#open(PSIf) as f:
#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
#PSI = [x[0] for x in csv.reader(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
PSI = [x[0] for x in csv.reader(open(PSIf), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
print'rows read:',len(PSI)
#print 'PSI',PSI

#Check for existing template before generating one.
corrPSIf = "PSI_2frame_diff_n"+str(interval)+"_w"+str(PSIWidth)+".csv"

starttime = time.time()
#Read in only the intervals/rows that are to be used to obtain the corr. coeff.
sPSI = PSI[0:len(PSI):interval] #this still covers 2*PSI cycles but at subset of rows defined by interval
print'Subset of rows/frame to analyze:',len(sPSI)

# EITHER INTERPOLATE PSIWidth TO NEW WIDTH ,OR LEAVE AS STANDARD PSIWIDTH, and store i rows offset by 1 in each column

 #++++++++++++++START INTER+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
NewWidth = RunningWidth
#To compensate for when the inevitable frequency shift occurs we will calculate a LARGER range than necessary
#by 240 rows or 1320 instead of 1080. This gives about 18% margin to play with.
MaxPSIrows = csize
template=[]
#Renormalize or resize, then interpolate the PSI to a new range, if different than current.
#The new width/intervals is the number of columns that will be required based on the row skip we decide
#At an interval of 1 this is just be the width of the new PSI.
#The required rows are dictated by the interval as well, but the basis for selection
#is limited by the frame height, which in the current case is 1080 + an overage factor.
OldWidth = PSIWidth
xNewSize = int(round(NewWidth / interval)) 		#number of columns to generate
Rowrng = int(round(MaxPSIrows / interval,0))  #number of rows to generate
#The values in the PSIy array are cut in at intervals of total row range/interval over the extra range (1320)
#Generate new fraction widths,
#original non reduced size of rows in PSI_Template =(1358)
#Read each column row of data into an array and deal with rescaling.
#++++++++++++++++++++REMAP THE PROFILE TO NEW WIDTH+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#Resize the old data range at intervals into the new compressed range
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#We will generate a template, PSIWidth/interval columns wide and full frame height + extra rows long.
#the range represents 2 PSI cycles, so full PSI width's row stream shifted by column and rows by PSIWidth/interval
# is samples over the range 0 to PSIwidth-1. The final 2D template thus will represent a matrix of PSIwidth/interval columns
#and 1080/interval rows of the new profile rgb values

for i in range(xNewSize): 
	if renormPSI: # should we renormalize data or just use the standard PSIWidth
		#Set up new x intervals and fractions between rows
		#sPSI is the template image vector already set to proper interval sequence.
		if NewWidth > OldWidth:
		#Tproblem if NewWidth > OldWidth, so first expand PSI by expanding sPSI, if needed.
			sPSI.extend(sPSI[0:(NewWidth-OldWidth+1)])
			OldWidth = len(sPSI)
		
		xfactor=float(NewWidth)/float(OldWidth) #must convert int-> float or produces only 0
		xoldrows = [x for x in range(0,PSIWidth,interval)]
		xfractionrows = [x*xfactor for x in xoldrows] 
		#generate new x integer array to be interpolated by the fractional x list
		xnew = [x for x in range(0,NewWidth,interval)] 
		#The PSI RGB values are now mapped 1:1 to the new fractional x values.
		#These fractional (float) x values are inconvenient; interpolate to set of integer values that 
		#cover the new PSI width at the same interval size. 
		#We set up the integer scale to run from 0 to newMax and interpolate the desired integer 
		#between each fractional x,y pair. Do linear interpolation: Y=Y1+(X-X1)(Y2-Y1)/(X2-X1)
		#The difference between fractional intervals is uniform, pre-calc:
		xfractiondif = xfractionrows[1]-xfractionrows[0] # =(X2-X1) below
		#INTERPOLATION LOOP - FIX THE PSI RGB VALUES 
		#THIS FIXES ALL THE VALUES, BUT ALL WE WILL USE IS A RANGE OF THESE BASED ON
		#topPt and botPt
		#There is an interpolation function in numpy and scipy, but alas, not yet allowed in Fiji
		#generate a row of template data; 
		PSInew =[]*xNewSize
		#runs over each row of a PSI width range, but in reverse. Thus, when we use the template against
		#a vertical slice of a frame, we will be "moving" from the center peak forward along the 
		#template searching for the maximum (actually nextminimum or central row value on that frame)
		nPSI = len(sPSI)
		meanx = [0]*xNewSize
		#Generate two lists one index off from each other and get difference between lists
		#the next operation also slices sPSI down to the width we want
		sPSIy1 = sPSI[nPSI-xNewSize-i-1:nPSI-i-1] 
		sPSIy2 = sPSI[nPSI-xNewSize-i:nPSI-i]
		ydif = [(x - y) for x,y in zip(sPSIy2,sPSIy1)] # =(Y2-Y1)
		#Each x value in the xfractionrows needs to be subtracted from the nearest integer.
		#In turn, that integer value was already formed from the index number by multiplying by the interval
		xndif = [(x - int(y)) for x,y in zip(xfractionrows,xfractionrows)] #X-X(nearest int)
		#Put the interpolation lists together to get the new PSI values
		#Not sure if this is any faster than just referencing individual elements
		yOVERx = [(x/xfractiondif) for x in ydif]	 #(Y2-Y1)/(X2-X1)
		Addy = [(x*y) for x,y in zip(xndif,yOVERx)]  #(X-X1)(Y2-Y1)/(X2-X1)
		#Need to normalize each row to a baseline.
		#The baseline depends on the highest value of the PSI
		PSIy = [(x+y) for x,y in zip(sPSIy1,Addy)] 	 #Y1+(X-X1)(Y2-Y1)/(X2-X1)
		#PSIy is now an expanded or condensed row of PSI values at row intervals and column row intervals of 1
	else: #will not adjust PSI
		PSIy = sPSI[i:len(sPSI)+i] # no correction needed, already at 255 level also.

	template.append(PSIy) #add whatever we did or did not do to sPSI to  2D template
#++++++++++END INTERPOLATION OF ROWS TO NEW PSI AND/OR FULL 2D TEMPLATE AT INTERVAL ROWS++++++++++++++++++++++

#note how this is saved; the format is specific so that we can recall a template later if the 
#interval and width are the same.
#Each colomn in template of rows, each row differing by interval number of rows. There are 
#2*RunningWidth/inteval number of rows in each column. First point and all subsequent points
#in each column are offset by the interval number from the previous column.
#Because each column is offset, each 1080/interval set of points represents a potential
#match for a PSI difference spectrum. Thus, we only need to keep 1080/interval rows of these col sets
del template[ImgHt/interval+1:len(template)]
corrPSIf = "PSI_2frame_diff_n"+str(interval)+"_w"+str(NewWidth)+".csv"
corrpath = templating_files+corrPSIf
print 'Interpreting template file name: n## is the interval between points; w#### is the width of the PSI'
#with open(corrpath,'w', newline='') as f: 'newline must be used in >3.2 and windows
f = open(corrpath,'w') #, newline='')
writeout = csv.writer(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n') 
#print 'template', template
print 'template file saved as:',corrpath
for row in template:
	writeout.writerow(row)
f.close() #will not be needed >2.5Ver

#Change newWidth to the PSIWidth now that resampling and resizing is done.
PSIWidth = NewWidth

#alternate method when Fiji and 64 bit Pyhton catch up with numpy; loadtxt is a numpy function
#PSI = numpy.loadtxt(open(PSIf,"r"),delimiter=",",skiprows=0, dtype=int)

# get the new PSI 
allowed_intervals = []
n=int((botPt-topPt)/interval)

if ((botPt-topPt) % interval !=0):
	allowed_intervals = [x for x in range(botPt-topPt) if ((botPt-topPt) % x !=0)] 
	print "Bad interval choice - aborting; allowed values are: ", allowed_intervals
 	sys.exit()

"""
Calculate the Pearson coefficients for the sPSI vector
The Pearson coefficient method used is that described in: 
http://fiji.lbl.gov/mediawiki/phase3/index.php/Integral_Image_Filters
This method has the advantage of avoiding calculating the averages, which require slow division operation.
We have a vector DiffPSI that is a subset of the 2*PSIwidth PSI. We extract the ROI in the image at the same interval 
width used for DiffPSI which will be the same for the PSIwidth and do an extracted sPSI row by rextracted image 
row Pearson correlation (pcc list). We then determine the largest correlation value of the list, from which we determine 
where the PSI center is for each slice. The Pearson code is mostly based on  the file: 
pearson.py; Author: Ernesto P. Adorio, PhD.; UPDEPP, at Clarkfield, Pampanga ;Version   0.0.1 Oct. 1, 
2011. also see viola jones technique, but works for geatured whereobject id mosthly in the frame
Formula is:
r = (n*S(xiyi) - S(xi)S(yi))/(sqrt(n*(S(x))^2 -S(x^2))(sqrt(n*(S(y))^2 -S(y^2)), where S = sum; n is the number of rows
x is the calculated rgb values and y is the observed frame rgb values for each row.
r will be between -1 and 1.
"""
# Calculate the sums for the existing sub PSI sections. For every comparison of the subset 
# image vector along the PSI templates vectors we need to calculate: a sum(xi*yi ), 
#sum(xi) (sum(x))^2 and sum(x^2). Speed up process by pre-calculating the latter three terms 
#for every interval and placing  in arrays. If necessary we can speed it up even more by doing
#the calculation in a separate python program, and just read the data in.

#A template contains all the PSI difference luminances related to the PSI differences of size newWith.
#A completely new template is created from this template that has all the sums that will be used for 
#the Pearson correlations

#n = int(ImgHt/interval) for full frame analysis
n = int((botPt - topPt)/interval) # number of rows to grab & sum to correlate with video values. 
np= int(RunningWidth/interval) #number of PSI's that will be in interval set.
print 'np:', np
print 'rows per frame used',n

#Pre-calculate the Sum(x) and sqrt(n*(Sum(x))^2 -(sum(x^2)) terms to improve run time. 
#The sums are calculated over the same size that is dictated by interval used to obtain 
#the sub profile list. The results are lists of sums that will be used with each profile point.
sumx = [0]*(np-1)
sumxsq = [0]*(np-1) # set the array for sumxsq; this is ok for 1D vector
sumprodxy = [0]*(np-1)
meanx = [0]*(np-1)

#template has a value of ImgHt rows, but we are only concerned about the rows in
#the region of the frame we will compare (n), so remove extraneous rows.
#Because the rows are position dependent on the luminance correction, must remove
#from top and bottom
del template[int(botPt/interval):len(template)]	
del template[0:int(topPt/interval)]

#template consists of PSI/interval columns. Each row in a column represents a luminance shifted
#value locked to its row position in the frame. We will sum down each column, which covers the 
#entire frame height region....
#python is not really 2D array/list friendly when it comes to columns(outside of numpy). We
#invert the data to convert columns to rows using list(zip(*template). 
t2 = list(zip(*template)) # The PSI's are now located in rows.
meanx = [sum(x)/n for x in t2] #checked OK
#print 'meanx', meanx

def doBlur():
	#how this is really working is a bit fuzzy (hmmm, pun), but result suggest probably working. We run blur, but on what? 
	#PlotProfile is a gui class process and is looking for an ImagePlus, but I do not need to close the image after
	#getting profile. What is consuming the smooth ROI image?
	#At any rate, the image does show blurring, and I believe the profile is being correctly 
	#read off the blurred ROI.		
	#AVI file read only, must duplicate to use blur
	#get the current slice
	image = WindowManager.getCurrentImage()
	dimage = image.createImagePlus() #this does not generate a new image only the attributes of the chosen image.
	#ip = image.getProcessor() # these 2 lines also worked instead of previous. Why? maybe because processor contains rgb values?
	#1ip2 = ip.duplicate();
	#test stuff -works and shows orig file as old.png
	#sliceFileName = default_path+"orig.png"  
	#ip = image.getProcessor() 'gets processor from current slice
	#im =ImagePlus('one',ip)    'creates a new (duplicate) ImagePlus titled 'one'
	#FileSaver(im).saveAsPng(sliceFileName)    'saves the new image, which is just the slice
	#im2 = WindowManager.getCurrentImage() gets current image on stack which 
	#test stuff end 
	IJ.run("Gaussian Blur...", "sigma=5 slice")
	dimage = WindowManager.getCurrentImage()
	#more test stuff - works and shows blurred file as new.png
	#ip = dimage.getProcessor()
	#sliceFileName = default_path+"new.png"   
	#FileSaver(dimage).saveAsPng(sliceFileName)    
	#test stuff end
	profile = ProfilePlot(dimage, True)	
	Prof = profile.getProfile()
	return Prof

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#NOW WORK THE IMAGES.
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# set the profile plot options before starting
#Although vertical measurement is supposedly set here; it really is only useful for any manual 
#verification and manipulation. The call to generate a profile does not "listen" 
#to "Profile Plot Options..." settings. ProfilePlot overrides with its own default.
IJ.run("Profile Plot Options...", "width=450 height=200 minimum=0 maximum=0 vertical interpolate draw")

#this would specify image range to open in AVI file
#next line opens AVI file; "use" indicates use virtual stack, convert means convert to grey scale.
#imp = IJ.run("AVI...", "select=[C:\\Canon\\Projector Leader Tests 100 hotspot 267 657 102111 .avi] use convert")

#optional code that opens up dialog to choose file and input parameters; not good when testing
#imp = IJ.run("AVI...", "") #opens up dialog to choose avi file

# with the kind help of Wayne Rasband, 1>47j will open the
#avi stack for reading the slices etc' but in June, 2014 had to explicitly add 'from ij.plugin import AVI_Reader
#imp = AVI_Reader.openVirtual(["C:\\Canon\\Projector Leader Tests 100 hotspot 267 657 102111 .avi"]); 
#print "size="+imp.getStackSize(); 
#mp.show(); path = "C:\\Canon\\Projector Leader Tests 100 hotspot 267 657 102111 .avi" 


avi_file = OpenDialog("Choose the avi file", None)   
filename = avi_file.getFileName()   
if filename is None:   
	print "User canceled the dialog!"  
	sys.exit()
else:   
	directory = avi_file.getDirectory()   
	avi_filepath = directory + filename   
	print "Selected file path:", avi_filepath   

(file_name, file_ext) = os.path.splitext(filename) 
print file_name
#Produce name of centers file; Get corresponding centers file (
CentersPath = avi_inpath+"Cntrs_"+file_name+".csv"

#READ IN AVI FILE
stack = AVI_Reader.openVirtual(avi_filepath)
print "frames in stack=", stack.getStackSize() 
stack.show() 
AllSlices = stack.getStackSize()

#Future reference: Virtual stack is read only, if need to manipulate it, duplicate it.
maxslices = int((AllSlices-nstart)/slicecutter)
print 'max. # of slices to analyze', maxslices
#pre-calc the camcorder total row cycle vert.blanking region + video frame height
Ftotrows = B1+ImgHt
#set up lists
SliceNum = [0]*(maxslices+1)
PSICenter = [0]*(maxslices+1)
PSIraw=[0]*(maxslices+1)
PSIw=[0]*(maxslices+1)
PSICntrPred=[0]*(maxslices+1)
PSIMovAvg=[0]*(maxslices+1)
pccmax=[0]*(maxslices+1)
PSIFramePos=[0]*(maxslices+1) #needed to calculate pn jump between frames
PSINewWidth=[0]*(maxslices+1) #needed to calculate pn jump between frames
FrameLumCor = [0]*(maxslices+1) #luminance correction amount for entire frame
pn=[0]*(maxslices+1)
scaler = [0]*(np-1)
kk = 0
#++++++++++++++++++++++++++++++++++++++
#NOTE THAT IN THIS SPECIFIC CASE RIGHT NOW WE ARE SKIPPING FIRST FRAME BECAUSE IT 
#IS NOT A VALID MOVIE FRAME, JUST A HEADER TO INDICATE 100s
#change the range from 2 back to 1 for real data.
#++++++++++++++++++++++++++++++++++++++++
#must create a second template to hold adjusted grey values
t3 = list(zip(*template))

#For each pair of adjacent slice differences, calculate all the possible pcc values
#slicecutter is set in variables list at beginning of script.
#loop is a bit messy. The stack index starts with frame 1, not zero,
for k in range(nstart,AllSlices-1,slicecutter): 
  # get the first frame rgb average profile
	imp1 = IJ.getImage()
	#print '---------'+str(imp)+'slice'+str(k)+'-----------'
  	#				x lft	ytop	rect width	 rect height
	IJ.makeRectangle(lftPt, topPt, (rtPt-lftPt), (botPt-topPt))
	profile = ProfilePlot(imp1, True) # The Boolean is for vertical or horiz. "True" = vertical
	#if BurFilter set, blur image a bit to reduce outlyer speckling
	if BlurFilter:
		Prof = doBlur #Do Gaussian Blur on single image
	else:
		Prof = profile.getProfile()

	sProf1 = Prof[::interval]
	 # get the next frame rgb average profile 
	IJ.setSlice(k+1)
	imp2 = IJ.getImage()
	IJ.makeRectangle(lftPt, topPt, (rtPt-lftPt), (botPt-topPt))
	profile = ProfilePlot(imp2, True) # The Boolean is for vertical or horiz. "True" = vertical
	if BlurFilter:	
		Prof = doBlur #Do Gaussian Blur on single image
	else:
		Prof = profile.getProfile()
		
	sProf2 = Prof[::interval]  
	#print 'sProf1',sProf1 
 	#print 'sProf2', sProf2
 	#get difference between the two adjacent images profiles
	DiffProf = [a - b for a,b in zip(sProf2,sProf1)]
	RectHt = len(sProf1) # this is also the rectangle y limits
 	DiffProf = [float(i) for i in DiffProf]
	#Intensity scaling considerations to promote a better fit between the template and image profiles
	# MAY NEED TO FIX THIS SCALAR. MEANX IS THE VALUE OF THE TEMPLATE, BUT THIS WILL NOW BE CLOSE TO
	#ZERO IN MANY CASES. SHOULD I BE SCALING INTENSITIES NOT MEAN VALUES
	meany = sum(DiffProf)/len(DiffProf)
	scaler = [x-meany for x in meanx]
	#print 'scaler', scaler
	#print 'np:', np
	for i in range(np-1): #run over PSIwidth intervals range
		t3[i] = [x-scaler[i] for x in t2[i]]
	#We now get all the pcc s "at once" using the previous template of partially calculated parameters
	#get various pcc eqn sum values
	#get sum of values
	for i in range(np-1):
		sumx[i] = sum([x for x in t3[i]]) # a list of S(x) for of each n rows (corrected sPSI) 

	#get sum(x^2) for each row position i
	for i in range(np-1):
		sumxsq[i]=sum([x*y for x,y in zip(t3[i],t3[i])]) #(sum(x^2))sum the product of xi.xi of each xi block list by itself

	denx1 = [x*y for x,y in zip(sumx,sumx)] #(Sum(x))^2 
	denx2 = [x*n for x in sumxsq] #n*(Sum(x))^2
	denomx = [a - b for a, b in zip(denx2, denx1)] #n*(Sum(x))^2 -sum(x^2)
	denomx = [sqrt(i) for i in denomx] #sqrt(n*(Sum(x))^2 -(sum(x^2))
	#GET PROFILE SUMS
	sumy = sum(DiffProf)
	#print 'sumy',sumy
	sumysq = sum([x*y for x,y in zip(DiffProf,DiffProf)]) #(sum(y^2)
	deny1 = sumy**2
	deny2 = sumysq*n 
	denomy = sqrt(deny2-deny1) #[a - b for a, b in zip(deny2, deny1)] 
	if denomy == 0:
		IJ.showMessage("Slice "+str(k)+" and slice "+str(k+1)+"are duplicate frames. Cannot continue process. Remove one of the frames.")
		sys.exit()
	denom =[denomy*x for x in denomx] #denom product of x sums and y at each point up to PSIWidth/interval
	#print 'denom', denom
	#get PCC numerator cross terms over all PSI interval rows
	for i in range(np-1):
	# calc sub block for elements to be summed for sumprodxy
		e1 = t3[i] #e1 just intermediate list; could not figure list comprehension out
		sumprodxy[i] = sum((x*y) for x,y in zip(e1,DiffProf)) #S(xiyi) 

	nsumprodxy = [y*n for y in sumprodxy] #n*S(xiyi)
	# multiply the sums of each current sProf vector by each sum of sPSIvector.
	sumxy = [(sumy*x) for x in sumx] #S(xi)S(yi)
	num = [a - b for a,b in zip(nsumprodxy,sumxy)] #n*S(xiyi) - S(xi)S(yi)

	#Put it all together to get corr. coef. vectors
	pcc = [a/b for a,b in zip(num, denom)] 
	#print 'pcc',pcc # this line used during testing 
	maxr =  max(pcc) # max Pearson Corr. Coef.; supposedly PSI peak
	if maxr< 0.60:
		print 'slice:'+str(k)+'; WARNING: UNRELIABLE POSITION; CORR. COEFF < 0.6' 
	rindex =pcc.index(max(pcc)) #finds the index of maxr; not the fastest code though
	#Convert the index position to a peak position on some frame.)
	#note that maxr may be in restricted profile rectangle on the video frame, so must take
	#into account that zero is measured from inside the rectangle with row index 0, which is 
	#really topPt rows into the frame. index*interval gives the shift of PSI from the "whitest" 
   	#position of the PSI. Also, we "move" the comparison such that the whitest point moves up the frame
   	#and ultimately to a negative position relative to the current fame. If a peak was at the topPt, 
   	#the whiteest point, relative to frame 0, f(0) is at -index*interval  + topPt,.e.g. if PSI width
   	#=1358 and the peak centers on topPt, then the whiteest point is at  -(index*interval) + topPt.
   	#The peak is then at PSI/2 -(index*interval) + topPt. In addition, if any peak value is more negative
   	#than this value, it means the pk is "inside" the previous vertical blanking region and we need 
   	#to jump to the next peak.

   	#Given the frame find the relative position of the peak "valley" with respect to the frame.
   	#Note this is presented as a positive number, but is actually negative with respect to the frame.
	PSIraw[kk] = rindex*(interval)
	pccmax[kk] = maxr
	#print 'raw center:',PSIraw[kk]
	#Find position of the PSI center. topPt is the offset if used
	PSICenter[kk] = PSIraw[kk]
	#this is weird, and must have to do with how the difference PSI profile is generated,
	#but the slice that ends up being analyzed here starts with 2 NOT 1. Slice 1 is therefore lost.
	#so slicenum[0] is actually slice 2 data, not slice 1
	#All other programs should use the slicenumber in column 0 as the reference.
	SliceNum[kk] = k+1 # frame number
		
	#When values are within about 89 units of 0th row, the peak finder may
	#find a peak that is either before or after the zero point. Thus, around zero rows the values 
	#can jump from either valuss such as 1279 (close to a peak width value to say 64. In terms of 
	#running position this is not a problem, only absolute position is affected.
	#There is no real correction for this issue, but it does adveraely affect the PSI widths calculated below.
	#see Validation of PSI_avi_Processor.xlsx [Optimum factors Lum corrected] for details.
	
	# Clearly, if a position is greater than the PSI width it means the peak finder missed the first peak, but 
	#did find a second, but what should be the width to use to jump back to the first point.
	#In addition, a problem can develop if two peaks values are both off from the expected, 
	#Although dangerous to use an average if the projector is not holding fps steady,
	#it can be worse if the widths lead to big errors. Try using average value, which is really found
	#after the fact MAY NEED TO CHANGE THAT).
	if PSICenter[kk] > NewWidth:
		PSICenter[kk] = PSICenter[kk] - NewWidth
	PSIFramePos[kk]= k*Ftotrows + PSICenter[kk] #frame number x total frame rows H+B1
	#get the PSI number from start, only sensible for slicecutter = 1.
	if slicecutter == 1:
		if k==nstart:
			PSIw[kk] = int(PSIWidth) #RPSIWidth was replaced by RunningWidth ...NewWidth
			pn[kk] = 1 #  PSI jump
		if k > nstart:
			PSIw[kk] = int(PSIFramePos[kk]-PSIFramePos[kk-1])
			if PSIw[kk] < 2000:
				pn[kk] = 1
			else: #must be two
				PSIw[kk] = int(PSIw[kk]/2)
				pn[kk]=2
		else:
			PSIw[kk] = RunningWidth
	
	#The current stream value needs to be compared not to the frame, but PSI index number.
	#Generate the PSI cycle number from the frame number
	nrel = k-nstart
	kk+=1
	#sys.exit() # Used during code testing to stop excution at first frame 

# if true correct PSI center if between 0-400 by using a three point moving average.
MaxCenters = len(PSICenter)
if Center_Correct:
	PSICntrPred[0] = PSICenter[0]
	PSICntrPred[MaxCenters-2] = PSICenter[MaxCenters-2]
	PSICntrPred[MaxCenters-1] = PSICenter[MaxCenters-1]
	for k in range(1,MaxCenters - 3):	
		if PSICenter[kk] < 400:
			PSINewWidth[k] = ((PSICenter[k+1] - PSICenter[k-1]) + HB*(SliceNum[k+1]-SliceNum[k-1]))/(pn[k] + pn[k+1])
			PSICntrPred[k] = int(PSICenter[k-1] +pn[k]*PSINewWidth[k] - HB)
			PSINewWidth[k] = int(PSINewWidth[k])
			#PSICntrPred[k] = int(PSICenter[k-1] +(pn[k]*((PSICenter[k+1] - PSICenter[k-1]) + HB*(SliceNum[k+1]-SliceNum[k-1]))/(pn[k] + pn[k+1])) -HB)
		else:
			PSICntrPred[k] = PSICenter[k]
			PSINewWidth[k] = PSIw[k]
		#Need to do a final check on PSICenter after correction, because will isolate PSI range based on std PSIwidth
		if PSICntrPred[k] > PSIWidth: PSICntrPred[k] = PSICntrPred[k] - PSIWidth
		if PSICntrPred[k] < 0: PSICntrPred[k] = int(PSICntrPred[k] + PSINewWidth[k])

print 'Sub profile (sProf) list size:', RectHt
print'slices analyzed:', maxslices

# fcn to calculate a moving average of PSI; 
def moving_average(iterable, n):
#iterable is list of values to subject to moving average; n is the range of values, e.g., set to 18 to represent 1 second of film
#def moving_average(iterable, n=3):
    # moving_average([40, 30, 50, 46, 39, 44]) --> 40.0 42.0 45.0 43.0
    # http://en.wikipedia.org/wiki/Moving_average
    #deque is a specal type of list object optimized for fast appends and pops for infinite (unbounded) lists
    it = iter(iterable) #make an iterable out of the list
    d = deque(islice(it, n-1)) #slice the iterable n-1 because we will add a value
    d.appendleft(0)
    s = sum(d)
    for elem in it:
        s += elem - d.popleft()
        d.append(elem)
        #print list(d)
        yield int(s / n) #moving average

#calc moving average using new fixed values and fill in PSIMovAvg 
if len(PSINewWidth) > MovAvgRng:
	MovAvg =list(moving_average(PSINewWidth, MovAvgRng)) #intermediate list
	#print MovAvg
	#The last MovAvgRng, e.g. 18 values are suspect, so we will have to use last value generated
	
	for k in range(0,(len(PSIMovAvg) - MovAvgRng-2)):
		PSIMovAvg[k] = MovAvg [k]

	LastVal = len(MovAvg)-MovAvgRng -2	#trouble here; not sure of what value to use 
	for k in range(len(PSIMovAvg)-MovAvgRng -2,len(PSIMovAvg)):
	   PSIMovAvg[k] = int(PSIMovAvg[LastVal])

else: # slices less than MovAvgRng; aver what is there and use for all
	PSIAvg = sum(PSINewWidth)/len(PSINewWidth)
	for k in range(PSINewWidth):
	   PSIMovAvg[k] = int(PSIAvg)
#print MovAvg
#Prepare list of lists for output
#PSICenterOutput = [ [ 0 for i in range(3) ] for j in range(kk) ] 'another way

#Calculate General Frame Luminance correction
#5.74692E-11	4
#-2.36532E-07	3
#0.000298942	2
#-0.117250047	1
# 126.2787364	0

#These are not used, but are calculated anyway
for k in range(MaxCenters):
	FrameLumCor[k]	=AverNum - (n4*PSICenter[k]**4 + n3*PSICenter[k]**3 + n2*PSICenter[k]**2+ n1*PSICenter[k] + n0)


PSICenterOutput = []
PSICenterOutput.append(SliceNum)
PSICenterOutput.append(PSICenter)
PSICenterOutput.append(PSIraw)
PSICenterOutput.append(pccmax)
PSICenterOutput.append(pn)
PSICenterOutput.append(PSIw)
PSICenterOutput.append(PSICntrPred)
PSICenterOutput.append(PSINewWidth)
PSICenterOutput.append(PSIMovAvg)
PSICenterOutput.append(FrameLumCor)
print PSICenterOutput
PSICenterOutput =[list(i) for i in zip(*PSICenterOutput)] 
#the hdr is not printed now because of the way AVI_Processor uses zip function to get columns
#hdr = ['slice','cn','raw','pcc','pn','pw'] #note cryptic key for simple use with R
#cn = PSICenter - PSI center position relative to current slice or frame, 
#pw = PSIw->PSIWidth between frames; pcc = max value of Peason corr. coeff.
#pn = one or 2 PSIs between frames;
#open(CentersPath,'w', newline='') as f: 'newline must be used in >3.2 and windows
#PSICenterOutput.insert(0,hdr)

#Depending on slicecutter value, last row may not be filled. Need to check for deletion...
row_total = 0.0
if PSICenterOutput[len(PSICenterOutput)-1]:
	for x in PSICenterOutput[len(PSICenterOutput)-1]: 
		row_total += x
	if row_total==0:
	 	PSICenterOutput.pop(-1)
for row in PSICenterOutput:
	print row

f = open(CentersPath,'w') 
fout = csv.writer(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n' ) 
for row in PSICenterOutput:
	fout.writerow(row)
f.close()
print 'CSV file ['+CentersPath+'] holds the PSI Centers Data'
print 'csv format: '
print '            slice =	frame #;' 
print '            cn  = 	PSI center row;' 
print '            raw =    pattern recog. center (no corrections);'
print '            pcc =    maximmum Pearson Corr. Coeff. of found PSI center;'
print '            pn  =    number of PSI between last and current frame (pn will be zero if slice interval >1);'
print '            pw  =    PSI width/frame;'
print '            pcn =    predicted next center based on n+1 and n-1 for n width differences;' 
print '            pnw =    new width between predicted in n+1 and n-1 for n;'
print '            pma =    moving average width based on moving average chunk of ' + str(MovAvgRng) + ';'
print '            flc  =   frame luminance rgb correction value for entire frame;'
print ''
stoptime = time.time()
print  'Elapsed time to process '+str(maxslices)+'frames:'+ str((stoptime-starttime)/60)+' minutes'
#NOW GO TO R AND GET THE REGIMES USING THE CSV DATA SET
#NEXT OPERATION IF WE DID NOT HAVE TO DO THIS WOULD BE THE ACTUAL FRAME CORRECTION FILTER ON A 
#FRAME BY FRAME BASIS.
# WE WOULD FIRST INVERT THE VALUES OF THE TEMPLATE BEFORE DOOING THE OPERATION.
#GENERATE A MASK FOR THE FRAME AND SUBTRACT. HOW TO CREATE AN IMAGE MASK FROM A NUMBER SET?
