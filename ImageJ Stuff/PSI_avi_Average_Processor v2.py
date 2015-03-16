"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
ImageJ Python(Jython)  script run under ImageJ/FIJI to average user set substacks from an avi stack.
code is based on Fiji implementation, which uses Python 2.5 and ImageJ 1.49
 Fiji-ImageJ does not recognize Python 3.x specific changes. This especially affects print
 statements and exception functions as the most upfront issue to consider.
 and does not allow numpy package, which would simplify any matrix code substantially.

Requies:
input file:	 an avi file (Color file tested, but BW may work)
remove all file from directory Canon\imagedump\ before starting.

Output file: stack3.avi
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
#from internet ?Cardona had this with zProjector
from ij.plugin import ZProjector
#from ij.plugin import SubstackMaker
#from ij.gui import GenericDialog   
from math import sqrt
from jarray import zeros #jarray is a Jython module that implements only two methods, zeros and array
from operator import itemgetter
from java.io import File 
import java.io.File.__dict__ 
from mpicbg.imglib.image.display.imagej import ImageJFunctions as IJF
import ij.VirtualStack 
from ij.gui import NewImage
from ij.plugin import AVI_Reader # added June, 2014 after upgrading to Imagej2, needed explicitly
from ij.io import OpenDialog
from ij.gui import GenericDialog 
from ij.gui import NonBlockingGenericDialog
from ij.io import FileSaver
#SET ALL GLOBAL PARAMETERS HERE
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
slicecutter = 1		# slices to skip; not really used here, but could be used to createfast motion
nstart = 1 # starting frame to pick up only white leader frames PSIs 
nstop = -1 #-1 # end avi frame/image; set to -1 means do all frames

#CRITICAL INFO THAT MUST BE SUPPLIED FROM OTHER METHODS
# Next factor is appled to PSI template as an experimental factor to improve light variance
# between PSI and image; 1.0 is no multiplier factor 1.3 is a 30% increase for each pixel, which 
# which as the effect of enhancing the PSI values of the template correction; applied in GetTemplate
ImgHt = 1080 	   #default, but will get from laoded avi stack
ImgWidth = 1920    #default, but will get from laoded avi stack
avg_range = 2 # frames to average over

defaultMethod = ZProjector.AVG_METHOD
#SEE http://www.ini.uzh.ch/~acardona/fiji-tutorial/#generic-dialog FOR STARTER IDEAS.
# set working drive and main folder if needed

DriveOption = "F" #either C, F, X;  X is for dialogues to choose diectories
default_path = "ImageJ Stuff\\" 
#+++++++++++++++ getPaths+++++++++++++++++++++++++++++++++++++++++++++++++
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
# This input method is not very flexible. but has advantage of bypassing 
# dialogue for each file.
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
print 'input avi path is set to:', avi_inpath
#os.chdir(avi_inpath) does not work anymore!!!!!!!!!
d1 = os.getcwd()  
print d1

def getParameters(def_range):   
	gd = GenericDialog("Parameters")   
	gd.addNumericField("Number of Images to Average:", def_range, 0)  # show no decimals
	gd.showDialog()
	avg_range = gd.getNextNumber()    
 	if gd.wasCanceled():   
		print "User canceled dialog!"
		sys.exit()
		avg_range = gd.getNextNumber() 	 
	return avg_range

filecount  = 0
filecount  = len(os.listdir(imagepath))

if filecount > 0:
	IJ.showMessage("Files in Folder", "Cannot run until files removed from /imagedump/ folder.")
	sys.exit()

#CHOOSE THE AVI FILE NOW SO CAN GET PROPER CENTERS FILE.
od = OpenDialog("Choose the avi file",avi_outpath, None)   
filename = od.getFileName() 
if filename is None:   
	print "User canceled the dialog.Exiting!"  
	sys.exit()
else:   
	directory = od.getDirectory()   
	avi_file = directory + filename   
	print "Selected file path:", avi_file   
	(file_name, file_ext) = os.path.splitext(filename) 

print file_name

#cannot get a dialog box to show up while running
#gx = NonBlockingGenericDialog("Running...") #yourGenericDialog.setModalityType(Dialog.ModalityType.MODELESS);
#gx.setModel(false) #true hangs 
#gx.showDialog()

options = getParameters(avg_range)
print options

if options is not None:  
	avg_range = options 
print 'Average Range Used:', avg_range

def validGroupSize(stack_size, aver_group):
	if (aver_group > 0)  and (aver_group <= stack_size):
		retval = True
	else:
		retval = False

	ValidGroupSize = retval
	return ValidGroupSize


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
#     * @param firstFrame  	Number of first frame to read (first frame of the file is 1)
#     * @param lastFrame   	Number of last frame to read or 0 for reading all, -1 for all but last...
#     * @param isVirtual        Whether to return a virtual stack
#     * @param convertToGray    Whether to convert color images to grayscale
#     * @return  Returns the stack; null on failure.
#    *  The stack returned may be non-null, but have a length of zero if no suitable frames were found
#print "size="+imp.getStackSize(); 
#Note imp is now the stack name in this method

stack.show() 
stack_ID = stack.getID() 

gdworking = GenericDialog("Notice")
gdworking.addMessage("PROGRESS IS ONLY DISPLAYED IN iMAGEj STATUS BAR AS THIS PROCEEDS") 
gdworking.showDialog()

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

