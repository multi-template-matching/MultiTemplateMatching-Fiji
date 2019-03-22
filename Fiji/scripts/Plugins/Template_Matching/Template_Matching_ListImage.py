#@ File[]    (Label="Templates", style="file") template_files   
#@ File[]    (label="Image for which to look for the template") image_files
#@ File 	 (label="Region of Interest (ROI) for search (optional)", required=false) roi_file
#@ Boolean   (Label="Flip template vertically") flipv 
#@ Boolean   (Label="Flip template horizontally") fliph 
#@ String    (Label="Additional rotation angles separated by ," ,required=False) angles 
#@ String    (Label="Matching method",choices={"Normalised Square Difference", "Normalised cross-correlation", "Normalised 0-mean cross-correlation"}, value="Normalised 0-mean cross-correlation") method 
#@ int       (Label="Expected number of templates", min=1) n_hit 
#@ String    (visibility="MESSAGE", value="The parameters below are used only if more than 1 template are expected in the image") doc 
#@ Float     (Label="Score Threshold (0-1)", min=0, max=1, value=0.5, stepSize=0.1) score_threshold 
#@ Float     (Label="Min peak height relative to neighborhood (0-1, decrease to get more hits)", min=0, max=1, value=0.1, stepSize=0.1) tolerance 
#@ Float     (Label="Maximal overlap between Bounding boxes (0-1)",min=0, max=1, value=0.4, stepSize=0.1) max_overlap 
#@ String    (visibility="MESSAGE", value="Output") out 
#@ Boolean   (Label="Open images (as stack ie images must have identical dimensions)") show_images 
#@ Boolean   (Label="Add ROI to ROI Manager") show_roi 
#@ Boolean   (Label="Show result table") show_table 
'''
previous field : Boolean   (Label="Display correlation map(s)") show_map 
 
Requires ImageJ 1.52i to have the possibility to fill the background while rotating for 16-bit images 
 
FIJI macro  to do template matching 
input : 
- template_files : list of template path 
- image_files    : list of image path for which we want to search a template 
ie this macro search for N templates (with eventual flipped/rotated version) into L target images. 
 
 
First of all, additionnal versions of the template are generated (flip+rotation) 
For the resulting list of templates the search is carried out and results in a list of correlation maps 
 
Minima/maxima in the correlation map are detected, followed by Non-Maxima Supression in case of multiple correlation map/templates 
 
 
## TO DO :  
- order of the column in result table 
 
- use steerable tempalte matching see steerable detector BIG Lausanne 
 
 
## NB :  
- If open_images is true, the images must have the same dimensions 
 
- The multifile input is not yet macro recordable. An alternative is to use a folder input and to process the content of the folder (but not as flexible) 
 
- (currently no search ROi so not applicable) Delete the previous ROI for every new Run otherwise 1st ROI is used to limit the search 
 
- Method limited to normalised method to have correlation map in range 0-1 : easier to apply a treshold.  
Otherwise normalising relative to maxima of each correlation map is not good since this result in having the global maxima to always be one,  
eventhough its correlation value was not one. 
Another possibility would be to have an absolute threshold (realtive to the correlation score) and a relative threshold (relative to the maxima of this particular map)   
 
The multifile input is not yet macro recordable. An alternative is to use a folder input and to process the content of the folder (but not as flexible) 
'''
### IMPORT ###
import time 	  # for becnhmark
from ij import IJ # ImageJ1 import

## Home-Made module 
from Template_Matching.MatchTemplate_module    import getHit_Template, CornerToCenter 
from Template_Matching.NonMaximaSupression_Py2 import NMS 

if show_images:  
	from ij import ImagePlus, ImageStack 
	Stack_Image     = ImageStack() 
	Stack_Image_ImP = ImagePlus() 
 
if show_roi: 
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
	
	
	

#nROI = 0 
## Loop over templates for template matching and maxima detection 
for i, im_file in enumerate(image_files): 
		
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
	Start = time.clock()
	
	# Initialise list before looping over templates 
	Hits_BeforeNMS = [] 
	 
	## Loop over template for matching against current image 
	for ImpTemplate in List_Template:
		
		# Check that template is smaller than the searched image
		if ImpTemplate.width>ImpImage.width or ImpTemplate.height>ImpImage.height:
			raise Exception('The current template is larger in width and/or height than the searched image')

		# Get hits for the current template (and his flipped and/or rotated versions) 
		List_Hit = getHit_Template(ImpTemplate, ImpImage, flipv, fliph, angles, Method, n_hit, score_threshold, tolerance) # raher use ImagePlus as input to get the name of the template used
		 
		# Store the hits 
		Hits_BeforeNMS.extend(List_Hit) 
	 
	 
	 
	### NMS ###
	print "\n-- Hits before NMS --\n", 
	for hit in Hits_BeforeNMS: print hit 
 
	# InterHit NMS if more than one hit 
	if Method in [0,1]:  
		Hits_AfterNMS = NMS(Hits_BeforeNMS, N=n_hit, maxOverlap=max_overlap, sortDescending=False) # only difference is the sorting 
 
	else: 
		Hits_AfterNMS = NMS(Hits_BeforeNMS, N=n_hit, maxOverlap=max_overlap, sortDescending=True) 
 
	print "\n-- Hits after NMS --\n" 
	for hit in Hits_AfterNMS : print hit
	
	
	
	## Stop time here (we dont benchmark display time)
	Stop = time.clock()
	Elapsed = Stop - Start # in seconds
	ListTime.append(Elapsed)
	 
	
	
	## Loop over final hits to generate ROI, result table... ###
	for hit in Hits_AfterNMS: 
		
		if Bool_SearchRoi: # Add the offset of the search ROI
			hit['BBox'] = (hit['BBox'][0]+dX, hit['BBox'][1]+dY, hit['BBox'][2], hit['BBox'][3])  
		 
		if show_roi: 
			roi = Roi(*hit['BBox']) 
			roi.setName(hit['TemplateName']) 
			roi.setPosition(i+1) # set slice position 
			#nROI+=1 
			rm.add(None, roi, i+1) # Trick to be able to set slice when less images than ROI. Here i is an digit index before the Roi Name 
			 
		if show_table: 
			Xcorner, Ycorner = hit['BBox'][0], hit['BBox'][1] 
			Xcenter, Ycenter = CornerToCenter(Xcorner, Ycorner, hit['BBox'][2], hit['BBox'][3]) 
			Dico = {'Image':ImName, 'Template':hit['TemplateName'] ,'Xcorner':Xcorner, 'Ycorner':Ycorner, 'Xcenter':Xcenter, 'Ycenter':Ycenter, 'Score':hit['Score']} 
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

		if show_roi:
			# Show All ROI + Associate ROI to slices 
			rm.runCommand("Associate", "true")	
			rm.runCommand("Show All with labels")
	
for i in ListTime:
	print i
