'''
Object recognition using one or multiple template images 
this plugin search for one template (with eventual flipped/rotated version) into one target image. 
The 2 images should be already opened in Fiji. 

input : 
- template : ImagePlus of the object to search in the target image  
- image    : ImagePlus or Stack 

First, additionnal versions of the template are generated (flip+rotation) if selected
Then each template is searched in the target image. This yield as set of correlation maps 
 
Minima/maxima in the correlation maps are detected, followed by Non-Maxima Supression when several object are explected in the target image
- matchTemplate Method limited to normalised method to have correlation map in range 0-1 : easier to apply a treshold.  

The search region can be limited to a rectangular ROI, that is drawn on the image/stack before execution of the plugin.

Requirements:
- IJ-OpenCV update site
'''
#import time
#@PrefService prefs 
from fiji.util.gui import GenericDialogPlus
# rest of imports below on purpose (otherwise searchRoi lost)

## Create GUI 
Win = GenericDialogPlus("Multiple Template Matching") 
Win.addImageChoice("Template", prefs.get("Template","Choice")) 
Win.addImageChoice("Image", prefs.get("Image", "Choice")) 
Win.addCheckbox("Flip_template_vertically", prefs.getInt("FlipV", False)) 
Win.addCheckbox("Flip_template_horizontally", prefs.getInt("FlipH", False)) 
Win.addStringField("Rotate template by ..(comma-separated)", prefs.get("Angles", "")) 
Win.addChoice("Matching_method", ["Normalised Square Difference","Normalised cross-correlation","Normalised 0-mean cross-correlation"], prefs.get("Method","Normalised 0-mean cross-correlation")) 
Win.addNumericField("Number_of_objects expected", prefs.getInt("N_hit",1),0) 
Win.addMessage("If more than 1 object expected :") 
Win.addSlider("Score_Threshold", 0, 1, prefs.getFloat("Score_Threshold",0.5), 0.1) 
#Win.addNumericField("Min_peak_height relative to neighborhood ([0-1], decrease to get more hits)", prefs.getFloat("Tolerance",0.1), 2) 
Win.addSlider("Maximal_overlap between Bounding boxes", 0, 1, prefs.getFloat("MaxOverlap",0.4), 0.1) 
Win.addMessage("Outputs") 
Win.addCheckbox("Add_ROI detected to ROI manager", prefs.getInt("AddRoi", True)) 
Win.addCheckbox("Show_result table", prefs.getInt("ShowTable", False)) 
Win.addMessage("""If you use this plugin please cite :
Thomas, L.S.V., Gehrig, J. 
Multi-template matching: a versatile tool for object-localization in microscopy images. 
BMC Bioinformatics 21, 44 (2020). https://doi.org/10.1186/s12859-020-3363-7""") 
Win.addHelp("https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/wiki") 
 
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
	from ij            import IJ, ImagePlus
	from ij.gui 	   import Roi 
 
	## Import  HomeMade modules 
	from Template_Matching.NonMaximaSupression_Py2 import NMS 
	from Template_Matching.MatchTemplate_Module    import getHit_Template, CornerToCenter  
 
 
	## Check that the template is smaller than the (possibly cropped) image 
	if Bool_SearchRoi and (template.height>searchRoi.getFloatHeight() or template.width>searchRoi.getFloatWidth()): 
		raise Exception('The template is larger in width and/or height than the searched Roi') 
	 
	elif template.height>image.height or template.width>image.width: 
		raise Exception('The template is larger in width and/or height than the searched image') 
 
	### Initialize outputs ### 
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
	imageStack = image.getStack() 
	nSlice     = image.getStackSize() 
	
	for i in xrange(1,nSlice+1): 
		
		if IJ.escapePressed():
			IJ.resetEscape() # for next call
			raise KeyboardInterrupt("Escape was pressed")
		 
		searchedImage = imageStack.getProcessor(i) # of slice i
		 
		if Bool_SearchRoi:
			searchedImage.setRoi(searchRoi)
			searchedImage = searchedImage.crop()
		
		
		# Fix the name for searchImage 
		if nSlice>1: 
			SliceLabel = imageStack.getSliceLabel(i)
			
			if SliceLabel: # sometimes the slicelabel is none
				Title = SliceLabel.split('\n',1)[0] # split otherwise we get some unecessary information 
			else:
				Title = image.getTitle()
		
		else: 
			Title = image.getTitle()
		
		# Do the template(s) matching
		#Start = time.clock()
		Hits_BeforeNMS = getHit_Template(template, 
										ImagePlus(Title, searchedImage), 
										flipv, fliph, 
										angles, 
										Method, 
										n_hit, 
										score_threshold, 
										tolerance) # template and image as ImagePlus (to get the name together with the image matrix) 
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
			#roi.setProperty("class", hit["TemplateName"])
			
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