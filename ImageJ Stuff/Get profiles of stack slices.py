#This python/jython script gets the vertical profiles from an avi file in a rectangular ROI
#and outputs each profile as a column array in csv format that can easily be opened in Excel.
#Its principle use is to simplify the task of getting blocks of profiles into Excel to find the shape of
#the PSI. However, it is generic enough to be used for any opeation that needs to read multiple profiles.
#It uses a virtual stack, so the avi files can be quite large for reading.
#For developing PSI profiles the process still requires manual picking of the alignment points.

#INPUT: ANY AVI FILE
#OUTPUT: #Default output is to the /ImageJ Stuff/ folder with file name: profiles.csv

#Copyright 2014 by Gary Dyrkacz. 
#(Last update fixed issues with major FIJI upgrade in 2014.

from ij import IJ, ImagePlus, ImageStack
import ij.io
import ij.gui 
import csv
import operator
import os
import sys
from ij.io import OpenDialog
from ij.gui import GenericDialog 
from ij.io import FileSaver
from java.io import File 
import java.io.File.__dict__ 
from mpicbg.imglib.image.display.imagej import ImageJFunctions as IJF
import ij.VirtualStack 
from ij.gui import NewImage
from ij.plugin import AVI_Reader # added June, 2014 after upgrading to Imagej2, needed explicitly
from ij.gui import ProfilePlot

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#SET DRIVE AND FOLDER DEFAULTS HERE
DriveOption = "F"  		# What drive is the data on? This also sets a subfolder. See below to change default.

#HOTE PROFILES.CSV IS OVERWRITEN EACH TIME RUN. TRANSFER DATA OUT OF FILE BEFORE RUNNING ANOTHER AVI.
#profile.csv ends up in folder "ImageJ Stuff"
outf = "profiles.csv"   #Standard file to dump profiles. 
#default_drivepath = DirectoryChooser("Choose Top Level Drive or Drive:/Directory").getDirectory()
#os.chdir(default_drivepath)
#avi_inpath = DirectoryChooser("Choose folder of inbound avi").getDirectory()

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

d1 = os.getcwd()  
print d1	
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#SET ALL PARAMETERS HERE
ImgHt = 1080
ImgWidth = 1920
#mext four values used to create final rectangle, usually will mirror values used for finding centers in template script.
topPt =0 #60			# top point of video frame that starts the profile measurement rectangle in ImageJ
lftPt = 240				# left point of video frame that is the left edge of the profile measurement rectangle in ImageJ
botPt = 1080 #1020      # bottom point of video frame that ends the profile measurement rectangle in ImageJ
rtPt  = 1680 			# rigth point of video frame that is the right edge of the profile measurement rectangle in ImageJ
startf = 1				# starting frame to get profile
endf = -1				# last frame to analyze
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#OUTPUT FILE FOR ARRAY OF PROFILES


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
if endf< 0: endf=stacksize
#run("AVI...", "select=C:\\Canon\\avi_out\\stack2.avi first=1 last=181 use convert")
#Z-project has a number of projection attributes. One is to average the intensities

IJ.makeRectangle(lftPt,topPt,rtPt-lftPt,ImgHt)

profile_list=[]
hdr=[]
for i in range(startf,endf):
	slice = stack.setSlice(i)
	imp=IJ.getImage()
 #gets current slice as image
	pp = ProfilePlot(imp, True) #Despite invoking vertical option above,ProfilePlot overides, must declare horizontal averaging here
	profile = pp.getProfile()
	hdr.append("s"+str(i))
	profile_list.append(profile)
	
profiles = zip(*profile_list) #turn rows to columns for typical output.
profiles.insert(0,hdr)

profilepath = default_path+outf
f = open(profilepath,'w') 
fout = csv.writer(f, dialect='excel', quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n' ) 
for p in profiles:
	fout.writerow(p)# note brackets around p - a separate list now
f.close()
sys.exit()
"""
#TO USE RESULT TABLE AND DUMP DIRECTLY TO EXCEL FILE SEE BELOW
#THIS IS NOT QUITE SET AT THIS POINT AND WOULD NEED TO BE IN SLICE PROCESSING LOOP
#THIS NEEDS TO START A NEW COLUMN SO RUNNING OVER TWO INDICES. ONE FOR SLICE/COLUMN
#AND ONE FOR PRINTING ROW VALUES AS BELOW.
#NOTE THIS CODE IS QUITE A BIT DIFFERENT THAN MACRO CODE EXAMPLE BELOW
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


#Save file as Excel; the following adds the column labels from results
#fname = "mean_avi_profile"
#IJ.run("Excel...", "select...=["+dir2+fname+".xls]") 

#following two lines print only the data. not the headers from the results
IJ.run("Input/Output...", "file=.xls") 
IJ.saveAs("Results", "C:\\Canon\\ImageJ Stuff\\Average.xls");


// StackProfileData
// This ImageJ macro gets the profile of all slices in a stack
// and writes the data to the Results table, one column per slice.
//
// Version 1.0, 24-Sep-2010 Michael Schmid

macro "Stack profile Data" {
     if (!(selectionType()==0 || selectionType==5 || selectionType==6))
       exit("Line or Rectangle Selection Required");
     setBatchMode(true);

     run("Plot Profile");
     Plot.getValues(x, y);
     run("Clear Results");
     for (i=0; i<x.length; i++)
         setResult("x", i, x[i]);
     close();

     n = nSlices;
     for (slice=1; slice<=n; slice++) {
         showProgress(slice, n);
         setSlice(slice);
         profile = getProfile();
         sliceLabel = toString(slice);
         sliceData = split(getMetadata("Label"),"\n");
         if (sliceData.length>0) {
             line0 = sliceData[0];
             if (lengthOf(sliceLabel) > 0)
                 sliceLabel = sliceLabel+ " ("+ line0 + ")";
         }
         for (i=0; i<profile.length; i++)
             setResult(sliceLabel, i, profile[i]);
     }
     setBatchMode(false);
     updateResults;
}

"""

