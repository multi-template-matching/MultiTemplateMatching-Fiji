'''
This module contains functions to converts from an ImagePlus (RGB, 32-bit, 16-bit...) to an opencv matrix and vice-versa
The default BitType of the opencv matricx is 8-bit
'''
from ijopencv.ij     import ImagePlusMatConverter
from ijopencv.opencv import MatImagePlusConverter 

ip2mat = ImagePlusMatConverter()
mat2ip = MatImagePlusConverter()

def ImProcToMat(ImProc, Bit=8):
	'''
	Convert an ImageProcessor to an opencv matrix with optionnal BitDepth conversion
	'''	
	# I - Convert the image Processor to a different BitType (if necessary)
	if ImProc.getBitDepth() != Bit:
		
		# For the conversion from higher to lower bitType the value are scaled
		# Similarly RGB to Gray result in a one channel gray image thanks to the ImageProcessor method
		if Bit == 8:
			ImProc = ImProc.convertToByteProcessor() # Boolean argument doScaling = True by default ?
		
		elif Bit == 16:
			ImProc = ImProc.convertToShortProcessor()
		
		elif Bit == 32:	
			ImProc = ImProc.convertToFloatProcessor()
		
		else:
			# left as is
			pass
	
	
	# II - Convert the image processor to an opencv matrix
	ImCV = ip2mat.toMat(ImProc)
	
	return ImCV

	
	
def MatToImProc(Mat):
	'''Convert an opencv matrix to an ImageProcessor of sane BitType'''
	IP = mat2ip.toImageProcessor(Mat)
	return IP