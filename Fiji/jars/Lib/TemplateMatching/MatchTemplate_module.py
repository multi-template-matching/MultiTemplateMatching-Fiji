'''

This script contains the function to make template matching between a template and an image. 
This implementation is compatible with the smart imaging but also with the macro version (in this case the GUI is done with script parameters) 
The detected area will be displayed as a rectangular ROI on the image, and this ROI will be added to the ROI manager 
The found area will also be saved in a subfolder "Found" of the image folder if the option is ticked. 
 
A limited search area can be provided by adding a ROI to the ROI manager. This ROI must be the first in the ROI manager (selected by position). It will be rename to searchROI 
This is especially important when running the macro several time : delete the previously detected ROI 
There should not be any other ROI in addition ot this search ROI otherwiose the displayed ROI will be mispositionned in the resulting stack 
 
NB : 
- all target images should have the same size since they are appended to a stack 
 
Requirements : 
- IJ-OpenCV (from the updater) 
 
TO DO : 
- Images with overlay in Stack : change to the easier ij.plugin.ImagesToStack that use a list to make the stack. No need to precise the size.. 
- Found image in stacks and save the stack at the end (add a Terminate() function). currently the template are saved as separate images 
 
- Make a function that generate and return the GUI object, and a second one that opens this GUI (could be used to reuse the GUI for the non smart imaging): Maybe once we use the Pref service instead of file	
 '''
# Python
from __future__		import division 

# OpenCV
from org.bytedeco.javacpp.opencv_imgproc import matchTemplate, threshold, CV_THRESH_TOZERO
from org.bytedeco.javacpp.opencv_core	 import Mat, Scalar, Point, minMaxLoc, subtract # UNUSED normalize, NORM_MINMAX, CV_8UC1, CV_32FC1
from org.bytedeco.javacpp				 import DoublePointer 

# ImageJ
from ij					import IJ # , ImagePlus, ImageStack 
from ij.plugin.filter	import MaximumFinder
#from ij.gui			import Roi, PointRoi 


# Java
from java.lang 	import Float #used to convert BytesToFloat

# Home-made module in jars/Lib sent with Acquifer update site 
from ImageConverter import ImProcToMat, MatToImProc
from ImageRotator 	import Rotate


  
  
def MatchTemplate(ImProc_Template, ImProc_Target, Method):  
	'''
	Function that performs the matching between one template (opencv matrix) and an image (ImagePlus)  
	ImProc_Template : ImageProcessor object of the template image   
	ImProc_Target	: ImageProcessor object of the image in which we search the template   
	Method		: Integer for the tempate matching method (openCV)  
	return the correlation map 
	'''
	# Convert to image matrix, 8-bit (if both are 8-bit) or 32-bit 
	if ImProc_Template.getBitDepth()==8 and ImProc_Target.getBitDepth()==8: 
		ImTemplateCV = ImProcToMat(ImProc_Template, Bit=8) 
		ImTargetCV	 = ImProcToMat(ImProc_Target, Bit=8) 
	else: 
		ImTemplateCV = ImProcToMat(ImProc_Template, Bit=32) 
		ImTargetCV	 = ImProcToMat(ImProc_Target, Bit=32) 
	 
	# Create a correlation map object and do the matching  
	CorrMapCV = Mat()  
	matchTemplate(ImTargetCV, ImTemplateCV, CorrMapCV, Method)	# result directly stored in CorrMap  
	 
	return CorrMapCV 
 


