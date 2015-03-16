#This script averages all the frames in a stack in a specified hardwired rectanglular area
#and produces an image of the average. The corresponding vertical profile is obtained 
# region.
#In addition, a results window lists the values, and they are output as both a csv file 
#and an Excel file.
#

from ij import IJ, ImagePlus, ImageStack
import ij.io
import ij.gui 
import csv
import operator
import os
import sys

DriveOption = "C"

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
	avi_inpath = default_drivepath+"avi_out\\"
print avi_inpath	
os.chdir(avi_inpath) #default_path)
d1 = os.getcwd()  
print d1	

#SET ALL PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
ImgHt = 1080
ImgWidth = 1920
#mext four values used to create final rectangle, usually will mirror values used for finding centers in template script.
topPt =0 #60				# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240					# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020          # bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680 				# rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ


od = OpenDialog("Choose the avi file to analyze",avi_inpath, None)

filename = od.getFileName() 
if filename is None:   
	print "User canceled the dialog.Exiting!"
	sys.exit()
else:   
	directory = od.getDirectory()
	avi_file = directory + filename
	print "Selected file path:", avi_file

stack = AVI_Reader.openVirtual(avi_file)

stack.show() 
stack_ID = stack.getID()
stacksize = stack.getStackSize()

ImgWidth = stack.getWidth()
ImgHt = stack.getHeight()

print 'stack size', stacksize
startf = 1
endf = 3
#run("AVI...", "select=C:\\Canon\\avi_out\\stack2.avi first=1 last=181 use convert")
#Z-project has a number of projection attributes. One is to average the intensities
#IJ.run("Z Project...")
#For unexplained reasons the range of frames that the plughin allows you to pick, do
#not work for some reason. 
IJ.run("Z Project...", "start=2 stop=18 projection=[Average Intensity]")
imp=IJ.getImage()
#print imp.getTitle()
IJ.makeRectangle(lftPt,topPt,rtPt-lftPt,ImgHt)
IJ.run("Profile Plot Options...", "width=450 height=200 minimum=0 maximum=0 vertical interpolate draw")
pp = ProfilePlot(imp, True) #Despite invoking vertical option above,ProfilePlot overides, must declare horizontal averaging here
#IJ.run("Plot Profile")
profile = pp.getProfile()
#see for ResultsTable class: http://rsbweb.nih.gov/ij/developer/api/ij/measure/ResultsTable.html

rt = ResultsTable()
#rt.incrementCounter()
#if rt.columnExists(1): 
#	print 'was created'
#else:
#	print 'cant find column'
for i in range(len(profile)):
	rt.incrementCounter() #must use this internal counter;add value does not work as might think from docs.
	rt.addValue(1, profile[i]) # using name as header name.
	#rt.setValue(0,i,profile[i]) #adds to specific row
rt.show("Average")

profilepath = default_path+"aver_stack.csv"
f = open(profilepath,'w') 
fout = csv.writer(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n' ) 
profile = profile.tolist()
#profile now a list
for p in profile:
	fout.writerow([p])# note brackets around p - a separate list now
f.close()

#Save file as Excel; the following adds the column labels from results
#fname = "mean_avi_profile"
#IJ.run("Excel...", "select...=["+dir2+fname+".xls]") 

#following two lines print only the data. not the headers from the results
IJ.run("Input/Output...", "file=.xls") 
IJ.saveAs("Results", "C:\\Canon\\ImageJ Stuff\\Average.xls");
sys.exit()
