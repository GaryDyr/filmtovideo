#Python code to generate frame luminance corrected PSI template data 
# i.e., base or normalized PSI profile corrected for luminance variations 
#This procedure only generates the template array to correct or "distort
#a normal or base PSI to a luminance corrected version as a video frame
#would show it.
#Compared to the Excel version it is lightening fast. The Excel version takes over 
#3.4 minutes to run. This code runs in less than a second. 
#Note that this sequence generates a full seequence of PSIWidth/interval
#columns, by 1080 rows of data. The Excel version automatically subtracts 
# out a fraction of the row range for the measured rectangle that will be 
#chosen#account the good image row range. 
#THIS SCRIPT DOES NOT DO PSI expansion or compression. 
#
# The code here can be run in python versions > 3.2.3 
# IT CANNOT RUN IN JYTHON  under FIJI-ImageJ as of 07/05/2012, which only 
# supports Python 2.5.
# Furthermore, the code does not use numpy calls, which is definitely
# a preformance weak point. The reason is that the code was run on
# 64 bit Windows 7 system. At this time, numpy only runs on 32 bit Python 3.2. 
# under specific circumstances. See:
# http://www.andrewsturges.com/2012/05/installing-numpy-for-python-3-in.html
# for details.
# similar issues exist with the openCSV package.

#Requires 
# A csv file of two connected mormalized PSI profiles  (2 x wavelength)
# Default file name: "PSI_norm_1358.csv"
#AND
# nine 3rd order fitting coeffiicents (only six may be used) see below,
$OR,
# or a file of correction row values
# ALSO MUST SPECIFY VARIABLES BELOW

from sys import exit 
import math
import csv
import os
from math import sqrt
#from numpy import *
#Set the interval spacing in the timeplate here..1
#--------------USER VARIABLES TO SET--------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
default_path = "C:\\Canon\ImageJ Stuff\\" # working directory with data files
#default_path = "G:\\ImageJ Stuff\\" # working directory with data files
PSIf = "PSI_norm_1358.csv"
corrf = "Frame_Luminance_Correction_Coef.csv"
interval = 10 			# row spacing between successive points; 1 = every row
PSIWidth = 1358			# width of the normalized PSI
csize = 1320			# default row size of the vertical resolution, e.g., 1080, to account for compression of PSI
corr_file = True		# Sets if 3rd order coefficients will be in a csv file (True) or are below.
topx = 240				# left most video column where rectangle portion starts
topy = 108				# top row where profile measuring rectangle portion starts
botx = 1340				# right edge where profile measuring rectangle portion stops
boty  = 972				# bot row where profile measuring rectangle stops
Ht = 1080				# video frame height = number of rows = vertical video frame resolution
# Default 3rd order coefficients
# 			x^3         x^2          x         c
Imax = [-6.0772E-08,3.40639E-05,0.042506019,123.6491484]
Imin = [-2.5251E-08,2.84076E-05,-0.001742574,74.722009]
Idif = [-3.5521E-08,5.65627E-06,0.044248592,48.92713942]
IBase = 255
#++++++++++++++++++++++++++++++++++++++++++++++++++++*************************

"""
PSI is an array vector that is twice the length of PSI. This array is generated 
and stored as a csv file from Excel Projector Leader Tests.xlsm [PSI] column 5
corr ia the calculated array of luminance correction factors based on where the PSI is.
"""
# a way to determine integer values of cszie/interval
#filter function returns an interator object, not a list convert or use list comprehension
allowed_intervals = []

if (csize % interval !=0):
	allowed_intervals = [x for x in range(csize) if (csize % x !=0)] 
    print("Bad interval choice - aborting; allowed values are: ", allowed_intervals)
	sys.exit()

n=int(csize/interval)

if os.getcwd() != default_path:
    os.chdir(default_path) 

#Excel stores numbers in a csv file without quotes, with a comma as separator
#using the QUOTE_NUMERIC parameter convert to a float value internal to reader
#uaing 'with' is apparently safer code for cleanup on exceptions
with open(default_path+PSIf) as f:
	#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
	PSI = [x[0] for x in csv.reader(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)] 

print('rows:',len(PSI))
#print('PSI',PSI)

#alternate method when Fiji and 64 bit Pyhton catch up with loadtxt is a numpy function
#PSI = numpy.loadtxt(open(PSIf,"rb"),delimiter=",",skiprows=0, dtype=int)

#FRAME CORRECTION GENERATOR
#generate or get from file an array of x values corresponding to row intervals
#corr = numpy.loadtxt(corrf,delimiter=",",skiprows=0, dtype = float, usecols = (0,1)) #the numpy method
	
corrf = "Frame_Luminance_Correction_Coef.csv"

#Read the csv file containing max and min 3rd order equations parameters 
if corr_file: # Supplying file or building?
	with open(default_path+corrf,'r') as f:
		corr = [x for x in csv.reader(f, dialect='excel',quoting=csv.QUOTE_NONNUMERIC)]

