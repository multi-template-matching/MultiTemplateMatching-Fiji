#@ ImagePlus ("Label=Template") template
#@ ImagePlus ("Label=Image") image
#@ String    (Label="Matching method",choices={"Normalised Square Difference", "Normalised cross-correlation", "Normalised 0-mean cross-correlation"}, value="Normalised 0-mean cross-correlation") method 
#@ Float ("Score Threshold", min=0, max=1, stepSize=0.1) score_threshold
'''
Compute correlation map between a template and an image
currently only the normalsied corss correlation used
'''
from Template_Matching.MatchTemplate_Module   import MatchTemplate
from org.bytedeco.javacpp.opencv_imgproc import threshold, CV_THRESH_TOZERO
from org.bytedeco.javacpp.opencv_core	 import Mat, Scalar, subtract
from ImageConverter 					 import MatToImProc
from ij									 import ImagePlus 
from ij.plugin.filter					 import MaximumFinder
from ij.gui			import Roi, PointRoi 

# Convert method string to the opencv corresponding index 
Dico_Method  = {"Square difference":0,"Normalised Square Difference":1,"Cross-Correlation":2,"Normalised cross-correlation":3,"0-mean cross-correlation":4,"Normalised 0-mean cross-correlation":5} 
Method       =  Dico_Method[method] 

# Convert to ImageProcessor
TempProc = template.getProcessor()
ImProc   = image.getProcessor()

# Do matching
CorrMapCV = MatchTemplate(TempProc, ImProc, Method)
CorrMap = MatToImProc(CorrMapCV)
CorrMapImp = ImagePlus("Score Map", CorrMap)
CorrMapImp.show()


# Threshold the corrmap (below threshold 0, above left untouched)
if Method==1: 
	# Invert the correlation map : min becomes maxima
	One = Scalar(1.0)
	CorrMapInvCV = subtract(One, CorrMapCV).asMat()		
	#CorrMapInv = MatToImProc(CorrMapInvCV)
	#CorrMapInv = ImagePlus("Inverted", CorrMapInv)
	#CorrMapInv.show()
	
	
	# Apply a "TO ZERO" threshold on the correlation map : to compensate the fact that maxima finder does not have a threshold argument
	# TO ZERO : below the threshold set to 0, above left untouched
	# NB : 1-score_threshold since we have inverted the image : we want to look for minima of value <x so we have to look for maxima of value>1-x in the inverted image
	CorrMapThreshCV = Mat()
	threshold(CorrMapInvCV, CorrMapThreshCV, 1-score_threshold, 0, CV_THRESH_TOZERO)
	#CorrMapThreshImp = ImagePlus("Thresholded", CorrMapThresh)
	#CorrMapThreshImp.show()
			
else:
	CorrMapThreshCV = Mat()
	threshold(CorrMapCV, CorrMapThreshCV, score_threshold, 0, CV_THRESH_TOZERO)

	
# Display
CorrMapThresh = MatToImProc(CorrMapThreshCV) # Keep this conversion, not only for visualisation
CorrMapThreshImp = ImagePlus("Score Map - thresholded", CorrMapThresh)
CorrMapThreshImp.show()

## For both cases (Multi-Min/Max-detection) detect maxima on the thresholded map
excludeOnEdge = False # otherwise miss quite a lot of them
tolerance = 0
Polygon = MaximumFinder().getMaxima(CorrMapThresh, tolerance, excludeOnEdge)
roi = PointRoi(Polygon)
CorrMapThreshImp.setRoi(roi)