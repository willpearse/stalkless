#!/usr/bin/env python
# encoding: utf-8

#First draft of pipeline
#Will Pearse - 01/28/2013

#Headers
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage, misc
import argparse, sys, os, subprocess, platform
from time import gmtime, strftime

#MAIN
def main():
    #Figure out OS for directory listings, etc.
    if platform.system() == "Windows":
        os_directory_symbol = '\\'
    else:
        os_directory_symbol = "/"
    #Handle arguments
    args = parser.parse_args()
    if args.version:
        print "0.2a"
        sys.exit()
    
    if args.maxObjects:
        maxObjects = args.maxObjects
    else:
        maxObjects = 0

    if args.input or args.files:
        if args.input:
            if args.input[-1] != os_directory_symbol:
                args.input += os_directory_symbol
            default_wd = args.input
            try:
                files = os.listdir(args.input)
                files = [x for x in files if not x[0]=="."]
            except:
                print "ERROR: no valid input directory specified"
                sys.exit()
        if args.files:
            default_wd = os.getcwd() + os_directory_symbol
            try:
                files = []
                with open(args.files) as inputFiles:
                    for each in inputFiles:
                        files.append(each.strip())
            except:
                print "ERROR: can't load list of files to be read"
                sys.exit()
    else:
        print "ERROR: must specify either an input directory, or a list of files to be read"
        sys.exit()
    
    
    if args.output[-1] != os_directory_symbol:
        args.output += os_directory_symbol

    noObjects = []
    if args.exactObjects:
        try:
            with open(args.exactObjects) as inputFiles:
                for each in inputFiles:
                    noObjects.append(int(each.strip()))
        except:
            print "ERROR: something went wrong loading how many objects in each image. Check file and location"
            sys.exit()
        if len(noObjects) != len(files):
            print "ERROR: number of files does not match expected number of images in those files"
            sys.exit()
    else:
        noObjects = [0 for x in range(len(files))]
    
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

    print "\nStalkess v0.2a - Will Pearse (will.pearse@gmail.com)"
    print " - remember to use *full* paths in all input, or you'll get strange errors!"
    print " - I make no guarantees this software works! You have been warned!"
    print ""
    #Loop over files, so as to save memory (my laptop 'only' has 8Gb of RAM...)
    print "Processing and segmenting images..."
    #Setup
    toolbar_width = 50
    each_segment = len(files) / toolbar_width
    #Beware if you've got fewer files than segments for the progress bar...
    if each_segment == 0:
        each_segment = 1
    sys.stdout.write("[%s]" % (" " * toolbar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (toolbar_width+1))
    current_bar = 0
    surface_areas = {}
    for file_no,file_name in enumerate(files):
        progress = file_no / each_segment
        if progress != current_bar:
            sys.stdout.write(".")
            sys.stdout.flush()
        os.chdir(default_wd)
        thresholded = thresholdImage(loadFile(file_name, exclusion), noObjects[file_no], maxObjects)
        os.chdir(args.output)
        for i,segImage in enumerate(segmentImage(thresholded)):
            file_name = file_name.split(os_directory_symbol)[-1]
            refName = saveFile(segImage, file_name, i)
            surface_areas[refName] = np.sum(segImage != 0)

    sys.stdout.write(".\n")
    #Write out the surface areas
    print "Writing out surface areas..."
    os.chdir(args.output)
    with open("surfaceAreas.txt", "w") as saFile:
        for file_name,s_a in surface_areas.iteritems():
            saFile.write(file_name + "\t" + str(s_a) + "\n")
        
    
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
        mask_sizes = np.array([x in sizes[sizes.argsort()][- (nObjects+1):] for x in sizes])
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
        rScript.write("images <- images[grepl('.jpg', images, fixed=TRUE)]\n")
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
        parser.add_argument("-input", help="Folder containing nothing but input images")
        parser.add_argument("-noObjects", help="How many objects in each image?", type=int)
        parser.add_argument("-maxObjects", help="Maximum number of objects in each image? (used in conjunction with image detection so you're not guaranteed this many images)", type=int)
        parser.add_argument("-exclusion", help="Comma-separated BOTTOM,LEFT,TOP,RIGHT no. of pixels to ignore in image")
        parser.add_argument("-analyseNow", action="store_true", help="Run R analysis script immediately (*highly* not recommended!")
        parser.add_argument("-files", help="A file with each file to be loaded on a separate line")
        parser.add_argument("-exactObjects", help="A file with the number of objects to be loaded in each file on each line. Must match '-files' or strange errors will occur!")
	main()
