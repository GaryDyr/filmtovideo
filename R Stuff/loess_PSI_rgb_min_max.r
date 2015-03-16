demo(loess_lumrgbfitting)
#TAKES FRACTION OF CHANGE FROM PSI MAX @(PSI CENTER) TO 
#PSI MIN AT PSI MOVING AVERAGE WIDTH, COMPUTES LOESS FIT IN RANGE 0-255
#REQUIRES loess_lum_min_max.csv
#FILE OUT:lum_rgb_loessfit.csv
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
 P1<-read.csv("loess_lum_min_max.csv", header = TRUE) #around 5779 pts in file
nrow(P1)
ncol(P1)
#Generate a std 0-255 row sequence to use against predicted fit.
row<-seq(0,255)
#print row to make sure generated
row
# capture the output of the loess summary
# sink("lumrgb.out")
# set the plot so can determine if fit looks good
plot(P1$Lmax,P1$diff)
# Adjust span parameter to get the smoothed data
fit<-loess(P1$diff~P1$Lmax, span = 0.20)
pred.lum<-predict(fit,P1$Lmax)
lines (P1$Lmax, pred.lum, col ="red")
# Now calculate the 0-255 data points from the generated row vector.
yfit.lum<-predict(fit,row)

# if you wished to do say another column
# fit2<-loess(P1$xmin~P1$row, span = 0.1)
# pred.min<-predict(fit2,P1$row)
# lines(P1$row, pred.min, col ="red")
# yfit.min<-fitted(fit2)
# shut off data capture
# sink()
# Prints out the printed numbers.
#residuals(fit) # Prints residuals
##############################################################################################################
# set the output file # use to save sequence.
#outlist<-cbind(row,yfit.lum)
#This still put out data with an index
write.table(yfit.lum, file = "lum_rgb_loessfit.csv", sep = ",", col.names = NA, qmethod = "double") # may also need row.names=NA or F to suppress row position