def FindMinMax(CorrMapCV, Unique=True, MinMax="Max", Score_Threshold=0.5, Tolerance=0.1):
	'''
	Detect Minima(s) or Maxima(s) in the correlation map
	The function uses for that the MinMaxLoc from opencv for unique detection 
	or the MaximumFinder from ImageJ for multi-detection (in this case, for min detection the correlation map is inverted)
	
	- Unique			: True if we look for one global min/max, False if we want local ones
	- MinMax 			: "Min" if we look for Minima, "Max" if we look for maxima
	- Score_Threshold 	: in range [0;1] (correlation maps are normalised)
	
	Returns List of Min/Max : [(X, Y, Coefficient), ... ]
	'''
	#### Detect min/maxima of correlation map ####
	Extrema = [] 
	
	## if 1 hit expected
	if Unique: # Look for THE global min/max
		minVal = DoublePointer(1) 
		maxVal = DoublePointer(1) 
		minLoc = Point() 
		maxLoc = Point() 
		minMaxLoc(CorrMapCV, minVal, maxVal, minLoc, maxLoc, Mat())
		
		if MinMax=="Min": # For method based on difference we look at the min value 
			X = minLoc.x() 
			Y = minLoc.y()
			Coeff = minVal.get() 
	 
		elif MinMax=="Max": 
			X = maxLoc.x() 
			Y = maxLoc.y()
			Coeff = maxVal.get()
		
		# Append to the output list
		Extrema.append( (X, Y, Coeff) )
		
		
	
	## if more hit expected
	else: # expect more than 1 template/image. Do a multi minima/maxima detection
		
		## OLD CODE LEFT BUT DONT DO IT, NOT GOOD PREACTICE !! Normalise the correlation map to 0-1 (easier to apply the threshold)
		## Rather use normalised method only for the computation of the correlation map (by default normalised method are 0-1 bound)
		# The normalised method are already normalised to 0-1 but it is more work to take it into account in this function 
		# WARNING : this normalisation normalise regarding to the maxima of the given correlation map
		# Not good because it means the thresholding is define relative to a correlation map : a score of 1 might not correspond to a correlation of 1
		# But only means that the pixel was the maximum of this particular correlation map 
		
		#CorrMapNormCV = Mat()
		#normalize(CorrMapCV, CorrMapNormCV, 0, 1, NORM_MINMAX, CV_32FC1, None)

		# Visualisation for debugging
		#CorrMapNorm = MatToImProc(CorrMapNormCV)
		#CorrMapNorm = ImagePlus("Normalised", CorrMapNorm)
		#CorrMapNorm.show()

		
		
		### Maxima/Minima detection on the correlation map
		
		## Difference-based method : we look for min value. For that we detect maxima on an inverted correlation map
		if MinMax=="Min": 
			
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
			threshold(CorrMapInvCV, CorrMapThreshCV, 1-Score_Threshold, 0, CV_THRESH_TOZERO)
			CorrMapThresh = MatToImProc(CorrMapThreshCV) # Keep this conversion, not only for visualisation
			#CorrMapThreshImp = ImagePlus("Thresholded", CorrMapThresh)
			#CorrMapThreshImp.show()
			

		
		## Correlation-based method : we look for maxima
		elif MinMax=="Max": 
			# Apply a "TO ZERO" threshold on the correlation map : to compensate the fact that maxima finder does not have a threshold argument
			# TO ZERO : below the threshold set to 0, above left untouched
			# NB : 1-score_threshold since we have inverted the image : we want to look for minima of value <x so we have to look for maxima of value>1-x in the inverted image
			CorrMapThreshCV = Mat()
			threshold(CorrMapCV, CorrMapThreshCV, Score_Threshold, 0, CV_THRESH_TOZERO)
			CorrMapThresh = MatToImProc(CorrMapThreshCV) # Keep this conversion, not only for visualisation
			#CorrMapThreshImp = ImagePlus("Thresholded", CorrMapThresh)
			#CorrMapThreshImp.show()
			
		
		
		## For both cases (Multi-Min/Max-detection) detect maxima on the thresholded map
		if CorrMapThresh.getMax()!=0: # Check if image is completely black (kind of fix for https://github.com/imagej/imagej1/issues/74 )
			
			# Detect local maxima
			excludeOnEdge = False # otherwise miss quite a lot of them
			Polygon = MaximumFinder().getMaxima(CorrMapThresh, Tolerance, excludeOnEdge)
			
			# Maxima as list of points
			#roi = PointRoi(Polygon)
			
			# Generate Hit from max coordinates
			for X,Y in zip(Polygon.xpoints, Polygon.ypoints):
			
				# Get point coordinates
				#X, Y = point.getX(), point.getY()

				# Get Coeff
				Coeff = CorrMapThresh.getPixel(int(X), int(Y))
				Coeff = Float.intBitsToFloat(Coeff) # require java.lang.Float
				
				# Revert the score again if we were detecting minima initially (since found as maxima of a reverted correlation map)
				if MinMax=="Min":
					Coeff = 1-Coeff
				
				# Wrap into corresponding hit
				Extrema.append( (X, Y, Coeff) )
	
	return Extrema

	
	
	
