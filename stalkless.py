#!/usr/bin/env python
# encoding: utf-8

#First draft of pipeline
#Will Pearse - 01/28/2013

#Headers
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage, misc
import argparse, sys, os, subprocess
from time import gmtime, strftime

#MAIN
def main():
    #Handle arguments
    args = parser.parse_args()
    if args.version:
        print "0.1a"
        sys.exit()
    
    if args.noObjects:
        noObjects = args.noObjects
    else:
        noObjects = 0
    
    if args.maxObjects:
        maxObjects = args.maxObjects
    else:
        maxObjects = 0
        
    if args.input[-1] != "/":
        args.input += "/"
    
    if args.output[-1] != "/":
        args.output += "/"

    #Load in image files
    try:
        files = os.listdir(args.input)
        files = [x for x in files if not x[0]=="."]
    except:
        print "ERROR: no valid input directory specified"
        sys.exit()
    
    #Load 'exclusion' if necessary
    if args.exclusion:
        try:
            exclusion = [int(x) for x in args.exclusion.split(",")]
            if len(exclusion) != 4:
                print "ERROR: invalid exclusion format. Remember to put in zero-length values too!"
                sys.exit()
        except:
            print "ERROR: invalid exclusion format. Remember to put in zero-length values too!"
            sys.exit()
    else:
        exclusion = 0

    print "\nStalkess v0.1a - Will Pearse (will.pearse@gmail.com)\n"
    
    #Loop over files
    print "Loading and processing images..."
    threshold_images = []
    os.chdir(args.input)
    for file in files:
        threshold_images.append(thresholdImage(loadFile(file, exclusion), noObjects, maxObjects))

    #Output
    print "Saving segmented images and surface areas..."
    os.chdir(args.output)
    with open("surfaceAreas.txt", "w") as saFile:
        for fileName,inputImage in zip(files, threshold_images):
            for i,segImage in enumerate(segmentImage(inputImage)):
                refName = saveFile(segImage, fileName, i)
                saFile.write(refName + "\t" + str(np.sum(segImage != 0)) + "\n")
    
    #Create R script
    print "Creating R analysis script..."
    os.chdir(args.output)
    makeRScript(args.output, args.output)

    #Run R script
    if args.analyseNow:
        print "Running R analysis script..."
        print "\t...this will likely crash. You were warned!"
        subprocess.call(['R', 'CMD', 'BATCH', 'rScript.R'])

    print "Finished!\n"
    
#Loading
def loadFile(fileName, exclusion=0):
    image = Image.open(fileName).convert("L")
    image = ImageOps.invert(image)
    image = np.array(image)
    if exclusion:
        if exclusion[0]: image = image[:-exclusion[0],:]#Bottom
        if exclusion[1]: image = image[:-exclusion[1],:]#Left
        if exclusion[2]: image = image[exclusion[2]:,:]#Top
        if exclusion[3]: image = image[exclusion[3]:,:]#Right
    
    return image

#Saving
def saveFile(image, fileName, suffix="", checkName=True):
    #Don't remove extensions you don't know for fear of ruining weird naming conventions (not an exhaustive list!)
    if checkName:
        if fileName[-4:] == ".png" or fileName[-4:] == ".jpg" or fileName[-4:] == ".gif" or fileName[-4:] == ".bmp" or fileName[-4:] == ".png" or fileName[-4:] == ".jpe":
            fileName = fileName[:-4] + "_" + str(suffix) + ".jpg"
        elif fileName[-5:] == ".jpeg":
            fileName = fileName[:-5] + "_" + str(suffix) + ".jpg"
        else:
            fileName = fileName + "_" + str(suffix) + ".jpg"
            print "...", fileName, "is a JPEG - sorry about the weird filename"
    misc.imsave(fileName, (1-np.uint8(image))*255)
    return fileName

    
