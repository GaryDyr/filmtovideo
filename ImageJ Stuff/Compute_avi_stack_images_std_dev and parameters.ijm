//This ijm imageJ macro was used to get a set of results from each slice of an avi leader file
//especially the HBath 1-200. AVI file. The main result desired was the std dev, but mean, max and 
//min were also output 
// the file processed is stack2; it is hardwired in.
//The idea. which failed. was to track the average SD to see if the PSILightFactor for PSI_avi_Procesor.py
//could be decided by looking for the lowest average SD. It did not work out that way. The code here
//is an adaptation, and much simpler version of another ijm file, which apparentlYlooked at image files
//in a directory and did some averaging.

//All files here are hardwired.

//BECAUSE THIS IS BATCH MODE, NOTHING WILL BE VISIBLE UNLESS THE MACRO FAILS, OR IT COMPLETES.
//JUST WAIT UNTIL YOU SEE THE PROGRESS BAR SHOW UP AND COMPLETE ITSELF.

setBatchMode(true);
//You start a debugging session by pressing ctrl-d (Debug Macro). 
//You can then single step through the macro code by repeatedly pressing ctrl-e (Step). 
//SET UP PARAMETERS
//set fractions of image to cut away

//Get availabe memory for ImageJ use
MaxMem = IJ.maxMemory()

leftcut = 0.10
rtcut = 0.10
topcut = 0.10
botcut = 0.10
PtSpacing = 3


start = getTime;
dir2 = "F:\\Canon\\avi_out\\";

//dir1 = getDirectory("Choose image Directory");
//dir2 = getDirectory("Choose Destination Directory");
//list = getFileList(dir1);
name = "stack2"
//an AVI file may not open if too large, must choose option for virtual stack.
run("AVI...", "select=[F:\\Canon\\avi_out\\stack2.avi]");
//this will supposedly have a virtual stack trigger in the dialog box that opens when file picked.
//but not in batch mode

//clear any Results
run("Clear Results");
//set th measurements we want
run("Set Measurements...", "mean standard min median stack redirect=None decimal=3");
//get the stack image dimenstions
getDimensions(Iwidth, Iheight, channels, slices, frames); //could also just use getWidth() and getHeight()

//Calculate the ROI to use
leftPt = leftcut*Iwidth;
topPt = topcut*Iheight;
rWidth = Iwidth*(1-rtcut) - leftPt;
rHt = Iheight*(1- botcut) - topPt;

//create working area of image
//First get image dimensions
makeRectangle(leftPt, topPt, rWidth, rHt);  //x from left;  y from top; rect. Width; rect. Ht. 

//nSlices is standard variable for stack size
for (n=1; n<nSlices-1;n++) {
	showProgress(n/nSlices); //never saw this!?
	setSlice(n);
	run("Measure");
}

//Save file as Excel; the following adds the column labels from results
fname = "PSI_Results" + name;

//run("Input/Output...", "jpeg=90 gif=-1 file=.xls copy_column save_column");
//he following two lines print the data, and the headers from the results
run("Input/Output...", "file=.xls copy_column save_column"); 
saveAs("Results", dir2+File.name+".xls");

//he following two lines print only the data. not the headers from the results
//run("Input/Output...", "file=.xls"); 
//saveAs("Results", dir2+File.name+".xls");

//prints a csv file; no headers
run("Input/Output...", "file=.csv"); 
saveAs("Results", dir2+File.name+".csv");

//he following two lines print only the data, w/ no result headers
//run("Input/Output...", "file=.xls"); 
//saveAs("measurements", dir2+File.name+".xls");