def getHit_Template(ImpTemplate, ImpImage, FlipV=False, FlipH=False, Angles='', Method=5, N_Hit=1, Score_Threshold=0.5, Tolerance=0.1):
	'''
	This function performs :
	1) Preprocessing of the template (flipping and/or rotation)
	2) Template matching for each of those template
	4) Then for each correlation map, Min/Max detection and Non-Maxima Suppression (NMS)
	NB : It does not do the NMS between correlation map, only for a given correlation map (intra-NMS)
	The inter-NMS still remains to be done, it is not included in the function because other templates/hits might be used
	
	
	- ImProc_Template : ImageProcessor object of the template image   
	- ImProc_Image    : ImageProcessor object of the image in which we search the template   
	- FlipV/H         : Boolean, search for additional vertical/horizontal flipped version of the template 
 	- Angles          : String like "10,20,50" - angles to search for additional rotated version of the template (both initial and flipped template are rotated) 
	- Method		  : Integer for the template matching method (openCV) 
	- N_Hit           : Expected number of templates in the image
	- Score_Threshold : respectively Min/Max value for the detection of Maxima/Minima in the correlation map 
	- Tolerance       : peak height relative to neighbourhood for min/max detection (only used if N_hit>1)
	- Max_Overlap     : Max overlap (Intersection over Union, IoU) between bounding boxes used for NMS
	
	It returns a list of hit [ {TemplateName, BBox, Score}, ..., ]
	'''
	# Get ImageProcessor for template and image
	ImProc_Template = ImpTemplate.getProcessor()
	ImProc_Image    = ImpImage.getProcessor()
	
	# Get Image names for template and image
	TemplateName = ImpTemplate.getTitle()
	ImageName    = ImpImage.getTitle() 
	
	ListTemplate = [ {"Name":TemplateName, "ImProc":ImProc_Template} ] # initialise list with initial template
	
	## Pre-Process template (Flip and/or Rotation)
	# Flip vertical 
	if FlipV:
		TemplateFlipV = ImProc_Template.duplicate()
		TemplateFlipV.flipVertical() # duplicate previously to prevent in-place change
		ListTemplate.append( {"Name":TemplateName+"_Vertical_Flip", "ImProc":TemplateFlipV} )

	# Flip horizontal
	if FlipH:
		TemplateFlipH = ImProc_Template.duplicate()
		TemplateFlipH.flipHorizontal() # duplicate previously to prevent in-place change
		ListTemplate.append( {"Name":TemplateName+"_Horizontal_Flip", "ImProc":TemplateFlipH})


	# Rotation (initial and flipped templates)
	if Angles: # if different than an empty string 
		
		# Recover individual angle values 
		Angles = Angles.split(",")
		Angles = list(map(int, Angles)) # # convert to int. map returns a list in Py2 but an iterator in Py3 hence the list conversion for max compatibility 
		#print Angles 

		# copy before appending any rotated ones. ie only contains initial + flipped ones
		ListToRotate = ListTemplate[:] 
		
		# Loop over list of angles
		for angle in Angles: 
			
			# Loop over initial and flipped template and rotate each template in input list
			for template in ListToRotate: # template is a dictionnary here
				
				TemplateName = template['Name'] # it can be original or with "_flipX"
				
				# Perform the rotation
				Rotated = Rotate(template['ImProc'], angle)
				
				# Check that the rotated template still fits in the search area 
				if searchROI and (searchROI.getFloatWidth()<Rotated.width or searchROI.getFloatHeight()<Rotated.height): 
					IJ.log(TemplateName + " rotated by" + str(angle) + " degrees does not fit into the search area anymore. Cropped down")
				
					# Crop down to the size of the searchROI, starting from the top left corner 
					Rotated.setRoi(0,0,int(MaxWidth),int(MaxHeight)) 
					Rotated = Rotated.crop() 					
				
				# Append to the list of templates
				ListTemplate.append( {"Name": TemplateName + "_" + str(angle) + 'degrees', "ImProc":Rotated} )	


	### Loop over template to do the matching ####
	List_Hit = []
	for template in ListTemplate: # template is a dico here

		## Search the current template in the image -> Correlation Map ###
		CorrMapCV = MatchTemplate(template["ImProc"], ImProc_Image, Method) 
		#CorrMap = MatToImProc(CorrMapCV)
		#CorrMap = ImagePlus("CorrMap", CorrMap)
		#CorrMap.show()


		#### Detect min/maxima of correlation map ####
		if N_Hit==1: 
			Unique = True
		else:
			Unique = False
		
		if Method in [0,1]:
			MinMax="Min"
		else:
			MinMax="Max"
		
		List_XYCoeff  = FindMinMax(CorrMapCV, Unique, MinMax, Score_Threshold, Tolerance)
		List_NewHit   = [ { "ImageName":ImageName,
							"TemplateName":template["Name"], 
							"BBox":(x, y, template['ImProc'].width, template['ImProc'].height), 
							"Score":Coeff} for x,y,Coeff in List_XYCoeff ] 
		
		# Append Hit for this particular template to the list of output hit 
		List_Hit.extend(List_NewHit)
	
	# Return list of Hits
	return List_Hit
	

	
def CornerToCenter(Xcorner, Ycorner, TemplateWidth, TemplateHeight): 
	''' Convert from top left pixel to center pixel of detected ROI''' 
	 
	Xcenter = Xcorner + TemplateWidth//2 
	Ycenter = Ycorner + TemplateHeight//2 
	 
	return Xcenter,Ycenter