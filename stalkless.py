#!/usr/bin/env python3
# encoding: utf-8

#Headers
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage, misc
import argparse, sys, os, subprocess, platform
from time import gmtime, strftime
from skimage.measure import perimeter, regionprops
from skimage.morphology import convex_hull_image
from math import pi
import shutil
import imageio
import pdb

#MAIN
def main():
    #Figure out OS for directory listings, etc.
    if platform.system() == "Windows":
        os_directory_symbol = '\\'
    else:
        os_directory_symbol = "/"
    
    #Store starting working directory
    default_wd = os.getcwd() + os_directory_symbol
    #Handle arguments
    args = parser.parse_args()
    if args.version:
        print("0.3")
        sys.exit()
    
    if args.maxObjects:
        maxObjects = args.maxObjects
    else:
        maxObjects = 0
    
    if args.failObjects:
        failObjects = args.failObjects
    else:
        failObjects = None
    
    if args.input or args.files:
        if args.input:
            if args.input[-1] != os_directory_symbol:
                args.input += os_directory_symbol
            try:
                files = os.listdir(args.input)
                files = [x for x in files if not x[0]=="."]
                input_dir = args.input
            except:
                print("ERROR: no valid input directory specified")
                sys.exit()
        if args.files:
            try:
                files = []
                with open(args.files) as inputFiles:
                    for each in inputFiles:
                        files.append(each.strip())
            except:
                print("ERROR: can't load list of files to be read")
                sys.exit()
    else:
        print("ERROR: must specify either an input directory, or a list of files to be read")
        sys.exit()
    
    
    if args.output[-1] != os_directory_symbol:
        args.output += os_directory_symbol
    output_dir = args.output
    image_dir = args.output + "processed_images/"

    noObjects = []
    if args.noObjects and args.exactObjects:
        print("ERROR: Cannot specify a file with number of objects and the number of objects!")
        sys.exit()
    
    if args.exactObjects:
        try:
            with open(args.exactObjects) as inputFiles:
                for each in inputFiles:
                    noObjects.append(int(each.strip()))
        except:
            print("ERROR: something went wrong loading how many objects in each image. Check file and location")
            sys.exit()
        if len(noObjects) != len(files):
            print("ERROR: number of files does not match expected number of images in those files")
            sys.exit()
    elif args.noObjects:
        noObjects = [int(args.noObjects) for x in range(len(files))]
    else:
        noObjects = [0 for x in range(len(files))]
    
    #Load 'exclusion' if necessary
    if args.exclusion:
        try:
            exclusion = [int(x) for x in args.exclusion.split(",")]
            if len(exclusion) != 4:
                print("ERROR: invalid exclusion format. Remember to put in zero-length values too!")
                sys.exit()
        except:
            print("ERROR: invalid exclusion format. Remember to put in zero-length values too!")
            sys.exit()
    else:
        exclusion = 0

    print("\nStalkess v0.3 - Will Pearse (will.pearse@gmail.com)")
    print(" - remember to use *full* paths in all input, or you'll get strange errors!")
    print(" - I make no guarantees this software works! You have been warned!")
    print("")
    #Loop over files, so as to save memory (my laptop 'only' has 8Gb of RAM...)
    print("Processing and segmenting images...")
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
    statistics = []
    original_files = []
    new_files = []
    try:
        os.mkdir(image_dir)
    except OSError:
        print("\nERROR: Cowardly refusing to overwrite existing stalkless output...")
        sys.exit()
    
    for file_no,file_name in enumerate(files):
        progress = file_no / each_segment
        if progress != current_bar:
            current_bar = progress
            sys.stdout.write(".")
            sys.stdout.flush()
        if args.input:
            os.chdir(input_dir)
        image, resolution = loadFile(file_name, exclusion)
        thresholded = thresholdImage(image, noObjects[file_no], maxObjects)
        os.chdir(image_dir)
        try:
            for i,segImage in enumerate(segmentImage(thresholded)):
                if args.fill:
                    #Note: need to change internal structure for conv. hull method
                    segImage = convex_hull_image(np.array(segImage, order="C"))
                file_name = file_name.split(os_directory_symbol)[-1]
                original_files.append(file_name)
                new_files.append(saveFile(segImage, file_name, i))
                statistics.append(morphologyStats(segImage, resolution))
        except RuntimeError:
            print("failObjects threshold reached for", file_name, "...")
    
    sys.stdout.write(".\n")
    #Write out the statistics
    print("Writing out statistics...")
    os.chdir(output_dir)
    with open("statistics.txt", "w") as saFile:
        saFile.write("\t".join(["original.file", "seg.file", "perimeter", "surface.area", "dissection", "compactness"])+"\n")
        for i,file_name in enumerate(original_files):
            saFile.write("\t".join([file_name, new_files[i], "\t".join([str(statistics[i][0]),str(statistics[i][1]),str(statistics[i][2]),str(statistics[i][3])])]) + "\n")
    
    
    #Create R script
    print("Creating R analysis script...")
    os.chdir(output_dir)
    makeRScript(image_dir, output_dir, default_wd)
    
    #Run R script
    if args.analyseNow:
        print("Running R analysis script...")
        print("\t...this will likely crash. You were warned!")
        subprocess.call(['R', 'CMD', 'BATCH', 'rScript.R'])
    
    print("Finished!\n")

