#Basis R script for pipeline
#Will Pearse - 29/1/2013

#Headers
library(Momocs)
library(ReadImages)

#Load images
images <- list.files("IMAGE_DIRECTORY")
images <- Coo(images)

#Fourier analysis
fourier <- eFourier(images)

#Outer edge lengths
outer.edge <- sapply(images@coo, function(x) sum(sqrt((x[-1,1]-x[-nrow(x),1])^2 + (x[-1,2]-x[-nrow(x),2])^2)))

#Save workspace
save.image("OUTPUT_DIRECTORY/workspace.RData")