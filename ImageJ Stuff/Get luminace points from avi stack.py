
#This python\jython ImageJ script extracts the minimum and maximum luminance values of each row 
#across all the slices (frames) of a avi stack opened as a virtual stack. The output is a csv 
#file of two maximum and #minimum luminance points in columns in that order respectively, that
@can be fitted to develop the luminance equation used for the PSI correction.
#Output file will be in #Default_Path + Luminace_pts.csv, where default_path is 
#usually ImageJ Stuff//

#NOTE THAT IT IS ADVISABLE TO CONSIDER WHETHER THE FULL RANGE OF POINTS IS PRUDENT TO USE.
#IT HAS BEEN NOTED THAT EARLY FRAMES MAY HAVE LUMINANCE VALUES THAT MAY NOT BE REPRESENTATIVE 
#OF THE LEADER FRAME SEQUENCE IN GENERAL.

from ij import IJ, ImagePlus, ImageStack
import ij.io
import ij.gui 
import csv
import operator
import os
import sys

DriveOption = "E"

os.chdir("C:\\")
#default_drivepath = DirectoryChooser("Choose Top Level Drive or Drive:/Directory").getDirectory()
#os.chdir(default_drivepath)
#avi_inpath = DirectoryChooser("Choose folder of inbound avi").getDirectory()

if DriveOption == "C":
	default_drivepath = "C:\\Canon\\"
elif DriveOption == "E":
	default_drivepath = "E:\\"  
elif DriveOption == "G":
	default_drivepath = "G:\\"
elif DriveOption == "X":
	print 'X???'
#set directory paths
if DriveOption != "X":
	default_path = default_drivepath+"ImageJ Stuff\\" # use forward slashes or 2 back slashes for these
	avi_inpath = default_drivepath+"avi_in\\"
print 'avi in path:', avi_inpath	
os.chdir(avi_inpath) #default_path)
d1 = os.getcwd()  

#SET ALL PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
ImgHt = 1080
ImgWidth = 1920
#mext four values used to create final rectangle, usually will mirror values used for finding centers in template script.
topPt =0 #60			# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240				# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020      # bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680 			# rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ
luminf = "Luminace_pts.csv"

# SET STARTING AND ENDING FRAME
startf = 10
endf = -1 # -1 WILL USE ALL FRAME


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#GET AVI FILE INPUT
od = OpenDialog("Choose the avi file to analyze",avi_inpath, None)
filename = od.getFileName() 
if filename is None:   
	print "User canceled the dialog.Exiting!"
	sys.exit()
else:   
	directory = od.getDirectory()
	avi_file = directory + filename
	print "Selected file path:", avi_file

#open the avi file as a virtual stack file
stack = AVI_Reader.openVirtual(avi_file)
stack.show() 
stack_ID = stack.getID()
stacksize = stack.getStackSize()

ImgWidth = stack.getWidth()
ImgHt = stack.getHeight()

print 'stack size', stacksize

#run("AVI...", "select=C:\\Canon\\avi_out\\stack2.avi first=1 last=181 use convert")
#Z-project has a number of projection attributes. One is to average the intensities
maxprofile=[0]*ImgHt
minprofile=[0]*ImgHt
IJ.makeRectangle(lftPt,topPt,rtPt-lftPt,ImgHt)

if endf <0: endf=stacksize
for i in range(startf,endf):
	slice = stack.setSlice(i)
	imp=IJ.getImage()
	#Despite invoking vertical option above,ProfilePlot resets/overides, 
	#must declare horizontal averaging boolean here
	pp = ProfilePlot(imp, True) 
	profile = pp.getProfile()
	if i == startf:
		minprofile=[x for x in profile]
		maxprofile=[x for x in profile]
	else:
		for j in range(0,len(profile)):
			minprofile[j]=min(minprofile[j],profile[j])
			maxprofile[j]=max(maxprofile[j],profile[j])

minmax=[]
minmax.append(maxprofile)
minmax.append(minprofile)

#invert tthe data to convert columns to rows using list(zip(*minmax). 
lumPts= list(zip(*minmax))

#create and insert a header
hdr = ['max Pts','minPts'] 
lumPts.insert(0,hdr)

luminPath = default_path+luminf
#open(CentersPath,'w', newline='') as f: 'newline must be used in >3.2 and windows

f = open(luminPath,'w') 
fout = csv.writer(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n' ) 
for row in lumPts:
	fout.writerow(row)
f.close()
print 'CSV file ['+luminPath+'] holds the PSI Centers Data'