#create a second stack to hold averaged images
stack3 = ij.VirtualStack(ImgWidth, ImgHt, None, imagepath)
#either of these opens an image stack, but not a virtual stack, so works off available RAM
#fine for very small files, or systems with limited RAM
#stack3 = stack.createEmptyStack() creates a non virtual stack in memory
#stack3 = ImageStack(ImgWidth, ImgHt) 

stack3ID = stack.getID()

#Future reference. Virtual stack is read only, to manipulate it, duplicate it.
#Make sense? Why have an addslice if true?

maxslices = int((AllSlices-nstart)/slicecutter)
print 'AllSices', AllSlices,'maxslices', maxslices

starttime = time.time()
count = 0
print 'starting frame:', nstart, 'last frame:', nstop

#Expects the image stack is current window. Check it.
#Check that there is a current image. Should be redundant, but..
IsItAStack =ij. WindowManager.getCurrentImage()
if IsItAStack==None: 
	IJ.noImage() #This posts a message.
	# Make sure the input image is a stack and not a single image.
	stack_size = IsItAStack.getStackSize()
	if stack_size == 1:
		IJ.error("Running_ZProjector:" + 'this plugin must be called on an image stack.')
stack_size = stack.getStackSize()
  # Validate the image is a stack.
if stack_size == 0:
	IllegalArgumentException("Empty stack.")
if  not validGroupSize(nstop, avg_range):
	IllegalArgumentException("Invalid substack size check parameter avg_range.")

# We will use the Projector object. Initialize it
zproj = ZProjector(stack) 

# Slices are numbered 1,2,...,n     
# we average from the start, but we can only average to maxslices-number to aver
# there is a zproj.setImage fcn, but the java code indicates is uses 
# entire image plus set, not a selection  
nstop = nstop - avg_range 

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#MAIN STACK AVERAGOMG LOOP
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#Run through all slices to average out PSI on frame
for i in range(nstart,nstop):
	IJ.selectWindow(filename) 
	#zproj.setMethod(defaultMethod) # set to AVG_METHOD
	zproj.setStartSlice(int(i))
	zproj.setStopSlice(int(i+ avg_range)) # average avg_range+1 slice	
	zproj.doHyperStackProjection(False)
	#from java API code found next line does not use StartSlice and StopSlice
	#zproj.doRGBProjection() #produces a imageplus object, but does not display
	projection =  zproj.getProjection() # gets the imageplus of the combined images
	#projection.show() # for testing
	AvgImg = projection.getProcessor()
	# must do next line, but not clear why. Processors are supposedly 
	# instances of ImageStack, which are instances of ImagePlus, but if true
	# why do i have to declare it explicitly?	
	imp_temp=ImagePlus("avg_temp", AvgImg)		
	#result file of averaging
	imp_temp.setTitle("avg_"+str(i)+".png")
	#imagestack can add a slice after a specified slice. virtualstack cannot, 
	#but it reads files in a sequence. 
	out_image = imagepath+imp_temp.getTitle()
	FileSaver(imp_temp).saveAsPng(out_image) 
	stack3.addSlice(imp_temp.getTitle())
	count+=1
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

ImagePlus("stack3",stack3).show()
IJ.selectWindow("stack3")
IJ.run("Input/Output...", "jpeg=100 gif=-1 file=.txt use_file copy_row save_column save_row")
AVI_file_out = "stack3.avi"
avi_Out = avi_outpath+AVI_file_out
#no common program I have reads a png based avi file, including irfanview, 
#vitualdub64, use jpeg compression instead
#IJ.run("AVI... ", "compression=PNG frame=30 save=["+avi_Out+"]") 
IJ.run("AVI... ", "compression=JPEG frame=30 save=["+avi_Out+"]") #no compression factor added.

stoptime = time.time()
print 'Elapsed time to process '+str(count-1)+" frames: "+ str((stoptime-starttime)/60)+' min.'
#for checking purposes set plot profile measuring orientation to verical and set an ROI
#IJ.run("Profile Plot Options...", "width=450 height=200 minimum=0 maximum=0 vertical interpolate draw")
#IJ.makeRectangle(lftPt, topPt, ImgWidth, ImgHt)

#Delete the file stream in the png dump directory

#AS NOTED IN MESSAGE, IF FILES DELETED, stack3, A VIRTUAL STACK CANNOT BE DISPLAYED.
removeimages = False
gddelf = GenericDialog("Delete files?")
gddelf.addMessage("Delete intermediate .png image files (recommended, but virtualstack stack3 will not be available for viewing, and will close)")
gddelf.enableYesNoCancel("Delete", "Leave")
gddelf.showDialog()
if (gddelf.wasCanceled()):
	print 'User canceled removal of png images from'+imagepath
elif (gddelf.wasOKed()):
	print 'User opted to delete images from '+imagepath
	removeimages = True
else:
	print'User opted to not delete images from '+imagepath
avipnglist = os.listdir(imagepath)
print avipnglist
if removeimages:
	pattern = ".png"
	for f in avipnglist:
#	for f in File(imagepath).listFiles():
		if f.endswith(pattern):
#		if not os.path.isdir(f) and ".png" in f:
			os.unlink(imagepath+f) #	File(str(f)).delete() # Notice str(f) is needed: Java types vs Python...
	cw = ij.WindowManager.getCurrentWindow()
	cw.close()

print "Done.File saved as: "+AVI_file_out
gdend = GenericDialog("Finished")
gdend.addMessage("Done.File saved as: "+AVI_file_out) 
gdend.showDialog()
sys.exit()


