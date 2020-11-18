#@ File[]    (Label="Templates", style="file") template_files   
#@ File[]    (label="Image for which to look for the template") image_files
#@ File 	 (label="Region of Interest (ROI) for search (optional)", required=false) roi_file
#@ Boolean   (Label="Flip template vertically") flipv 
#@ Boolean   (Label="Flip template horizontally") fliph 
#@ String    (Label="Additional rotation angles separated by ," ,required=False) angles 
#@ String    (Label="Matching method",choices={"Normalised Square Difference", "Normalised cross-correlation", "Normalised 0-mean cross-correlation"}, value="Normalised 0-mean cross-correlation") method 
#@ Integer   (Label="Expected number of objects", min=1) n_hit 
#@ String    (visibility="MESSAGE", value="The parameters below are used only if more than 1 template are expected in the image") doc 
#@ Float     (Label="Score Threshold", min=0, max=1, value=0.5, stepSize=0.1, style="slider") score_threshold 
#@ Float     (Label="Maximal overlap between Bounding boxes", min=0, max=1, value=0.4, stepSize=0.1, style="slider") max_overlap 
#@ String    (visibility="MESSAGE", value="Output") out 
#@ Boolean   (Label="Open images (as stack ie images must have identical dimensions)") show_images 
#@ Boolean   (Label="Add ROI to ROI Manager") add_roi 
#@ Boolean   (Label="Show result table") show_table
#@ String    (visibility="MESSAGE", value="<html><center>If you use this plugin please cite:<brThomas, L.S.V., Gehrig, J.<br>Multi-template matching: a versatile tool for object-localization in microscopy images.<br>BMC Bioinformatics 21, 44 (2020)<br>https://doi.org/10.1186/s12859-020-3363-7</center></html>") disclaimer 
'''
previous field : 
Float     (Label="Min peak height relative to neighborhood (0-1, decrease to get more hits)", min=0, max=1, value=0.1, stepSize=0.1) tolerance 
Boolean   (Label="Display correlation map(s)") show_map 

Object recognition using one or multiple template images 
ie this macro search for N templates (with eventual flipped/rotated version) into L target images. 

input : 
- template_files : list of template path 
- image_files    : list of image path for which we want to search a template 

First, additionnal versions of the template are generated (flip+rotation) if selected
Then each template is searched in the target image. This yield as set of correlation maps 
 
Minima/maxima in the correlation maps are detected, followed by Non-Maxima Supression when several object are explected in the target image
- matchTemplate Method limited to normalised method to have correlation map in range 0-1 : easier to apply a treshold.  

The search region can be limited to a rectangular ROI, that is provided as a .roi file.

Requirements:
- IJ-OpenCV update site

 
## TO DO :  
- order of the column in result table 
  
## NB :  
- If show_images is true, the images must have the same dimensions 
 
- The multifile input is not yet macro recordable. An alternative is to use the folder input version 
  
- Method limited to normalised method to have correlation map in range 0-1 : easier to apply a treshold.  
Otherwise normalising relative to maxima of each correlation map is not good since this result in having the global maxima to always be one,  
eventhough its correlation value was not one.    
 '''
### IMPORT ###
import time 	  # for benchmark
from ij import IJ # ImageJ1 import

## Home-Made module 
from Template_Matching.MatchTemplate_Module    import getHit_Template, CornerToCenter 
from Template_Matching.NonMaximaSupression_Py2 import NMS 

if show_images:  
	from ij import ImagePlus, ImageStack 
	Stack_Image     = ImageStack() 
	Stack_Image_ImP = ImagePlus() 
 
if add_roi: 
	from ij.plugin.frame 	import RoiManager 
	from ij.gui 			import Roi 
	RM = RoiManager() 
	rm = RM.getInstance()  
	 
if show_table: 
	from ij.measure import ResultsTable 
	from utils 		import AddToTable 
	Table = ResultsTable().getResultsTable() # allows to append to an existing table 


# Convert method string to the opencv corresponding index 
Dico_Method  = {"Square difference":0,"Normalised Square Difference":1,"Cross-Correlation":2,"Normalised cross-correlation":3,"0-mean cross-correlation":4,"Normalised 0-mean cross-correlation":5} 
Method       =  Dico_Method[method] 

# Initialise time
ListTime = []

# Initialise list of templates (rather than opening them for every image iteration) 
List_Template = [ IJ.openImage( templ_file.getPath() ) for templ_file in template_files ]  



### Search ROI ? ###
# Check if there is a searchRoi
if roi_file:
	from ij.io import RoiDecoder
	searchRoi = RoiDecoder.open(roi_file.getPath())
else:
	searchRoi = None

# Check if it is a rectangular one
if searchRoi and searchRoi.getTypeAsString()=="Rectangle": 
	Bool_SearchRoi = True
else: 
	Bool_SearchRoi = False

# Define Offset for BBox if proper searchRoi
if Bool_SearchRoi:
	dX = searchRoi.getXBase()
	dY = searchRoi.getYBase()
else:
	dX = dY = 0
	
	
	

