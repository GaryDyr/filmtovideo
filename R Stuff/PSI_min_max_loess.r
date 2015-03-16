demo(loessrun1)
#requires package earth be available; get from CRAN
 #store the current directory
 #to run a .r file from console do: source("my_script.R")

 initial.dir<-getwd()
 # change to the new directory
 setwd("C:/Canon/R Stuff") # change this to working directory with data
 # load the necessary libraries
 #library(earth)
 # Are we in the right working directory?
 getwd()
 # What files are there?
 #list.files(path = ".") # list working directory files
 #P1 	# three columns: row, xmin, and xmax
 P1<-read.csv("PSIminmax.csv", header = TRUE) 
nrow(P1)
ncol(P1)
#capture the output of the loess summary
#sink("PSI_regimes.out")
plot(P1$row,P1$xmax)
fit<-loess(P1$xmax~P1$row, span = 0.10)
pred.max<-predict(fit,P1$row)
lines (P1$row, pred.max, col ="red")
yfit.max<-fitted(fit)
fit2<-loess(P1$xmin~P1$row, span = 0.10)
pred.min<-predict(fit2,P1$row)
lines(P1$row, pred.min, col ="red")
yfit.min<-fitted(fit2)
#shut off data capture
#sink()
# Prints out the printed numbers.
#residuals(fit) # Prints residuals
##############################################################################################################
# set the output file # use to save sequence.
#sink("earthfit.out")
#output better

outlist<-cbind(P1,yfit.max, yfit.min)
write.table(outlist, file = "luminance loess fit.csv", sep = ",", col.names = NA, qmethod = "double") # may also need row.names=NA or F to suppress row position


