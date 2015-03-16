#PSI_avi_Leader_Template_Processor.py
#Python code to find the projector shutter Image (PSI) center position on 
#video frames in an AVI file. 
# code is based on Fiji implementation, which uses Python 2.5 and ImageJ 1.49
#This code process and its content is copyright of Gary Dyrkacz and survivors. All rights reserved.
#It may be freely used for non commercial use only, without the author's permission. 
#Author: Gary Dyrkacz
#email: dyrgcmn@comcast.net
#date: 9/24/2012
#Last update: 9/24/2012

#note avi code will need to be changed for 1.47 imagej code.
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
#from numpy import *

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

# for old third order corrections corrf = templating_files+"Frame_Luminance_Correction_Coef.csv"
#Data in corrf is arranged in column order of first five rows related to luminance max exponentional
#parameters and and last five rows to luminance min exponential parameters.
#Order in rows (columns) is Peak Position, Peak Height, Peak width at half height.

#Projector Leader Tests 100 hotspot 267 657 102111 .avi original leaders name, but renamed to simpler

#+++++++++PARAMETERS SETTINGS - SET ALL PARAMETERS HERE+++++++++++++++++++++++++++++++
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
corrf = templating_files+"Exp_Luminance_Correction_Coef.csv"
PSIf = templating_files+"PSI_norm_1358.csv"

nstart = 1 # starting frame to pick up only white leader frames PSIs 
interval =10 			# row spacing between successive points; 1 = every row
slicecutter = 1			# slices to skip
#CRITICAL INFO THAT MUST BE SUPPLIED FROM OTHER METHODS
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
PSIWidth = 1358			# width of the normalized PSI
NewWidth = 1358
RunningWidth = 1235
B1 = 1166.910722		#Blanking interval obtained from rotating camcorder info
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
ImgHt = 1080
ImgWidth = 1920
csize = 1320			# default row size of the vertical resolution, e.g., 1080, to account for compression of PSI
topPt =0 #60			# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240			# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020          	# bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680            	# rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ
IBase = 255
#TRIGGERS
CorrectLuminance = True 	# Use the base PSI or correct for the luminace and use the data.
corr_file = True		# Sets if 3rd order coefficients will be in a csv file (True) or are below.
BlurFilter = True		# Use Gaussian Blur Filter to remove high frequency variation. Huge performance hit if true

pksmax = [45.553,140.158,438.030,816.044,1031.389]
Htmax = [3.168,9.566,17.704,16.361,6.746]
sigmamax = [46.986,188.882,361.070,395.567,79.903]
pksmin = [-4.290,135.213,331.585,588.971,1079.422]
Htmin = [2.995,0.674,2.885,2.410,5.645]
sigmamin = [98.351,58.268,248.432,194.119,240.585]

zeromax = 105.8122484
zeromin = 57.12497667
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

print PSIf
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

