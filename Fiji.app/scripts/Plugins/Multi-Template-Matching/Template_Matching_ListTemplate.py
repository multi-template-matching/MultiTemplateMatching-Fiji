#@ File[]    (Label="Templates", style="file") template_files  
#@ ImagePlus (label="Image for which to look for the template") image
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
#@ Boolean   (Label="Add ROI to ROI manager") show_roi
#@ Boolean   (Label="Show result table") show_table
'''
previous field : Boolean   (Label="Display correlation map(s)") show_map

Requires ImageJ 1.52i to have the possibility to fill the background while rotating for 16-bit images

FIJI macro  to do template matching
input :
- template_files : list of template path
- image          : ImagePlus for the target image
ie this macro search for one template (with eventual flipped/rotated version)into one target image.
The target image should be already open in Fiji.

First of all, additionnal versions of the template are generated (flip+rotation)
For the resulting list of templates the search is carried out and results in a list of correlation maps

Minima/maxima in the correlation map are detected, followed by Non-Maxima Supression in case of multiple correlation map/templates


TO DO : 
- order of the column in result table
- use steerable tempalte matching see steerable detector BIG Lausanne

NB : 
- The multifile input is not yet macro recordable. An alternative is to use a folder input and to process the content of the folder (but not as flexible)

- (currently no search ROi so not applicable) Delete the previous ROI for every new Run otherwise 1st ROI is used to limit the search

- Method limited to normalised method to have correlation map in range 0-1 : easier to apply a treshold. 
Otherwise normalising relative to maxima of each correlation map is not good since this result in having the global maxima to always be one, 
eventhough its correlation value was not one.
Another possibility would be to have an absolute threshold (realtive to the correlation score) and a relative threshold (relative to the maxima of this particular map)  

The multifile input is not yet macro recordable. An alternative is to use a folder input and to process the content of the folder (but not as flexible)
'''
## Initialise variables before import (otherwise the ROI is lost)
ImageName = image.getTitle()
searchRoi = image.getRoi()

## Rectangle ROI ?
if searchRoi and searchRoi.getTypeAsString()=="Rectangle": 
	Bool_SearchRoi = True
else:
	Bool_SearchRoi = False

# Define offset
if Bool_SearchRoi:
	image = image.crop()
	dX = int(searchRoi.getXBase())
	dY = int(searchRoi.getYBase())
else:
	dX = dY = 0

	
### IMPORT MODULES (after retrieving ROI) ###
from ij import IJ 

# Home-Made module
from Template_Matching.MatchTemplate_module    import getHit_Template, CornerToCenter
from Template_Matching.NonMaximaSupression_Py2 import NMS


# Convert method string to the index
Dico_Method  = {"Square difference":0,"Normalised Square Difference":1,"Cross-Correlation":2,"Normalised cross-correlation":3,"0-mean cross-correlation":4,"Normalised 0-mean cross-correlation":5}
Method       =  Dico_Method[method]


# Initialise list of hit before looping
Hits_BeforeNMS = [] 

## Loop over templates for template matching and maxima detection
for temp_file in template_files:
	
	# Get ImageProcessor for the current template
	PathTemp = temp_file.getPath()
	ImpTemplate = IJ.openImage(PathTemp)
	
	# Check that template is smaller than the searched image
	if ImpTemplate.width>image.width or ImpTemplate.height>image.height:
		raise Exception('The current template is larger in width and/or height than the searched image')
	
	# Get hits for the current template (and his flipped and/or rotated versions)
	List_Hit = getHit_Template(ImpTemplate, image, flipv, fliph, angles, Method, n_hit, score_threshold, tolerance)
	
	# Store the hits
	Hits_BeforeNMS.extend(List_Hit)
	


### NMS inter template ###
print "\n-- Hits before NMS --\n"
for hit in Hits_BeforeNMS: print hit

# NMS if more than one hit
if Method in [0,1]: 
	Hits_AfterNMS = NMS(Hits_BeforeNMS, N=n_hit, maxOverlap=max_overlap, sortDescending=False) # only difference is the sorting

else:
	Hits_AfterNMS = NMS(Hits_BeforeNMS, N=n_hit, maxOverlap=max_overlap, sortDescending=True)

print "\n-- Hits after NMS --\n"
for hit in Hits_AfterNMS: print hit




### Outputs ###
if show_table:
	from ij.measure import ResultsTable
	from utils 		import AddToTable
	
	Table = ResultsTable().getResultsTable() # allows to append to an existing table

if show_roi:
	from ij.plugin.frame 	import RoiManager
	from ij.gui 			import Roi
	
	# Initialise RoiManager
	RM = RoiManager()
	rm = RM.getInstance()
	
	# Show All ROI + Associate ROI to slices 
	rm.runCommand("Associate", "true")	
	rm.runCommand("Show All with labels")
	

# Loop over final hits to generate ROI, result table...
for hit in Hits_AfterNMS:
	
	if Bool_SearchRoi: # Add offset of searchRoi
		hit['BBox'] = (hit['BBox'][0]+dX, hit['BBox'][1]+dY, hit['BBox'][2], hit['BBox'][3])  

	if show_roi:
		roi = Roi(*hit['BBox'])
		roi.setName(hit['TemplateName'])
		rm.addRoi(roi)
	
	if show_table:
		Xcorner, Ycorner = hit['BBox'][0], hit['BBox'][1]
		Xcenter, Ycenter = CornerToCenter(Xcorner, Ycorner, hit['BBox'][2], hit['BBox'][3])
		Dico = {"Image":ImageName, 'Template':hit['TemplateName'] ,'Xcorner':Xcorner, 'Ycorner':Ycorner, 'Xcenter':Xcenter, 'Ycenter':Ycenter, 'Score':hit['Score']}
		AddToTable(Table, Dico, Order=("Image", "Template", "Score", "Xcorner", "Ycorner", "Xcenter", "Ycenter"))
		

## Finally update display
if show_roi: IJ.selectWindow(ImageName)
if show_table: Table.show("Results")
