demo(interpolator)
#TAKES a col of rgb values and fractions to be interpolated and
#COMPUTES interpolated values IN RANGE 0-255
#REQUIRES interpolate_this.csv
#FILE OUT:interpolated_values.csv
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
# call input data P1 two columns with header names: rgb, fctr
#rgb are the original rgb values, and fctr is the relative fraction change
#needed to adjust first run rgb corrections to a more refined factor.
 P1<-read.csv("interpolate_this.csv", header = TRUE)
nrow(P1)
ncol(P1)
#Generate a std 0-255 row sequence to use against predicted fit.
row<-seq(0,255)
#print row to make sure generated
row
# capture the output of the loess summary
# sink("lumrgb.out")
# set the plot so can determine if fit looks good
plot(P1$rgb,P1$fctr)
# Adjust span parameter to get the smoothed data
yfit <- approx(P1$rgb,P1$fctr, xout=row, ties = "ordered")
lines (P1$rgb, yfit, col ="red")
# Now calculate the 0-255 data points from the generated row vector.

##############################################################################################################
# set the output file # use to save sequence.
#outlist<-cbind(row,yfit)
#This still put out data with an index
write.table(yfit, file = "interpolated_values.csv", sep = ",", col.names = NA, qmethod = "double") # may also need row.names=NA or F to suppress row position


