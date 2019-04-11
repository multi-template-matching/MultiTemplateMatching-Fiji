'''
previous parameter removed : 
Boolean (Label="Display correlation map(s)") show_map # Complicated, showing several correlation map with each variation of the template 
At the gaps above, removed because it was displayed when macro recorded 
String  (visibility="MESSAGE", value="The parameters below are used only if more than 1 template are expected in the image") doc 
String  (visibility="MESSAGE", value="Output") out 
 
Requires ImageJ 1.52i to have the possibilityy to fill the background while rotating for 16-bit images 
 
FIJI macro  to do template matching 
input : 
- template : ImagePlus for the template 
- image    : ImagePlus for the target image 
ie this macro search for one template (with eventual flipped/rotated version)into one target image. 
The 2 images should be already open in Fiji. 
 
First of all, additionnal versions of the template are generated (flip+rotation) 
For the resulting list of templates the search is carried out and results in a list of correlation maps 
 
Minima/maxima in the correlation map are detected, followed by Non-Maxima Supression in case of multiple correlation map/templates 
 
The multifile input is not yet macro recordable. An alternative is to use a folder input and to process the content of the folder (but not as flexible) 
 
TO DO :  
- use steerable tempalte matching see steerable detector BIG Lausanne 
 
 
- Method limited to normalised method to have correlation map in range 0-1 : easier to apply a treshold.  
Otherwise normalising relative to maxima of each correlation map is not good since this result in having the global maxima to always be one,  
eventhough its correlation value was not one. 
Another possibility would be to have an absolute threshold (relative to the correlation score) and a relative threshold (relative to the maxima of this particular map)   
'''
#import time
#@PrefService prefs 
from fiji.util.gui import GenericDialogPlus 
 
## Create GUI 
Win = GenericDialogPlus("Multiple Template Matching") 
Win.addImageChoice("Template", prefs.get("Template","Choice")) 
Win.addImageChoice("Image", prefs.get("Image", "Choice")) 
Win.addCheckbox("Flip_template_vertically", prefs.getInt("FlipV", False)) 
Win.addCheckbox("Flip_template_horizontally", prefs.getInt("FlipH", False)) 
Win.addStringField("Rotate template by (,-separated)", prefs.get("Angles", "")) 
Win.addChoice("Matching_method", ["Normalised Square Difference","Normalised cross-correlation","Normalised 0-mean cross-correlation"], prefs.get("Method","Normalised 0-mean cross-correlation")) 
Win.addNumericField("Number_of_templates expected", prefs.getInt("N_hit",1),0) 
Win.addMessage("If more than 1 template expected :") 
Win.addNumericField("Score_Threshold [0-1]", prefs.getFloat("Score_Threshold",0.5), 2) 
#Win.addNumericField("Min_peak_height relative to neighborhood ([0-1], decrease to get more hits)", prefs.getFloat("Tolerance",0.1), 2) 
Win.addNumericField("Maximal_overlap between Bounding boxes [0-1]", prefs.getFloat("MaxOverlap",0.4), 2) 
Win.addMessage("Outputs") 
Win.addCheckbox("Add_ROI detected to ROI manager", prefs.getInt("AddRoi", True)) 
Win.addCheckbox("Show_result table", prefs.getInt("ShowTable", False)) 
Win.addMessage("If you use this plugin please cite : xxx") 
Win.addHelp("https://github.com/acquifer/RoiDetection/wiki") 
 
Win.showDialog() 
 