## Loop over templates for template matching and maxima detection 
tolerance = 0 # deactivate the flood fill of the max detector
for i, im_file in enumerate(image_files): 
	
	if IJ.escapePressed():
		IJ.resetEscape() # for next call
		raise KeyboardInterrupt("Escape was pressed")
		
	# Get the current image 
	PathIm   = im_file.getPath() 
	ImpImage = IJ.openImage(PathIm) 
	ImName = ImpImage.getTitle() 
	ImProc = ImpImage.getProcessor().duplicate() 
	
	# Crop Image if searchRoi
	if Bool_SearchRoi:
		ImpImage.setRoi(searchRoi)
		ImpImage = ImpImage.crop()
	
	## Start Timer here (dont count opening of the image)
	#Start = time.clock()
	
	# Initialise list before looping over templates 
	Hits_BeforeNMS = [] 
	 
	## Loop over template for matching against current image 
	for ImpTemplate in List_Template:
		
		# Check that template is smaller than the searched image
		if Bool_SearchRoi and (ImpTemplate.height>searchRoi.getFloatHeight() or ImpTemplate.width>searchRoi.getFloatWidth()):
			IJ.log("The template "+ ImpTemplate.getTitle() +" is larger in width and/or height than the search region -> skipped")
			continue # go directly to the next for iteration
		
		elif ImpTemplate.width>ImpImage.width or ImpTemplate.height>ImpImage.height:
			IJ.log("The template "+ ImpTemplate.getTitle() + " is larger in width and/or height than the searched image-> skipped")
			continue # go directly to the next for iteration

		# Get hits for the current template (and his flipped and/or rotated versions) 
		List_Hit = getHit_Template(ImpTemplate, ImpImage, flipv, fliph, angles, Method, n_hit, score_threshold, tolerance) # raher use ImagePlus as input to get the name of the template used
		 
		# Store the hits 
		Hits_BeforeNMS.extend(List_Hit) 
	 
	 
	 
	### NMS ###
	#print "\n-- Hits before NMS --\n", 
	#for hit in Hits_BeforeNMS: print hit 
 
	# InterHit NMS if more than one hit 
	if Method in [0,1]:  
		Hits_AfterNMS = NMS(Hits_BeforeNMS, N=n_hit, maxOverlap=max_overlap, sortDescending=False) # only difference is the sorting 
 
	else: 
		Hits_AfterNMS = NMS(Hits_BeforeNMS, N=n_hit, maxOverlap=max_overlap, sortDescending=True) 
 
	#print "\n-- Hits after NMS --\n" 
	#for hit in Hits_AfterNMS : print hit
	
	
	
	## Stop time here (we dont benchmark display time)
	#Stop = time.clock()
	#Elapsed = Stop - Start # in seconds
	#ListTime.append(Elapsed)
	 
	
	
	## Loop over final hits to generate ROI, result table... ###
	for hit in Hits_AfterNMS: 
		
		if Bool_SearchRoi: # Add the offset of the search ROI
			hit['BBox'] = (hit['BBox'][0]+dX, hit['BBox'][1]+dY, hit['BBox'][2], hit['BBox'][3])  
		 
		if add_roi: 
			roi = Roi(*hit['BBox']) 
			roi.setName(hit['TemplateName']) 
			roi.setProperty("Score",  str(hit["Score"]) )
			roi.setPosition(i+1) # set slice position 
			rm.add(None, roi, i+1) # Trick to be able to set slice when less images than ROI. Here i is an digit index before the Roi Name 
			 
		if show_table: 
			Xcorner, Ycorner = hit['BBox'][0], hit['BBox'][1] 
			Xcenter, Ycenter = CornerToCenter(Xcorner, Ycorner, hit['BBox'][2], hit['BBox'][3]) 
			
			Dico = {'Image':ImName, 'Template':hit['TemplateName'] ,'Xcorner':Xcorner, 'Ycorner':Ycorner, 'Xcenter':Xcenter, 'Ycenter':Ycenter, 'Score':hit['Score']} 
			if add_roi:
				Dico['Roi Index'] = rm.getCount()
				AddToTable(Table, Dico, Order=("Image", "Template", "Score", "Roi Index", "Xcorner", "Ycorner", "Xcenter", "Ycenter")) 
			else:				
				AddToTable(Table, Dico, Order=('Image', 'Template', 'Score', 'Xcorner', 'Ycorner', 'Xcenter', 'Ycenter')) 
			
			Table.show("Results")
	 
	 
	
	## Display outputs
	if show_images: 
	
		# Initialise a stack of proper size if not the case before
		if Stack_Image.getSize()==0:
			 Stack_Image = ImageStack(ImProc.width, ImProc.height) # instead of using ImagePlus.getStack otherwise we loose the slice title for the 1st image
		 
		# Add images to Stack
		Stack_Image.addSlice(ImName, ImProc)  
		Stack_Image_ImP.setStack("Result", Stack_Image)

		# Update display
		Stack_Image_ImP.setSlice(i)
		Stack_Image_ImP.show()

		if add_roi:
			# Show All ROI + Associate ROI to slices 
			rm.runCommand("Associate", "true")	
			rm.runCommand("Show All with labels")
	
#for i in ListTime:
	#print i