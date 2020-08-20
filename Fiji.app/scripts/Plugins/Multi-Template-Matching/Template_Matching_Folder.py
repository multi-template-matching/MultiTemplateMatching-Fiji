'''
Object recognition using one or multiple template images 
this plugin searches for some templates (with eventual flipped/rotated versions) into some target image(s). 

input : 
- template : Path to template image or folder of template images 
- image    : Path to image or folder of images in which to look for the template

First, additionnal versions of the template are generated (flip+rotation) if selected
Then each template is searched in the target image. This yield as set of correlation maps 
 
Minima/maxima in the correlation maps are detected, followed by Non-Maxima Supression when several object are explected in the target image
- matchTemplate Method limited to normalised method to have correlation map in range 0-1 : easier to apply a treshold.  

The search region can be limited to a rectangular ROI, that is provided as a .roi file

Requirements:
- IJ-OpenCV update site
'''

## Import modules
#@PrefService prefs
#@FormatService fs # to check that the file in the folder are indeed images
from fiji.util.gui import GenericDialogPlus
from ij            import IJ
from ij.gui 	   import Roi
from os			   import listdir
from os.path 	   import join, isfile, isdir
#import time

## Home-Made module 
from Template_Matching.MatchTemplate_Module    import getHit_Template, CornerToCenter 
from Template_Matching.NonMaximaSupression_Py2 import NMS 

## Create GUI
Win = GenericDialogPlus("Multiple Template Matching")
Win.addDirectoryOrFileField("Template file or templates folder", prefs.get("TemplatePath", "template(s)"))
Win.addDirectoryOrFileField("Image file or images folder", prefs.get("ImagePath", "image(s)"))
Win.addFileField("Rectangular_search_ROI (optional)",  prefs.get("RoiPath","searchRoi"))

# Template pre-processing
Win.addCheckbox("Flip_template_vertically", prefs.getInt("FlipV", False))
Win.addCheckbox("Flip_template_horizontally", prefs.getInt("FlipH", False))
Win.addStringField("Rotate template by ..(comma-separated)", prefs.get("Angles", ""))

# Template matchign parameters
Win.addChoice("Matching_method", ["Normalised Square Difference","Normalised cross-correlation","Normalised 0-mean cross-correlation"], prefs.get("Method","Normalised 0-mean cross-correlation"))
Win.addNumericField("Number_of_objects expected", prefs.getInt("N_hit",1),0)
Win.addMessage("If more than 1 object expected :")
Win.addSlider("Score_Threshold", 0, 1, prefs.getFloat("Score_Threshold",0.5), 0.1) 
#Win.addNumericField("Min_peak_height relative to neighborhood ([0-1], decrease to get more hits)", prefs.getFloat("Tolerance",0.1), 2)
Win.addSlider("Maximal_overlap between Bounding boxes", 0, 1, prefs.getFloat("MaxOverlap",0.4), 0.1) 

# Outputs
Win.addMessage("Outputs")
Win.addCheckbox("Open_images as a stack (must have identical sizes)", prefs.getInt("ShowImages", True))
Win.addCheckbox("Add_ROI detected  to ROI Manager", prefs.getInt("AddRoi", True))
Win.addCheckbox("Show_result table", prefs.getInt("ShowTable", False))
Win.addMessage("""If you use this plugin please cite :
Thomas, L.S.V., Gehrig, J. 
Multi-template matching: a versatile tool for object-localization in microscopy images. 
BMC Bioinformatics 21, 44 (2020). https://doi.org/10.1186/s12859-020-3363-7""")
Win.addHelp("https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/wiki")

Win.showDialog()