#Thresholding
def thresholdImage(image, nObjects=0, maxObjects=0):
    threshold = np.mean(image) + np.std(image)
    thresh_image = image >= threshold
    label_objects, nb_labels = ndimage.label(thresh_image)
    sizes = np.bincount(label_objects.ravel())
    sizes[0] = 0#the background isn't a thing!
    #Use number of objects in image if known
    #Else, (rather stupidly) assume that the distribution of label sizes will be skewed enough to allow you to ignore those above a certain size
    
    if nObjects > 0:
        mask_sizes = np.array([x in sizes[sizes.argsort()][- nObjects:] for x in sizes])
    elif maxObjects > 0:
        mask_sizes = (len(sizes) -1 -sizes.argsort().argsort()) < maxObjects
        #Ugh. There's got to be a better way than this...
        sizeFilter = sizes > (np.mean(sizes) + np.std(image)*2)
        for i in range(len(mask_sizes)):
            if sizeFilter[i]==False:
                mask_sizes[i]=0
        
    else:
        mask_sizes = sizes > (np.mean(sizes) + np.std(image)*2)
    
    return mask_sizes[label_objects]

#Segmenting before output
def segmentImage(image):
    label_objects, nb_labels = ndimage.label(image)
    sizes = np.bincount(label_objects.ravel())
    outputImages = []
    for i in range(2, nb_labels+1):
        temp = label_objects ==i
        temp = temp[:, np.sum(temp, axis=0)>0]
        temp = temp[np.sum(temp, axis=1)>0,:]
        outputImages.append(temp)
    
    return outputImages

#R Script
def makeRScript(imageDir, outputDir):
    with open("rScript.R", 'w') as rScript:
        rScript.write("#Script automatically generated by stalkess - " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "\n")
        rScript.write("\n")
        rScript.write("#Headers\n")
        rScript.write("library(Momocs)\n")
        rScript.write("library(ReadImages)\n")
        rScript.write("\n")
        rScript.write("#Load images\n")
        rScript.write("images <- list.files('" + imageDir + "')\n")
        rScript.write("images <- images[!grepl('rScript.R', images, fixed=TRUE)]\n")
        rScript.write("images <- images[!grepl('surfaceAreas.txt', images, fixed=TRUE)]\n")
        rScript.write("images <- paste('" + imageDir + "', images, sep='')\n")
        rScript.write("images <- import.jpg(images)\n")
        rScript.write("images <- Coo(images)\n")
        rScript.write("\n")
        rScript.write("#Fourier analysis\n")
        rScript.write("fourier <- eFourier(images)\n")
        rScript.write("hcontrib(fourier)\n")
        rScript.write("\n")
        rScript.write("#Outer edge lengths\n")
        rScript.write("outer.edge <- sapply(images@coo, function(x) sum(sqrt((x[-1,1]-x[-nrow(x),1])^2 + (x[-1,2]-x[-nrow(x),2])^2)))\n")
        rScript.write("\n")
        rScript.write("#Save workspace\n")
        rScript.write("save.image('" + outputDir + "workspace.RData')\n")


#Argument parsing
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="stalkless, or learn to stop worrying and love leaf morphometrics.", epilog="Written by Will Pearse (will.pearse@gmail.com) for the Cavender-Bares Lab")
	parser.add_argument("--version", action="store_true", help="Display version information.")
	parser.add_argument("-output", help="Working directory for all output files", required=True)
        parser.add_argument("-input", help="Folder containing nothing but input images", required=True)
        parser.add_argument("-noObjects", help="How many objects in each image?", type=int)
        parser.add_argument("-maxObjects", help="Maximum number of objects in each image? (used in conjunction with image detection so you're not guaranteed this many images)", type=int)
        parser.add_argument("-exclusion", help="Comma-separated BOTTOM,LEFT,RIGHT,TOP no. of pixels to ignore in image")
        parser.add_argument("-analyseNow", action="store_true", help="Run R analysis script immediately (*highly* not recommended!")
	main()