#generate the 2D base PSI array slicing out only frame designated area at rows of interval.
#Sequence is: 
#  1. Generate single sub list of PSI values at desired interval
#  2. The correction must be applied to each block of size that will span the 1080 visual frame
#     at each interval,because correction is row dependent. 

sPSI = PSI[0:len(PSI):interval] #this still covers 2*PSI cylces/intervals
print('len of sPSI',len(sPSI))

#generate a list containing Ht/lnterval different lists of length csize/integral:
#to save cycles, do a row at a time, which varies col to col by interval of size csize/interval
#each row varies by interval with a col size of Ht of video frame. 

#Cannot use :PSInew= [[]*n for x in xrange(n)] to declare new array
#When you do []*n it creates multiples, but the list is actually a series of pointers, so you
#create three pointers to the same element.
#without the zero this is a list of empty lists, with only holders and no dim size can be read
#create list that has n columns and x rows (from range 0->Ht/interval
PSInew =list([[0]*n for x in range(int(Ht/interval))])
print('rows:',len(PSInew))
print('cols:',len(PSInew[0]))

#calct Imax,0 - Imin,0 term
if corr_file:
	Ir0 = corr[0][3]-corr[1][3] 
else:
	Ir0 = Imax[3]-Imin[3]	

for j in range(0,int(Ht/interval)):
	#calc new corrected PSI value for each row in cPSI
	for i in range(n):
		cPSI = sPSI[i:n+i] #slice out a section of sPSI at row i of size of csize/interval to correct rgb GHECKED OK
		#create a corresponding rowarray to hold the index (row) positions) for the calculation 
		rowarray = [x for x in range(i,csize+i,interval)]  #(i,Ht,interval)] #beyond frame height is meaningless CHECKED OK
		if corr_file:	
			Imaxr = corr[0][0] * rowarray[j]**3 + corr[0][1] * rowarray[j]**2 + corr[0][2] * rowarray[j] + corr[0][3]
			Iminr = corr[1][0] * rowarray[j]**3 + corr[1][1] * rowarray[j]**2 + corr[1][2] * rowarray[j] + corr[1][3]
			Idif = Imaxr - Iminr #Imax,r - Imin,r
		else:
			Imaxr = Imax[0] * rowarray[j]**3 + Imax[1] * rowarray[j]**2 + Imax[2] * rowarray + Imax[3]
			Iminr = Imin[0] * rowarray[j]**3 + Imin[1] * rowarray[j]**2 + Imin[2] * rowarray + Imin[3]
			Idif = Imaxr - Iminr 
		PSInew[j][i] = Imaxr + (((cPSI[j] - IBase) * Idif) / Ir0) # Imax,o-Imin,o from dif between Imax and Imin & 

corrPSIf = "PSI_corr_n"+str(interval)+"_w"+str(PSIWidth)+".csv"
corrpath = default_path+corrPSIf
print('template file saved is:',corrpath)
print('n$$ is the interval between points; w is the width of the PSI')
with open(corrpath,'w', newline='') as f: 'newline must be used in >3.2 and windows
	#reads a column; without [0] reads as individual arrays; useful in 2D arrays, but redundant here
	fout = csv.writer(f, dialect='excel') #, quoting=csv.QUOTE_NONNUMERIC) 
	fout.writerows(PSInew)

#THE FOLLOW IS HOW TO REMOVE THE TOP AND BOTTOM LINES FROM A 1080 SEQUENCE AND LEAVE THE REST	
#As needed remove the bottom and top lines that equal the section analyzed in the rectangle	
PSISliced = list(PSInew)
del PSISliced[int(boty/interval):len(PSInew)]	
del PSISliced[0:int(topy/interval)]
print(len(PSISliced))

#next is numpy - can't use
#PSI2 = column_stack(PSI2,subPSI[i:csize+i])
#themeans = PSInew.mean(axis=0) # array of the mean of each of the columns
#thestds = std(sPSI,axis=0,ddof=1)
#numpy calls
#numpy.insert(sPSI,0,themeans) 
#numpy.insert(sPSI,1,thestds) 
#add two extra lines 
#dummy = zeros(csize, Int) 
#for aline in range(2):
#numpy.insert(PSI2, 2, dummy) 
#add a line at beginning to hold summary info 
#numpy.insert(PSI2, 0, dummy)	
#PSI2[0,0] = PSI2.shape[1]*PSI2*shape[0] # number of points in the file.
#PSI2[0,1] = interval #interval or step size; this wll be used to rebuild the index.
#PSI2[0,2] = PSI2.shape[0]+5 # number of rows in file;
#PSI2[0,3] = PSI2ape[1] # number of columns in file;
#PSI2[0,4] = PSIWidth # new PSI Width