if Win.wasOKed(): 
	template = Win.getNextImage()  
	image    = Win.getNextImage() 
	flipv  = Win.getNextBoolean() 
	fliph  = Win.getNextBoolean() 
	angles = Win.getNextString() 
	method = Win.getNextChoice() 
	n_hit  = int(Win.getNextNumber()) 
	score_threshold = Win.getNextNumber() 
	#tolerance   = Win.getNextNumber()
	tolerance = 0
	max_overlap = Win.getNextNumber() 
	add_roi     = Win.getNextBoolean() 
	show_table  = Win.getNextBoolean() 
	 
	# Save for persistence 
	ImageName = image.getTitle() 
	prefs.put("Template", template.getTitle()) 
	prefs.put("Image", ImageName) 
	prefs.put("FlipV",flipv) 
	prefs.put("FlipH",fliph) 
	prefs.put("Angles", angles) 
	prefs.put("Method", method) 
	prefs.put("N_hit", n_hit) 
	prefs.put("Score_Threshold", score_threshold) 
	#prefs.put("Tolerance", tolerance) 
	prefs.put("MaxOverlap", max_overlap) 
	prefs.put("AddRoi", add_roi) 
	prefs.put("ShowTable", show_table) 
	 
	# Check if input are valid 
	if n_hit<=0: 
		raise Exception('The expected number of object should be at least 1') 
	 
	if score_threshold<0 or score_threshold>1: 
		raise Exception('The score threshold should be in range [0,1]') 
		 
	#if tolerance<0 or tolerance>1: 
	#	raise Exception('Tolerance should be in range [0,1]') 
	 
	if max_overlap<0 or max_overlap>1: 
		raise Exception('The max overlap should be in range [0,1]') 
	 
	 
	## Initialise variables before import (otherwise the ROI is lost) 
	searchRoi = image.getRoi() 
 
	## Rectangle ROI ? 
	if searchRoi and searchRoi.getTypeAsString()=="Rectangle":  
		Bool_SearchRoi = True 
	else: 
		Bool_SearchRoi = False 
	 
	# Define offset 
	if Bool_SearchRoi: 
		dX = int(searchRoi.getXBase()) 
		dY = int(searchRoi.getYBase()) 
	else: 
		dX = dY = 0 
 
 
	## Import modules 
	from ij            import IJ 
	from ij.gui 	   import Roi 
 
	## Import  HomeMade modules 
	from Template_Matching.NonMaximaSupression_Py2 import NMS 
	from Template_Matching.MatchTemplate_Module    import getHit_Template, CornerToCenter  
 
 
	## Check that the template is smaller than the (possibly cropped) image 
	if Bool_SearchRoi and (template.height>searchRoi.getFloatHeight() or template.width>searchRoi.getFloatWidth()): 
		raise Exception('The template is larger in width and/or height than the searched Roi') 
	 
	elif template.height>image.height or template.width>image.width: 
		raise Exception('The template is larger in width and/or height than the searched image') 
 
	### Initialise outputs ### 
	if show_table: 
		from ij.measure import ResultsTable 
		from utils 		import AddToTable 
		Table = ResultsTable().getResultsTable() # allows to append to an existing table 
		 
	if add_roi: 
		from ij.plugin.frame 	import RoiManager 
		RM = RoiManager() 
		rm = RM.getInstance() 
 
 
	# Convert method string to the opencv corresponding index 
	Dico_Method  = {"Square difference":0,"Normalised Square Difference":1,"Cross-Correlation":2,"Normalised cross-correlation":3,"0-mean cross-correlation":4,"Normalised 0-mean cross-correlation":5} 
	Method       =  Dico_Method[method] 
 
	 
	# Loop over the images in the stack (or directly process if unique) 
	ImageStack = image.getStack() 
	nSlice     = image.getStackSize() 
	imageBis   = image.duplicate() # duplicate full stack to be sure to not mess around with ROI display
	
	for i in xrange(1,nSlice+1): 
		 
		imageBis.setSlice(i) # for stacks (important for both with/without searchRoi) for single image no adversial effect 
		 
		if Bool_SearchRoi: 
			imageBis.setRoi(searchRoi) 
			searchedImage = imageBis.crop() # Single image -> crop to ROI - Stack -> crop the slice to the ROI (in this case) 
			 
		elif nSlice>1: # no SearchRoi, but with Stack still crop to isolate the slice 
			 
			# Remove any ROI and crop 
			imageBis.killRoi() 
			searchedImage = imageBis.crop() 
 
		else: # no ROI and not a stack 
			searchedImage = imageBis 
			 
					 
		# Fix the name for imageBis 
		if nSlice>1: 
			SliceLabel = image.getStack().getSliceLabel(i)
			
			if SliceLabel: # sometimes the slicelabel is none
				Title = SliceLabel.split('\n',1)[0] # split otherwise we get some unecessary information 
			else:
				Title = image.getTitle()
		
		else: 
			Title = image.getTitle() 
		 
		searchedImage.setTitle(Title) 
		 
			 
		# Do the template(s) matching
		#Start = time.clock()
		Hits_BeforeNMS = getHit_Template(template, searchedImage, flipv, fliph, angles, Method, n_hit, score_threshold, tolerance) # template and image as ImagePlus (to get the name together with the image matrix) 
		#Stop = time.clock()
		#IJ.log("getHit_Template took " + str(Stop-Start) + " seconds")
		
		### NMS ### 
		#IJ.log(str(len(Hits_BeforeNMS)) + " hit before NMS") 
		
		#print "\n-- Hits before NMS --\n",  
		#for hit in Hits_BeforeNMS : print hit 
 
		# NMS if more than one hit before NMS. For n_hit=1 the NMS does not actually compute the IoU it will just take the best score 
		#start_NMS = time.clock()
		if len(Hits_BeforeNMS)==1: 
			Hits_AfterNMS = Hits_BeforeNMS 
 
		elif Method in [0,1]:  
			Hits_AfterNMS = NMS(Hits_BeforeNMS, N=n_hit, maxOverlap=max_overlap, sortDescending=False) # only difference is the sorting 
 
		else: 
			Hits_AfterNMS = NMS(Hits_BeforeNMS, N=n_hit, maxOverlap=max_overlap, sortDescending=True) 

 		#stop_NMS = time.clock()
 		#IJ.log("NMS duration(s): " + str(stop_NMS-start_NMS))
		#print "\n-- Hits after NMS --\n" 
		#for hit in Hits_AfterNMS : print hit 
 
		# NB : Hits coordinates have not been corrected for cropping here ! Done in the next for loop 
 
 
		# Loop over final hits to generate ROI 
		for hit in Hits_AfterNMS: 
			 
			#print hit	
			
			if Bool_SearchRoi: # Add offset of search ROI 
				hit['BBox'] = (hit['BBox'][0]+dX, hit['BBox'][1]+dY, hit['BBox'][2], hit['BBox'][3])   
			 
			# Create detected ROI 
			roi = Roi(*hit['BBox']) 
			roi.setName(hit['TemplateName']) 
			roi.setPosition(i) # set ROI Z-position 
			image.setSlice(i) 
			image.setRoi(roi) 
			 
			if add_roi: 
				rm.add(None, roi, i) # Trick to be able to set Z-position when less images than the number of ROI. Here i is an digit index before the Roi Name  
				 
				# Show All ROI + Associate ROI to slices  
				rm.runCommand("Associate", "true")	 
				rm.runCommand("Show All with labels") 
				IJ.selectWindow(ImageName) # does not work always 
			 
			if show_table: 
				Xcorner, Ycorner = hit['BBox'][0], hit['BBox'][1] 
				Xcenter, Ycenter = CornerToCenter(Xcorner, Ycorner, hit['BBox'][2], hit['BBox'][3]) 
				
				Dico = {'Image':hit['ImageName'],'Slice':i, 'Template':hit['TemplateName'] ,'Xcorner':Xcorner, 'Ycorner':Ycorner, 'Xcenter':Xcenter, 'Ycenter':Ycenter, 'Score':hit['Score']} # column order is defined below
				
				if add_roi: 
					# Add ROI index to the result table
					Dico['Roi Index'] = rm.getCount()
					AddToTable(Table, Dico, Order=("Image", "Slice", "Template", "Score", "Roi Index", "Xcorner", "Ycorner", "Xcenter", "Ycenter")) 
				else:	
					AddToTable(Table, Dico, Order=("Image", "Slice", "Template", "Score", "Xcorner", "Ycorner", "Xcenter", "Ycenter")) 
 
 
			 
	# Display result table 
	if show_table: 
		Table.show("Results")