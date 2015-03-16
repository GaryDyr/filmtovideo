demo(loessrun1)
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
# call input data P1 two columns with header names: row, lum
 P1<-read.csv("lum2correctionfit.csv", header = TRUE) 
nrow(P1)
ncol(P1)
# capture the output of the loess summary
# sink("lumcorr2.out")
plot(P1$row,P1$lum)
# Adjust span to get the smoothed data
fit<-loess(P1$lum~P1$row, span = 0.30)
pred.lum<-predict(fit,P1$row)
lines (P1$row, pred.lum, col ="red")
yfit.lum<-fitted(fit)
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
outlist<-cbind(P1,yfit.lum)
write.table(outlist, file = "luminanceloessfit.csv", sep = ",", col.names = NA, qmethod = "double") # may also need row.names=NA or F to suppress row position


