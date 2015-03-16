demo(mixtoosrun)
#requires package mixtools be available; get from CRAN
#store the current directory
#to run a .r file from console do: source("my_script.R")

initial.dir<-getwd()
# change to the new directory
setwd("C:/Canon/R Stuff") # change this to working directory with data
# load the necessary libraries
library(mixtools)
# Are we in the right working directory?
getwd()
# What files are there?
#list.files(path = ".") # list working directory files
#P1 will have three columns: row, max and min data is 1/2 1080
P1<-read.csv("luminance data div 2for mixtools.csv", header = TRUE) 
# Check if csv data seems okay
nrow(P1)
ncol(P1)
#capture the output of the l
#sink("PSI_regimes.out")
plot(P1$row,P1$max)
#"mvnormalmixEM(x, lambda = NULL, mu = NULL, sigma = NULL, k = 2,
#arbmean = TRUE, arbvar = TRUE, epsilon = 1e-08,
#"maxit = 10000, verb = FALSE)
x = cbind(P1$row,P1$max)
fit<-mvnormalmixEM(x, k=5)
summary(fit)
#found this for successive plots dnorm is std function (x is x or quantiles, mean, sd is list of standard deviations
#curve(expression or fcn, add true-add to existing plot in this case the function calcs the gaussian curve (dnorm) with given
#parameters

plot.normal.components <- function(mixture,component.number,...) {
  curve(mixture$lambda[component.number] * 
	dnorm(x,mean=mixture$mu[component.number],sd=mixture$sigma[component.number]), add=TRUE, ...)
}
sapply(1:4,plot.normal.components,mixture=fit)  'takes a vector and an expression
plot(P1$row,P1$max)
for (j in 1:4)
	lines(fit$row, fit$lambda[j]*dnorm(fit$row, mean=fit$mu[j], sd=fit$sigma), lwd=3, lty=2)
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


