demo(earthrun1)
#requires package earth be available; get from CRAN
 #store the current directory
 #to run a .r file from console do: source("my_script.R")

 initial.dir<-getwd()
 # change to the new directory
 setwd("C:/Canon/Curve Fitting Methods-Other") # change this to working directory with data
 # load the necessary libraries
 library(earth)
 # Are we in the right working directory?
 getwd()
 # What files are there?
 list.files(path = ".") # list working directory files
 PSI1<-read.csv("PSIposandN.csv", header = TRUE) 	 # Frame type data
 PSI2<-read.csv("PSIposandN2.csv", header = TRUE) 	# Running Row data, not frame data.
  # Check the data frames - list the data
 # pos is the PSI position; nf is the PSI peak index
 PSI1 	# fractional observed frame PSI position versus PSI peak number
 PSI2 # observed running row versus PSI peak number 
##############################################################################################################
# The below set of lines represents about the best we can do against the original data; it is not pretty. (Output is not shown.)
 fit<-earth( pos ~., data = PSI2, nk = 100, nfold = 9, ncross = 100, degree = 2, trace = 0, penalty = -1, newvar.penalty = 0, glm = NULL,  
 thresh = 0, minspan = 2,  fast.k = 0, fast.beta = 0, pmethod =  "forward", nprune = NULL, Exhaustive.tol = 1e-10)
# plot(fit)
#capture the output of the earth summary
#sink("PSI_regimes.out")
cat("\nFilm Slice zzzz MARS analysis\n\n")
#Here cat() is used to label a breakdown of means, leaving a blank line above and two below the label. Spacing the output with meaningful labels 
#improves the appearance and comprehensibility. 

summary(fit, decomp = "none") # "none" to print terms in same seq as a.lm below
#this gives the coefficeints that show up in the summary from summary
fit$coefficients
fit$cuts
fit$dir
#shut off data capture
#sink()
#fitted(fit) # Prints out the printed numbers.
#residuals(fit) # Prints residuals
##############################################################################################################
# set the output file # use to save sequence.
#sink("earthfit.out")
#output better
write.table(x, file = "PSI_regimes.csv", sep = ",", col.names = NA, qmethod = "double")
#alternate write.csv(x, file = "PSI_regimes.csv")

# Interpolate the PSI range, by generating a sequence of whole numbers, i.e., PSI index numbers, 
# and do a linear interpolation against the original data onto this set; this is to only pad a small data set - not used.
#xset<-seq(min(PSI2$nf),max(PSI2$nf), by = 1)
#out1<-approx (x = PSI2$nf, y=PSI2$pos, xout=xset, method="linear") 	#out1 is a 2 col frame containing the PSI integer series 
# The call to earth below was designed to maximize the number of factors;  there was no backward pass. It also traced what limits were 
#  causing earth to stop, which streamed a lot of data to the screen.
# fit<-earth( y = out1$y, x= out1$x, nk = 100, nfold = 9, ncross = 100, degree = 2, trace = 1, penalty = -1, newvar.penalty = 0, glm = NULL,  #thresh = 0, minspan = 2,  fast.k = 0, fast.beta = 0, pmethod =  "forward", nprune = NULL) 
# The following call to earth was as sufficient to produce errors within the same range as the overdone forward pass call to earth in the 
# previous line, and even it is likely overkill with respect to the values of  nk, nfold, and ncross. However, with a small number of points, the 
# time to run was reasonable, and there was a bit more confidence that all the data would be captured. 
#fit<-earth( y = out1$y, x= out1$x, nk = 100, nfold = 9, ncross = 100, degree = 2,thresh = 0)
#summary(fit)
#need to parse the lines in python
#plot(fit)

