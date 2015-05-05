stalkless
=========
Will Pearse (wdpearse@umn.edu)
[![DOI](https://zenodo.org/badge/4348/willpearse/stalkless.svg)](http://dx.doi.org/10.5281/zenodo.17364)

This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

The Cavender-Bares lab's (and friends'!) leaf analysis pipeline

##Easy use
* Download a pre-packaged binary for Mac (Windows coming soon when I have administrative rights on a PC)
* Mac: From within Terminal, run the file 'stalkless.app/Contents/MacOS/stalkless' - note that double clicking the application will generate an error! For example, if I'd installed stalkless into my home directory, I'd type '/Users/will/stalkless.app/Contents/MacOS/stalkess' in Terminal to run it.
* PC: Follow the instructions below for compiling the dependencies, then (from command prompt) type "python stalkless.py"
* Linux: Follow the instructions below for compiling the dependencies, then (from a terminal) type "python stalkless.py"

##'Compiling' it
Short answer: Install Python >=2.6; Numpy and SciPy for Python; Biopython >=2.5. Set up a folder ('requires') in the same folder as 'phyloGenerator.py' that contains the programs you'll use - check http://willpearse.github.com/phyloGenerator/install.html#compiling for the names of the programs.
Long answer: go to http://willpearse.github.com/phyloGenerator/install.html

##Examples
The website (http://willpearse.github.com/stalkless) should have more examples, but on my computer:
./stalkless.py -output /Users/will/firstAttempt -input /Users/will/leafImages -exclusion 0,0,500,0
Loads all image files in the 'leafImags' folder, excludes the top 500 pixels of every image (BOTTOM,LEFT,TOP,RIGHT is the 'exclusion' format) and puts all the output in the 'firstAttempt' folder.
./stalkless.py -output /Users/will/firstAttempt -input /Users/will/leafImages -exclusion 0,0,500,0 -maxObjects 5
Loads all the image files, as before, but also ensures that there are (at most) only five images in the output. Note that, because this option is used in conjunction with the default image thresholding, you may get fewer than the number of images you specify. This is not a problem!
Inside that 'firstAttempt' folder, you will find an R script that will run Fourier analyses of all your leaves. You can use the '-analyseNow' flag to run that from within stalkless, but I *strongly* advise against doing so, because under certain circumstances (a dodgy image, a different leaf of leaf) the Fourier analysis may not run. You will want to check your images first! This script will also calculate edge length (in pixels).
You will also find a 'surfaceArea.txt' file that contains the surface areas of your images (in pixels).
You can also use '-noObjects 2' to specify how many objects are in your scans. If this number is constant, I'd recommend you do so.

#Features:
Clearly, this script will not do everything you want. If you have any feature request, please *put them online* at https://github.com/willpearse/stalkless/issues. I would *much rather* an online request than an email!

#Bugs:
If the script simply won't run, make a bug report at https://github.com/willpearse/stalkless/issues. I'm actively looking for cases where the script doesn't properly segment images - send such examples to me through email (will.pearse@gmail.com)

#Citation:
Contact me when that time comes.

Happy leafing!

Will Pearse (wdpearse@umn.edu)