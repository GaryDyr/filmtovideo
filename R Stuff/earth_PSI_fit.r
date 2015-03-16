
#REQUIRES PACKAGES: earth, plyr BE INSTALLED; GET FROM CRAN SOURCE
#NOTE: To run a .r file from console do: source("my_script.R")
#store the current directory
# load the necessary libraries
library(earth)
library(plyr)
initial.dir<-getwd()
# change to the new directory
#setwd("C:/Canon/Curve Fitting Methods-Other") # change this to working directory with data
#setwd("C:/Canon/R Stuff") # change this to working directory with data
#setwd("F:/Curve Fitting Methods-Other")
setwd("F:R Stuff") # change this to working directory with data

# Are we in the right working directory?
getwd()
# What files are there?
list.files(path = ".") # list working directory files
PSI1<-read.csv("PSI_Leader_Centers.csv", header = TRUE) 	 # Frame type data
#csv file column header definitions
	#slice = frame #; 
	#fp = streaming PSI frame row; 
	#pn = PSI cycle #; 
	#pp = PSI streaming position; 
	#cp = Postion of PSI calculated from PSI width with zero pt to coincide with slice value.
	#Ck = fractional streaming frame value
	#pw = PSI width'
nrow(PSI1)
ncol(PSI1)
# Check the data frame - list the data
PSI1 	# fractional observed frame PSI position versus PSI peak number
#x1<-PSI1$fp -PSI1$cn[1] #attempt to use P'n-P0 = kw

######################### The call to earth with usually best parameters ###########################################################
  fit<-earth( x = PSI1$pn, y=PSI1$fp , nk = 100, nfold = 20, ncross = 100, degree = 2, trace = 0, penalty = -1, newvar.penalty = 0, glm = NULL,  
 thresh = 0, minspan = 0,  fast.k = 0, fast.beta = 0, pmethod = "backward", nprune = NULL, Exhaustive.tol = 1e-10)
 fit<-earth( x = PSI1$pn, y=PSI1$fp , nk = 100, nfold = 9, ncross = 100, degree = 2, trace = 0, penalty = -1, newvar.penalty = 0, glm = NULL,  
 thresh = 0, minspan = 0,  fast.k = 0, fast.beta = 0, pmethod = "forward", nprune = NULL, Exhaustive.tol = 1e-10)
 fit<-earth( x = PSI1$alice, y=PSI1$Ck, nk = 100, nfold = 9, ncross = 100, degree = 2, trace = 0, penalty = -1, newvar.penalty = 0, glm = NULL,  
 thresh = 0, minspan = 2,  fast.k = 0, fast.beta = 0, pmethod = "forward", nprune = NULL, Exhaustive.tol = 1e-10)
 #The not so good, but should it be????
 fit<-earth( x = PSI1$pn, y=x1 , nk = 100, nfold = 9, ncross = 100, degree = 2, trace = 0, penalty = -1, newvar.penalty = 0, glm = NULL,  
 thresh = 0, minspan = 6,  fast.k = 0, fast.beta = 0, pmethod = "forward", nprune = NULL, Exhaustive.tol = 1e-10)
 fit<-earth( x = PSI1$cp, y=PSI1$fp , nk = 100, nfold = 20, ncross = 100, degree = 2, trace = 0, penalty = -1, newvar.penalty = 0, glm = NULL,  
 thresh = 0, minspan = 4,  fast.k = 0, fast.beta = 0, pmethod = "backward", nprune = NULL, Exhaustive.tol = 1e-10) 
 ####################################################################################################################################
 plot(fit)
#capture the output of the earth summary
#sink("PSI_regimes.out")
#summary(fit, decomp = "none") # "none" to print terms in same seq as a.lm below
#this gives the coefficeints that show up in the summary from summary
#fit$coefficients
#fit$cuts
#fit$dir
#shut off data capture
#sink()
#fitted(fit) # Prints out the fitted values -> y values.
#NOTE: IF COPYING FROM OUTPUT SCREEN TO EXCEL DIRECTLY, THESE FUNCTIONS ALL PRINT THE ROW NAMES, WHICH CANNOT BE SUPRESSED. 
#USE THIS IN EXCEL TO GET NUMBERS: =RIGHT(J3,LEN(J3)-FIND("]",J3))*1 WHERE J3 IS CELL TO PARSE & *1 CONVERTS  TEXT TO #.
#residuals(fit) # Prints residuals
##############################################################################################################
# set the output file # use to save sequence.
#output the data to be read by ImageJ get all the info together from the various parameters
outlist<-cbind(fit$coefficients,fit$cuts,fit$dir)#plyer package function
write.table(outlist, file = "PSI_regimes.csv", sep = ",", col.names = NA, qmethod = "double") # may also need row.names=NA or F to suppress row position

