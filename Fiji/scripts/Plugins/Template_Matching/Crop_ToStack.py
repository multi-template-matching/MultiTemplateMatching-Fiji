#@ImagePlus imp
'''
From a list of rectangular ROI associated to some slices of a stack in Fiji
Crop each Roi from the image slice and append them to a stack
The size of the stack should be adjusted to match the ROI dimensions before running the macro

NB : if using with MultiTemplate Matching, using a non square template, the rotation yield different dimensiosn that do not fit in the stack
'''
from ij.plugin.frame import RoiManager
from ij import ImageStack, ImagePlus

RM = RoiManager.getRoiManager()
n = RM.getCount()

Roi1 = RM.getRoi(0)
Width  = int(Roi1.getFloatWidth())
Height = int(Roi1.getFloatHeight())
Stack = ImageStack(Width, Height)

for i in range(n):
	roi = RM.getRoi(i)
	ImIndex = roi.getPosition()
	#print ImIndex
	
	imp.setSlice(ImIndex)
	imp.setRoi(roi)
	Crop = imp.crop()
	Stack.addSlice( Crop.getProcessor() )

StackImp = ImagePlus("Stack",Stack)
StackImp.show()