if Win.wasOKed():
	TemplatePath = Win.getNextString()
	ImagePath    = Win.getNextString()
	RoiPath      = Win.getNextString()
	flipv  = Win.getNextBoolean()
	fliph  = Win.getNextBoolean()
	angles = Win.getNextString()
	method = Win.getNextChoice()
	n_hit  = int(Win.getNextNumber())
	score_threshold = Win.getNextNumber()
	#tolerance   = Win.getNextNumber()
	tolerance = 0
	max_overlap = Win.getNextNumber()
	show_images = Win.getNextBoolean()
	add_roi     = Win.getNextBoolean()
	show_table  = Win.getNextBoolean()
	
	# Save for persistence
	prefs.put("TemplatePath", TemplatePath)
	prefs.put("ImagePath", ImagePath)
	prefs.put("RoiPath", RoiPath)
	prefs.put("FlipV",flipv)
	prefs.put("FlipH",fliph)
	prefs.put("Angles", angles)
	prefs.put("Method", method)
	prefs.put("N_hit", n_hit)
	prefs.put("Score_Threshold", score_threshold)
	#prefs.put("Tolerance", tolerance)
	prefs.put("MaxOverlap", max_overlap)
	prefs.put("ShowImages", show_images)	
	prefs.put("AddRoi", add_roi)
	prefs.put("ShowTable", show_table)
	
	# Convert method string to the opencv corresponding index 
	Dico_Method  = {"Square difference":0,"Normalised Square Difference":1,"Cross-Correlation":2,"Normalised cross-correlation":3,"0-mean cross-correlation":4,"Normalised 0-mean cross-correlation":5} 
	Method       =  Dico_Method[method] 
	
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
	
	
	## Check if input are valid
	if n_hit<=0:
		raise Exception('The expected number of object should be at least 1')
	
	if score_threshold<0 or score_threshold>1:
		raise Exception('The score threshold should be in range [0,1]')
		
	#if tolerance<0 or tolerance>1:
	#	raise Exception('Tolerance should be in range [0,1]')
	
	if max_overlap<0 or max_overlap>1:
		raise Exception('The max overlap should be in range [0,1]')
	
	
	### Search ROI ? ###
	# Check if there is a searchRoi
	if RoiPath:
		from ij.io import RoiDecoder
		searchRoi = RoiDecoder.open(RoiPath)
	else:
		searchRoi = None

	# Check if it is a rectangular one
	if searchRoi and searchRoi.getTypeAsString()=="Rectangle": 
		Bool_SearchRoi = True
		dX = int(searchRoi.getXBase())
		dY = int(searchRoi.getYBase())
	
	else: 
		Bool_SearchRoi = False
		dX = dY = 0
		
	
	
	## File or Folder
	# Template(s)
	if isfile(TemplatePath): # single template file
		ListPathTemplate = [TemplatePath]
	
	elif isdir(TemplatePath): # template folder
		ListPathTemplate = []
		
		for name in listdir(TemplatePath):
			
			FullPathTem = join(TemplatePath,name) 
			
			if isfile(FullPathTem):
				try:
					fs.getFormat(FullPathTem) # check that it is an image file
					ListPathTemplate.append(FullPathTem)
				except:
					pass
	else:
		raise Exception("Template path does not exist")
	
	# Initialise list of templates (rather than opening them for every image iteration) 
	List_Template = [ IJ.openImage(PathTemp) for PathTemp in ListPathTemplate ]  
	
	
	
	
	# Image(s)
	if isfile(ImagePath): # single image path
		ListPathImage = [ImagePath]
	
	elif isdir(ImagePath): # image folder
		ListPathImage = [] # initialise
		
		for name in listdir(ImagePath):
			
			FullPathIm = join(ImagePath,name) 
			
			if isfile(FullPathIm):
				try:
					fs.getFormat(FullPathIm) # check that it is an image file
					ListPathImage.append(FullPathIm)
				except:
					pass
	
	else: # neither a file path nor a folder path (ie non existing)
		raise Exception("Image path does not exist")
	
	## Initialise Result table for time
	#TimeTable = ResultsTable()
	
	## Loop over images for template matching and maxima detection 
	for i, PathIm in enumerate(ListPathImage): 
		
		if IJ.escapePressed():
			IJ.resetEscape() # for next call
			raise KeyboardInterrupt("Escape was pressed")
			
		# Get the current image 
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
			
			# Check that template is smaller than the searched image or ROI
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
		
	


		## Loop over final hits to generate ROI ##
		for hit in Hits_AfterNMS:
			
			#print hit
			
			if Bool_SearchRoi: # Add offset of search ROI
				hit['BBox'] = (hit['BBox'][0]+dX, hit['BBox'][1]+dY, hit['BBox'][2], hit['BBox'][3])  
			
			# Create detected ROI
			roi = Roi(*hit['BBox'])
			roi.setName(hit['TemplateName'])
			roi.setPosition(i+1) # set ROI Z-position
			
			if add_roi:
				rm.add(None, roi, i+1) # Trick to be able to set Z-position when less images than the number of ROI. Here i is an digit index before the Roi Name 
			
			if show_table:
				Xcorner, Ycorner = hit['BBox'][0], hit['BBox'][1]
				Xcenter, Ycenter = CornerToCenter(Xcorner, Ycorner, hit['BBox'][2], hit['BBox'][3])
				
				Dico = {'Image':ImName, 'Template':hit['TemplateName'] ,'Xcorner':Xcorner, 'Ycorner':Ycorner, 'Xcenter':Xcenter, 'Ycenter':Ycenter, 'Score':hit['Score']} 
				if add_roi:
					Dico['Roi Index'] = rm.getCount()
					AddToTable(Table, Dico, Order=("Image", "Template", "Score", "Roi Index", "Xcorner", "Ycorner", "Xcenter", "Ycenter")) 
				else:				
					AddToTable(Table, Dico, Order=('Image', 'Template', 'Score', 'Xcorner', 'Ycorner', 'Xcenter', 'Ycenter')) 

		
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

			if add_roi: # Show All ROI + Associate ROI to slices 
				rm.runCommand("Associate", "true")	
				rm.runCommand("Show All with labels")
	
	
		## Stop time here
		#Stop = time.clock()
		#Elapsed = Stop - Start # in seconds
		#TimeTable.incrementCounter()
		#TimeTable.addValue('Time(s)', Elapsed)
	
	
	# At the end, display result table
	if show_table:
		Table.show("Results")
	
	#TimeTable.show("BenchmarkTime")