print PSIf
#open(PSIf) as f:
#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
#PSI = [x[0] for x in csv.reader(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
PSI = [x[0] for x in csv.reader(open(PSIf), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
print'rows:',len(PSI)
#print 'PSI',PSI

#Check for existing template before generating one.
corrPSIf = "PSI_corr_n"+str(interval)+"_w"+str(PSIWidth)+".csv"

#Read the csv file containing max and min 3rd order equations parameters if they exist

#Read the csv file containing max and min exponential parameters, if we say exists.
#The order here is corr[r][c] where r is the row info for a Gaussian peak in 
#the column order [pk position, pk height, pk width at half height(FWHM).zero point (factor to add to peak sums to get back to original rgb value].
if corr_file: # Supplying file or building?
	#with open(default_path+corrf,'r') as f: python >2.5
	f = open(corrf,'r') #python 2.5
	corr = [x for x in csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)]
	f.close()
	#exand and invert corr to read values as rows.
	corr = zip(*corr)
	pksmax = corr[0][0:5]
	Htmax = corr[1][0:5]
	sigmamax = corr[2][0:5]
	zeromax = corr[3][0]
	pksmin = corr[0][5:10]
	Htmin = corr[1][5:10]
	sigmamin = corr[2][5:10]
	zeromin = corr[3][5]

#Convert the sigma values
#The 2*2*ln(2) in prelog calc comes from using the LFWHM value. 
#Solving a Gaussian for a 1/2 maximum peak value the width for 
#1/2 side is 2*ln2. For full peak range this is doubled to get 4*ln2. 
#See internet for details. 
prelog = -2.0*2.0*math.log(2)
sigmamax = [prelog/float(x)**2 for x in sigmamax]
sigmamin = [prelog/float(x)**2 for x in sigmamin]

#if a template file already exist with proper PSI width and interval use it:
templatef = [f for f in os.listdir(default_path) if f.startswith(corrPSIf)] 
print 'template file exists:', templatef, 'will be used'

starttime = time.time()
#TRUE PART NOT WORKING, CHECK LATER
if templatef == corrPSIf: 
	template = [x for x in csv.reader(open(default_path+templatef), dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 
	sPSI = PSI[0:len(PSI):interval] #this still covers 2*PSI cylces/intervals
	print('in templatef if...len of sPSI',len(sPSI))
	sys.exit()
else:
	#INTERPOLATE PSIWdth TO NEW RANGE IF DECLARED IN PARAMETER SETTINGS.
	#To compensate for when the inevitable frequency shift occurs we will calculate a LARGER range than necessary
	#by 240 rows or 1320 instead of 1080. This gives about 18% margin to play with.
	MaxPSIrows = csize
	template=[]
	#Renormalize or resize, then interpolate the PSI to a new range, if it is different than current.
	#FIrst resize the base PSI to the new size range and then fit to the third order equations.
	#Read in only the intervals/rows that are to be used to obtain the corr. coeff.
	sPSI = PSI[0:len(PSI):interval] #this still covers 2*PSI cycles but at subset defined by interval
	print'Subset of rows/frame to analyze:',len(sPSI)
	#The new width/intervals is the number of columns that will be required.
	#At an interval of 1 this is just be the width of the new PSI.
	#The required rows are dictated by the interval as well, but the basis for selection
	#is limited by the frame height, which in the current case is 1080 + an overage factor.
	OldWidth = PSIWidth
	xNewSize = int(round(NewWidth / interval)) 		#number of columns to generate
	Rowrng = int(round(MaxPSIrows / interval,0))  #number of rows to generate
	#The values in the PSIy array are cut in at intervals of total row range/interval over the extra range (1320)

	#Generate new fraction widths,
	#original non reduced size of rows in PSI_Template =(1320)
	#Read each column row of data into an array and deal with rescaling.
	#++++++++++++++++++++REMAP THE PROFILE TO NEW WIDTH+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	#Resize the old data range at intervals into the new compressed range
	#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	#We will generate a template, PSIWidth/interval columns wide and full frame height + extra rows long.
	#the range a represents 2 PSI cycles, so  full PSI width's row  stream shifted by column and rowa by PSIWidth/interval
	# is samples over the range 0 to PSIwidth-1. The final 2D template thus will represent a matrix of PSIwidth/interval columns
	#and 1080/interval rows of the new profile rgb values

	#Set up new x intervals and fractions between rows
	#There will be a problem if NewWidth > OldWidth, so first expand PSI by expanding sPSI, if needed.
	if NewWidth > OldWidth:
		sPSI.extend(sPSI[0:(NewWidth-OldWidth+1)])
		OldWidth = len(sPSI)
	xfactor=float(NewWidth)/float(OldWidth) #must convert int-> float or produces only 0
	xoldrows = [x for x in range(0,PSIWidth,interval)]
	xfractionrows = [x*xfactor for x in xoldrows] 
	#generate new x integer array to be interpolated by the fractional x list
	xnew = [x for x in range(0,NewWidth,interval)] 
	
	#The PSI RGB values are now mapped 1:1 to the new fractional x values.
	#These fractional x values are inconvenient; interpolate to a set of integer x values that 
	#cover the new PSI width at the same interval size. 
	#We set up the integer scale to run from 0 to newMax and interpolate the desired integer 
	#between each fractional x,y pair. Do linear interpolation: Y=Y1+(X-X1)(Y2-Y1)/(X2-X1)
	#The difference between fractional intervals is uniform, pre-calc:
	xfractiondif = xfractionrows[1]-xfractionrows[0] # =(X2-X1) below

	#INTERPOLATION LOOP -FIX THE PSI RGB VALUES 
	#THIS FIXES ALL THE VALUES, BUT ALL WE WILL USE IS A RANGE OF THESE BASED ON
	#topPt and botPt
	#There is an interpolation function in numpy and scipy, but alas, not yet allowed in Fiji
	#generate a row of template data; 
	PSInew =[]*xNewSize
	#runs over each row of a PSI width range, but in reverse. Thus, when we use the template against
	#a vertical slice of a frame, we will be "moving" from the center peak forward along the 
	#template searching for the maximum (actually next minimum or central row value on that frame)
	nPSI = len(sPSI)
	meanx = [0]*xNewSize

	for i in range(xNewSize): 
		#Generate two lists one index off from each other and get difference between lists
		#the next operation also slices sPSI down to the width we want
		sPSIy1 = sPSI[nPSI-xNewSize-i-1:nPSI-i-1]  # this also sliced the sPSI down to a single PSI cycle
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

		#PSIy is now an expanded or condensed row of PSI values
		#correct the the PSIy row for luminance distortion and add it to the template list
		#save cycles, do a row at a time, which varies col to col by jumps of size csize/interval
		#calct Imax,0 - Imin,0 term
		#value was found from subtracting the max and min fitted values from each other and averaging
		#see leader_profiles summary.xlsm [fit data] for how difference found.
		Ir0  = 61.32 #s105.4240946 
		#calc corrected PSI value for current row
		j=i*interval		
		if CorrectLuminance:
			Imaxr = 0.0
			Iminr = 0.0
			for n in range(5): #there are five exp to calc.
				Imaxr += Htmax[n] * math.exp(sigmamax[n] * (j - pksmax[n]) ** 2)
				Iminr += Htmin[n] * math.exp(sigmamin[n] * (j - pksmin[n]) ** 2)
				# pkSum = pkSum + Ht(i) * Exp(sigma(i) * (ws.Cells(FR + n, 1).Value - Peak(i)) ^ 2)
			#the exponentials are based on normalized max and min luminance curves that start at zero 
			#on the minimum of the set. Must re-add that minimum value back.
			Imaxr = Imaxr + zeromax 
			Iminr = Iminr + zeromin
			Idif = Imaxr - Iminr #Imax,r - Imin,r
			PSInew = [Imaxr + (((x - IBase) * Idif) / Ir0) for x in PSIy] # Imax,o-Imin,o from dif between Imax and Imin & 
			#correct profile to a white baseline
			Pnmax = 255-max(PSInew)
			PSInew = [Pnmax+x for x in PSInew]
			template.append(PSInew)
		else:
			template.append(PSIy) # no correction needed, already at 255 level also. 
			
#note how this is saved; the format is specific so that we can recall a template later if the 
#interval and width are the same.	
#Remove all but 1080/interval rows
del template[ImgHt/interval+1:len(template)]
print 'template length',len(template)
corrPSIf = "PSI_corr_n"+str(interval)+"_w"+str(NewWidth)+".csv"
corrpath = templating_files+corrPSIf
print 'template file saved as:',corrpath
print 'Iterpreting template file name: n## is the interval between points; w#### is the width of the PSI'
#with open(corrpath,'w', newline='') as f: 'newline must be used in >3.2 and windows
f = open(corrpath,'w') #, newline='')
writeout = csv.writer(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n') 
for row in template:
	writeout.writerow(row)
f.close() #will not be needed >2.5Ver
#sys.exit()
#Change newWidth to the PSIWidth now that all the resampling and resizing is done.
PSIWidth = NewWidth

#alternate method when Fiji and 64 bit Pyhton catch up with numpy; loadtxt is a numpy function
#PSI = numpy.loadtxt(open(PSIf,"r"),delimiter=",",skiprows=0, dtype=int)
allowed_intervals = []

#n=int(csize/interval)
n=int((botPt-topPt)/interval)

if ((botPt-topPt) % interval !=0):
	allowed_intervals = [x for x in range(botPt-topPt) if ((botPt-topPt) % x !=0)] 
	print "Bad interval choice - aborting; allowed values are: ", allowed_intervals
 	sys.exit()

"""
Calculate the Pearson coefficients for the sPSI vector
The pearson coeficient method used is that described in: 
http://fiji.lbl.gov/mediawiki/phase3/index.php/Integral_Image_Filters
This method has the advantage of avoiding calculating the averages, which require slow division operation.
We have a vector sPSI that is a subset of the 2*PSIwidth PSI. We extract the ROI in the image at the same interval 
width used for sPSI and do an extracted sPSI row by rextracted image row Pearson correlation (pcc list). We then determine the 
largest correlation value of the list, from which we determine where the PSI center is for each slice. The Pearson code is 
mostly based on  the file: pearson.py; Author: Ernesto P. Adorio, PhD.; UPDEPP, at Clarkfield, Pampanga ;Version   0.0.1 Oct. 1, 
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

#A template contains all the corrected PSI luminances related to the PSI of width newWith.
#A completely new template is created from this template that has all the sums

#n = int(ImgHt/interval) for full frame analysis
n = int((botPt - topPt)/interval) # number of rows to grab & sum to correlate with video values. 
np= int(PSIWidth/interval) #number of PSI's that will be in interval set.
print 'rows per frame used',n

#MAY ELIMINATE THE NEXT BUNCH OF LINES AND GO BACK TO ORIGINAL HOLD OUT

#Pre-calculate the Sum(x) and sqrt(n*(Sum(x))^2 -(sum(x^2)) terms to improve run time. 
#The sums are calcluated over the same size that is dictated by interval used to obtain 
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
#entire frame region....
#python is not really 2D array/list friendly when it comes to columns(outside of numpy). We
#invert tthe data to convert columns to rows using list(zip(*template). 
t2 = list(zip(*template)) # The PSI's are now located in rows.

meanx = [sum(x)/n for x in t2] #checked OK
#print 'meanx', meanx

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#NOW WORK THE IMAGES.
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# set the profile plot options before starting
#Although vertical meassurement is supposedly set here; it really is only useful for any manual 
#verification and manipulation. The call to generate a profile does not "listen" 
#to "Profile Plot Options..." setting. ProfilePlot overrides with its own default.
IJ.run("Profile Plot Options...", "width=450 height=200 minimum=0 maximum=0 vertical interpolate draw")

#this would specifiy image range to open in AVI file
#next line opens AVI file; "use" indicates use virtual stack, convert means convert to grey scale.
#imp = IJ.run("AVI...", "select=[C:\\Canon\\Projector Leader Tests 100 hotspot 267 657 102111 .avi] use convert")

#optional code tbat opens up dialog to choose file and input parameters; not good when testing
#imp = IJ.run("AVI...", "") #opens up dialog to choose avi file

# with the kind help of Wayne Rasband, this is the way > 1.47j will open the
#avi stack for reading the slices etc
##	imp = AVI_Reader.openVirtual(["C:\\Canon\\Projector Leader Tests 100 hotspot 267 657 102111 .avi"]); 
#	print "size="+imp.getStackSize(); 
#	imp.show(); path = "C:\\Canon\\Projector Leader Tests 100 hotspot 267 657 102111 .avi" 

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
#Produce name of centers fileGet corresponding centers file (
CentersPath = avi_inpath+"Cntrs_"+file_name+".csv"

#READ IN AVI FILE
#this works for 1.46 right now; creates an instance of AVI_Reader
reader = AVI_Reader() 

stack = reader.makeStack (avi_filepath, 1, 0, True, True, False) 
print "frames in stack=", stack.getSize() 
ImagePlus("stack", stack).show() 
AllSlices = stack.getSize()

#Furture reference. Virtual stack is read only, if need to manipulate it, duplicate it.

#this can get us image statistics
#The options variable is the bitwise-or combination of three different static fields 
#of the ImageStatistics class. The final options is an integer that has specific bits 
#set that indicate mean, median and min and max values.
#options = IS.MEAN | IS.MEDIAN | IS.MIN_MAX   
#stats = IS.getStatistics(ip, options, imp.getCalibration())   

#For each slice calculate all the possible pcc values
#slicecutter is set in variables list at beginning of script.

maxslices = int((AllSlices-nstart)/slicecutter)
print 'max. # of slices to analyze', maxslices
#pre-calc the camcorder total row cycle vert.blanking region + video frame height
Ftotrows = B1+ImgHt

#set up lists
PSICenter = [0]*(maxslices+1)
SliceNum = [0]*(maxslices+1)
PSIraw=[0]*(maxslices+1)
PSIw=[0]*(maxslices+1)
pccmax=[0]*(maxslices+1)
PSIFramePos=[0]*(maxslices+1) #needed to calculate pn jump between frames

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

for k in range(nstart,AllSlices,slicecutter): 
	IJ.setSlice(k); 
	imp = IJ.getImage()

	#print '---------'+str(imp)+'slice'+str(k)+'-----------'
  	#				x lft	ytop	rect width	 rect height
   	IJ.makeRectangle(lftPt, topPt, (rtPt-lftPt), (botPt-topPt))
 	#blur image a bit to reduce forefront 
 	if BlurFilter:	#Do Gaussian Blur on single image
		#how this is really working is a bit fuzzy, but result suggest probably working. We run blur, but on what? 
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
 	else:
 		profile = ProfilePlot(imp, True) # The Boolean is for vertical or horiz. "True" = vertical
		Prof =profile.getProfile()

	sProf = Prof[::interval]
	RectHt = len(sProf) # this is also the rectangle y limits
 	sProf = [float(i) for i in sProf]
	#Intensity scaling considerations to promote a better fit between the template and image profiles
	meany = sum(sProf)/len(sProf)
	scaler = [x-meany for x in meanx]
	#print 'scaler', scaler
	for i in range(np): #run over PSIwidth intervals range
		t3[i] = [x-scaler[i] for x in t2[i]]
	for p in t3:
		if p>255.0:
			p = 255.0
		elif p<0.0:
			p= 0.0 
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
	sumy = sum(sProf)
	sumysq = sum([x*y for x,y in zip(sProf,sProf)]) #(sum(y^2)
	deny1 = sumy**2
	deny2 = sumysq*n 
	denomy = sqrt(deny2-deny1) #[a - b for a, b in zip(deny2, deny1)] 
	denom =[denomy*x for x in denomx] #denom product of x sums and y at each point up to PSIWidth/interval
	#get PCC numerator cross terms over all PSI interval rows
	for i in range(np-1):
     	# calc sub block for elements to be summed for sumprodxy
		e1 = t3[i] #e1 just intermediate list; could not figure list comprehension out
		sumprodxy[i] = sum((x*y) for x,y in zip(e1,sProf)) #S(xiyi) 
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
	PSICenter[kk] = PSIraw[kk] + topPt
	SliceNum[kk] = k # frame number
		
	#When values are within about 89 units of 0th row, the peak finder may
	#find a peak that is either before or after the zero point. Thus, around zero rows the values 
	#can jump from either valuss such as 1279 (close to a peak width value to say 64. In terms of 
	#running position this is not a problem, only absolute position is affected.
	#There is no real correction for this issue, but it does adveraely affect the PSI widths calculated below.
	#see Validation of PSI_avi_Processor.xlsx [Optimum factors Lum corrected] for details.
	
	# Clearly, if a position is greater than the PSI width it means the peak finder missed the first peak, but 
	#did find a second, but what should be the width to use to jump back to the first point.
	# In addition, a problem can develop if two peaks values are both off from the expected, 
	#Although dangerous to use an average if the projector is not holding fps steady,
	#it can be worse if the widths lead to big errors. Try using average value, which is really found
	#after the fact MAY NEED TO CHANGE THAT).
	if PSICenter[kk] > PSIWidth:
		PSICenter[kk] -= RunningWidth
	
	PSIFramePos[kk]= k*Ftotrows + PSICenter[kk] #frame number x total frame rows H+B1
	#get the PSI number from start, only sensible for slicecutter = 1.
	if slicecutter == 1:
		if k==nstart:
			PSIw[kk] = float(PSIWidth)
			pn[kk] = 1 #  PSI jump
		if k > nstart:
			PSIw[kk] = PSIFramePos[kk]-PSIFramePos[kk-1]
			if PSIw[kk] < 2000:
				pn[kk] = 1
			else:
				PSIw[kk] = PSIw[kk]/2
				pn[kk]=2
	else:
		PSIw[kk] = PSIWidth	 

	#The current stream value needs to be compared not to the frame, but PSI index number.
	#Generate the PSI cycle number from the frame number
	nrel = k-nstart
	kk+=1
	#sys.exit() # Used during code testing to stop excution at first frame 

print 'Sub profile (sProf) list size:', RectHt
print'slices analyzed:', maxslices

#print 'PSICenter',PSICenter

#Prepare list of lists for output
#PSICenterOutput = [ [ 0 for i in range(3) ] for j in range(kk) ] 'another way

PSICenterOutput = []
PSICenterOutput.append(SliceNum)
PSICenterOutput.append(PSICenter)
PSICenterOutput.append(PSIraw)
PSICenterOutput.append(pccmax)
PSICenterOutput.append(pn)
PSICenterOutput.append(PSIw)
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
print 'csv format: slice = frame #; cn = PSI center row; raw = pattern recog. center (no corrections):'
print '            pcc = pn = number of PSI in frame; pw = PSI width/frame'
print '            (pn will be zero if slice interval >1)'
stoptime = time.time()
print  'Elapsed time to process '+str(maxslices)+'frames:'+ str((stoptime-starttime)/60)
#NOW GO TO R AND GET THE REGIMES USING THE CSV DATA SET
#NEXT OPERATION IF WE DID NOT HAVE TO DO THIS WOULD BE THE ACTUAL FRAME CORRECTION FILTER ON A 
#FRAME BY FRAME BASIS.
# WE WOULD FIRST INVERT THE VALUES OF THE TEMPLATE BEFORE DOOING THE OPERATION.
#GENERATE A MASK FOR THE FRAME AND SUBTRACT. HOW TO CREATE AN IMAGE MASK FROM A NUMBER SET?