#Loading
def loadFile(fileName, exclusion=0):
    image = Image.open(fileName).convert("L")
    resolution = image.info['dpi']
    image = ImageOps.invert(image)
    image = np.array(image)
    if exclusion:
        #Check dimensions of image match the exclusion
        if exclusion[0]+exclusion[2] < image.shape[0] and exclusion[1]+exclusion[3] < image.shape[1]:
            if exclusion[0]: image = image[:-exclusion[0],:]#Bottom
            if exclusion[1]: image = image[:,:-exclusion[1]]#Left
            if exclusion[2]: image = image[exclusion[2]:,:]#Top
            if exclusion[3]: image = image[:,exclusion[3]:]#Right
        else:
            print("\nImage", fileName, "too small to perform exclusion; processing unaltered")
    
    return image, resolution[0]

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
            print("...", fileName, "is a JPEG - sorry about the weird filename")
    imageio.imwrite(fileName, (1-np.uint8(image))*255)
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
def segmentImage(image, failThresh=None):
    label_objects, nb_labels = ndimage.label(image)
    if failThresh != None and len(nb_labels) >= failThresh:
        raise RuntimeError
    sizes = np.bincount(label_objects.ravel())
    outputImages = []
    #Loop over images, ignoring the background
    for i in range(1, nb_labels+1):
        temp = label_objects ==i
        temp = temp[:, np.sum(temp, axis=0)>0]
        temp = temp[np.sum(temp, axis=1)>0,:]
        outputImages.append(temp)
    
    return outputImages

def fillHoles(thresh_image, orig_image):
    #Find background in original image
    threshold = np.mean(image) + np.std(image)
    thresh_image = image >= threshold
    label_objects, nb_labels = ndimage.label(thresh_image)
    sizes = np.bincount(label_objects.ravel())
    sizes[0] = 0
    #XOR the background from the image to find the holes
    # - at some point in the future...

#Calculate simple image statistics
def morphologyStats(image, res):
    perim = (float(perimeter(image)) / res) * (2.0 + 35.0/64.0)
    area = (float(np.sum(image != 0)) / (res**2)) * ((2.0 + 35.0/64.0)**2)
    dissection = (4 * area) / (perim ** 2)
    compactness = (perim ** 2) / area
    return (perim, area, dissection, compactness)

#R Script
def makeRScript(imageDir, outputDir, origDir):
    date_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    r_template = "".join(open(origDir + 'r_template.R').readlines())
    r_template = r_template.replace("DATETIME", date_time)
    r_template = r_template.replace("IMAGEDIRECTORY", imageDir)
    r_template = r_template.replace("OUTPUTDIRECTORY", outputDir)
    shutil.copy(origDir+"stalkless_headers.R", outputDir+"stalkless_headers.R")
    with open("fourier_script.R", 'w') as rScript:
        rScript.write(r_template)

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
    parser.add_argument("-fill", action="store_true", help="Fill holes in leaf using convex hull algorithm.")
    parser.add_argument("-failObjects", help="Abort processing image if this many potential images detected")
    main()


#thresholded = thresholdImage(loadFile("/home/will/Documents/leaves/raw_data/Sam_et_al/Minnesota/MinnesotaScans/Minneota_A 03-06-2013 1.png"))
        
