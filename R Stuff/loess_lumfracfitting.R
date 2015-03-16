demo(loess_lumfracfitting)
#requires package earth be available; get from CRAN
 #store the current directory
 #to run a .r file from console do: source("my_script.R")

 initial.dir<-getwd()
 # change to the new directory
 setwd("F:/Canon/R Stuff") # change this to working directory with data
 # load the necessary libraries
 #library(Add Lib Here If Needed)
 # Are we in the right working directory?
 getwd()
 # What files are there?
 list.files(path = ".") # list working directory files
# Get the csv file containing the data; make sure there are headers
# call input data P1 two columns with header names: Lmin,frac
#Lmin is the min rgb value, and frac is the relative fraction change
#from the min to maximum PSI position.
 P1<-read.csv("lumminfrac.csv", header = TRUE) #around 5779 pts in file
nrow(P1)
ncol(P1)
#Generate a std 0-255 row sequence to use against predicted fit.
row<-seq(0,255)
#print row to make sure generated
row
# capture the output of the loess summary
# sink("lumfrac.out")
# set the plot so can determine if fit looks good
plot(P1$Lmin,P1$frac)
# Adjust span parameter to get the smoothed data
fit<-loess(P1$frac~P1$Lmin, span = 0.30)
pred.frac<-predict(fit,P1$Lmin)
lines (P1$Lmin, pred.frac, col ="red")
# Now calculate the 0-255 data points from the generated row vector.
yfit.frac<-predict(fit,row)

# if you wished to do say another column
# fit2<-loess(P1$xmin~P1$row, span = 0.10)
# pred.min<-predict(fit2,P1$row)
# lines(P1$row, pred.min, col ="red")
# yfit.min<-fitted(fit2)
# shut off data capture
# sink()
# Prints out the printed numbers.
#residuals(fit) # Prints residuals
##############################################################################################################
# set the output file # use to save sequence.
#outlist<-cbind(row,yfit.frac)
#This still put out data with an index
write.table(yfit.frac, file = "lumfracloessfit.csv", sep = ",", col.names = NA, qmethod = "double") # may also need row.names=NA or F to suppress row position


