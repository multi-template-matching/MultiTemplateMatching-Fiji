#@ ImagePlus ("Label=Template") template
#@ ImagePlus ("Label=Image") image
#@ Float ("Score Threshold") score_threshold
#@ Float ("Tolerance") tolerance

'''
Compute correlation map between a template and an image
currently only the normalsied corss correlation used
'''
from ROIdetection.MatchTemplate_Module   import MatchTemplate
from org.bytedeco.javacpp.opencv_imgproc import threshold, CV_THRESH_TOZERO
from org.bytedeco.javacpp.opencv_core	 import Mat
from ImageConverter 					 import MatToImProc
from ij									 import ImagePlus 
from ij.plugin.filter					 import MaximumFinder

# Convert to ImageProcessor
TempProc = template.getProcessor()
ImProc   = image.getProcessor()

# Do matching
CorrMapCV = MatchTemplate(TempProc, ImProc, 5)
CorrMap = MatToImProc(CorrMapCV)
CorrMapImp = ImagePlus("Score Map", CorrMap)
CorrMapImp.show()

# Threshold the corrmap (below threshold 0, above left untouched)
CorrMapThreshCV = Mat()
threshold(CorrMapCV, CorrMapThreshCV, score_threshold, 0, CV_THRESH_TOZERO)

# Display
CorrMapThresh = MatToImProc(CorrMapThreshCV) # Keep this conversion, not only for visualisation
CorrMapThreshImp = ImagePlus("SCore Map - thresholded", CorrMapThresh)
CorrMapThreshImp.show()

## For both cases (Multi-Min/Max-detection) detect maxima on the thresholded map
excludeOnEdge = False # otherwise miss quite a lot of them
Polygon = MaximumFinder().getMaxima(CorrMapThresh, tolerance, excludeOnEdge)
print Polygon.xpoints