#Basic stalkless testing
#Will Pearse - 2014-08-27

#Setup
import pytest, sys
sys.path.append("..")
sys.path.append(".")
from stalkless import *

def test_loadFile():
    #Basics
    image, resolution = loadFile("image")
    assert resolution == 200
    assert image.shape == (1400,851)
    assert image.max() == 241
    assert image.min() == 0

    #Exclusion
    image, resolution = loadFile("image", [0,0,100,0])
    assert image.shape == (1300,851)
    image, resolution = loadFile("image", [0,100,0,0])
    assert image.shape == (1400,751)


def test_thresholdImage():
    #Auto
    image, resolution = loadFile("image")
    auto = thresholdImage(image)
    assert auto.shape == image.shape
    assert auto.max() == True
    assert auto.min() == False
    assert auto.sum() == 33124
    
    #nObjects
    nobj = thresholdImage(image, nObjects=3)
    assert auto.max() == True
    assert auto.min() == False
    assert nobj.sum() == 24071

    #maxObjects
    maxobj = thresholdImage(image, nObjects=5)
    assert auto.max() == True
    assert auto.min() == False
    assert maxobj.sum() == 27132


def test_segmentImage():
    #Auto (works badly)
    image, resolution = loadFile("image")
    auto = thresholdImage(image)
    auto = segmentImage(auto)
    assert [x.sum() for x in auto] == [503, 761, 465, 348, 433, 1213, 492, 9743, 357, 365, 282, 258, 319, 196, 1661, 6256, 5145, 2927]

    #nObjects
    nobj = thresholdImage(image, nObjects=3)
    nobj = segmentImage(nobj)
    assert [x.sum() for x in nobj] == [6256, 5145, 2927]


def test_morphologyStats():
    image, resolution = loadFile("image")
    image = thresholdImage(image, nObjects=3)
    image = segmentImage(image)[0]
    assert morphologyStats(image, resolution) == (4.991293864584921, 1.01449990234375, 0.1628867361160843, 24.556941193476455)

