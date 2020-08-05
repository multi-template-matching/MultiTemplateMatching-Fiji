'''
Perform rotation of an image expanding the canvas and filling the background with the modal value of the initial value
without calling IJ.run
For that we create an empty canvas of the size of the final matrix (or larger : dimension of the initial image), paste the centered image and rotate it
This is due to the fact that the canvas must be big enough to contain the all the rotated state of the image
'''
from ij.gui 		import Roi
from ij.plugin 		import RoiRotator
from fiji.selection import Select_Bounding_Box
from java.awt 		import Rectangle
#from ij.plugin import CanvasResizer # does not allow to set a background value in gray level neither only rgb


def Rotate(ImProc, angle):
	'''
	This return a rotated version of the input ImageProcessor, filling the background with the modal value of the initial image
	For square rotation, prefer the rotateLeft/rotateRight method in ImageProcessor
	'''

	### Calculate width and height of rotated image ###
	# For this we simply use a ROI of the same size than the initial image, rotate it by the same angle and ask for the bounding box of this rotated rectangle 
	
	# Get size of the initial image
	w = ImProc.width
	h = ImProc.height
	
	# Generate a ROI of this size
	Rect = Roi(0,0,w,h)
	
	# Rotate this ROI
	RectRot = RoiRotator().rotate(Rect,angle)

	# Compute size of the new Image
	# For its dimensions we take for each dimension the largest length between the initial image size and the size of the rotated bounding rectangle 
	# otherwise the image gets cropped while rotated
	nw = max(w, int( RectRot.getFloatWidth()  ) )
	nh = max(h, int( RectRot.getFloatHeight() ) )

	'''
	# Previous way to compute new dimensions
	rangle = math.radians(angle)
	nw = abs(math.sin(rangle)*h) + abs(math.cos(rangle)*w)
	nh = abs(math.cos(rangle)*h) + abs(math.sin(rangle)*w)
	nw = int(round(nw))
	nh = int(round(nh))
	'''

	# Compute offset/translation vector to center initial image in the new canvas
	Xoff = (nw-w)//2
	Yoff = (nh-h)//2
	
	# Adjust canvas of the image
	IPnew = ImProc.createProcessor(nw, nh)

	# Compute modal value of initial image
	Gray = ImProc.getStats().dmode
	#print Gray
	
	# Fill background with define gray level
	IPnew.setValue(Gray)           # for fill
	IPnew.fill()
	
	# Insert previous image centered
	IPnew.insert(ImProc, Xoff, Yoff)
	IPnew.setBackgroundValue(Gray) # for rotate
	IPnew.rotate(angle)
	
	### Remove the extra border that can still be there after rotation. Not always working : background might not be recognised ###
	Rect0 = Rectangle(nw,nh) # intialise ROI of size of the image (where to compute the background)

	# Get ROI  
	BoxFinder = Select_Bounding_Box()
	bg        = BoxFinder.guessBackground(IPnew)
	NewRect   = BoxFinder.getBoundingBox(IPnew, Rect0, bg)
	#print NewRect
	
	# Crop 
	IPnew.setRoi(NewRect)
	IPnew = IPnew.crop()

	return IPnew


'''
# MAIN - Rotate the input image
Rotated = Rotate(Image.getProcessor(), 60)

# Display
NewImage = ImagePlus("Rotated", Rotated)
NewImage.show()
'''