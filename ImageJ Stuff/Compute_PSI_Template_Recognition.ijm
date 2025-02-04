

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

//SET UP IMAGEJ FUNCTION CONDITIONS
//default profile conditions except do a vertical profile
//getprofile 
run("Profile Plot Options...", "width=450 height=200 minimum=0 maximum=0 vertical interpolate draw");
run("Set Measurements...", "area mean standard min median redirect=None decimal=3");

//BRING IN TEMPLATE DATA
//Two ways to do this. One is as a 
progress("Open file, which must be a csv list in (value x, value y) format", 1, 10);
string = File.openAsString(""); //cannot find openasstring is it really:
run("Text File... ", "open=[G:\\camcorder rotating tests\\CamRotOutside\\Rotating Camcorder outside subset vert 250th_15th png _000011.png]");
start = getTime;
progress("Split the CSV file into an array of lines", 2, 10);
lines = split(string, "\n");

run("Text Image... ", "open=[G:\\camcorder rotating tests\\CamRotOutside\\Rotating Camcorder outside subset vert 250th_15th png _000011.png]");

//MAYBE I SHOULD NOT BE SO QUICK TO RUN THE COLUMN STUFF IN IMAGEJ.
//CRUNCHING NUMBERS IS NOT ITS FORTE. WE STILL HAVE T DEAL WITH OUTPUTING THEDATA INTO SOME KIND OF EXCEL FILE. IMAGEJ DOES NOT REALLY DO 2d ARRAYS

//initialise some variables
n = lengthOf(lines);
x = newArray(n);
y = newArray(n);



//Open the file series; getdirectory asks for the directories
//next 2 lines were for early testing only, but show needed format
//for file specification:
//dir1 = "C:\\Graphics\\camcorder rotating tests\\" ;
//dir2 = "C:\\Graphics\\camcorder rotating tests\\Outfeed\\";


dir1 = getDirectory("Choose image Directory");
dir2 = getDirectory("Choose Destination Directory");
list = getFileList(dir1);

//this file will not open contains error..must choose option for virtual stack.
run("AVI...", "select=[C:\\Canon\\Projector Leader Tests 091611 100 only.avi]");
//this will supposedly have a virtual stack trigger in the dialog box that opens when file picked.

 run("Clear Results");

//Loop through files
for (n=0; n<list.length;n++) {
    showProgress(n+1, list.length); //never saw this!?
    open(dir1+list[n]);

//Extract name of image for header for id purposes later
//could also use File, name here, but this works
//problem if file name has blanks; Excel writer plugin uses CSV/text file 
//and parses blanks to cells, so remove blanks.... 
name = getTitle; 
index = 0;
while (index!=-1) {
   index = indexOf(name," ");
   if (index!=-1) name = substring(name,0,index) + substring(name,index+2); 
}
//take care of dot in file name
index = lastIndexOf(name, "."); 
if (index!=-1) name = substring(name, 0, index); 

//MAY NOT NEED NEXT TWO LINES, NO REASON TO DUPLICATE
//process the image file, top crop first, on duplicate file.
//run("Duplicate...", "title=[temp-1.png]");

//create working area of image
//First get image dimensions
getDimensions(Iwidth, Iheight, channels, slices, frames); //could also just use getWidth() and getHeight()

leftPt = leftcut*Iwidth;
topPt = topcut*Iheight;
rWidth = Iwidth*(1-rtcut) - leftPt;
rHt = Iheight*(1- botcut) - opPt;
  
makeRectangle(leftPt, TopPt, rWidth, rHt);  //x from left;  y from top; rect. Width; rect. Ht. 

//run("Crop"); //may not be necessary for this
run("8-bit"); //convert to 8 bit greyscale

//Could just calculate the std deviation and mean myself
sqrt( (sum of squared pixel values - (sum of pixel values)^2 / n) / (n - 1) )

// Get profile and display values in "Results" window
//vertical option will cause averaging of all columns in each row.
run("Measure");
profile = getProfile(); 
//We can only work with one Results window, so use arrays to hold all data and results for summary info
//Array format for each column will be:
//file ID
//number of points
//mean
//standard deviation

Amean = getResult("Mean", 1) 
AnSD = getResults "StdDev", 1)

run("Clear Results");





  for (i=0; i<profile.length; i++){
     setResult(name + "b", i, profile[i]);    // using name as header name.
    //   updateResults(); //Call only if we want to see updated results, slows down process
  }
counterold = nResults();
run("Analyze Particles...", "size=0-Infinity circularity=0.00-1.00 show=Nothing display record");
counter = nResults()-1;
//This is needed to fill every row w/ label because of Excel cvs conversion.
for (k=counterold; k<counter+1;k++) {
  setResult("Label",k,name);
  updateResults();
}

close(); //close the cropped duplicate

} //file loop


   }

  //Close the image file, but not the results table
   close();
}  //file loop

//Save file as Excel; the following adds the column labels from results
fname = "PSI_Results + name";
run("Excel...", "select...=["+dir2+fname+".xls]"); 

//he following two lines print only the data. not the headers from the results
//run("Input/Output...", "file=.xls"); 
//saveAs("measurements", dir2+File.name+".xls");








//Save file as Excel; the following adds the column labels from results
fname = "topbotvertresults2";
run("Excel...", "select...=["+dir2+fname+".xls]"); 

//he following two lines print only the data, w/ no result headers
//run("Input/Output...", "file=.xls"); 
//saveAs("measurements", dir2+File.name+".xls");


