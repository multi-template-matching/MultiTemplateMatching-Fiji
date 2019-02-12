# -*- coding: utf-8 -*-
"""
-Python2-

Non maxima supression for match template

Let say we have a correlation map and we want to detect the N best location in this map, while we want to make sure the detected location do not overlap too much
The threshold for the overlap used is a maximal value of Intersection over Union (IoU). Large overlap will have large IoU.
The IoU is conveneient as it is normalised between 0 and 1 and is a value normalised by the intial area.

To keep the N best hit/bounding-box without overlap, we first take the N best hit as returned by the maxima detector
Then we loop over the best hit (by decreasing order of score, best score first) and compute the IoU with each remaning bounding box
If the IoU is too high, the second bounding box is deleted and replaced by the N+1 th (or N + offset) bounding box in the intiial list of hit

ListOfHit contains N dictionnaries, 1/hit : {'TemplateIdx':i, 'BBox':(x,y,width,hieght), 'Score':float} 

@author: Laurent Thomas
"""
from __future__ import division
from ij.gui 	import Roi

def computeIoU(BBox1,BBox2):
	'''
	Compute the IoU (Intersection over Union) between 2 rectangular bounding boxes defined by the top left (Xtop,Ytop) and bottom right (Xbot, Ybot) pixel coordinates
	Code adapted from https://www.pyimagesearch.com/2016/11/07/intersection-over-union-iou-for-object-detection/
	'''
	print 'BBox1 : ', BBox1
	print 'BBox2 : ', BBox2
	
	# Unpack input (python3 - tuple input are no more supported)
	Xleft1, Ytop1, Width1, Height1 = BBox1
	Xleft2, Ytop2, Width2, Height2 = BBox2
	
	# Compute bottom coordinates
	Xright1 = Xleft1 + Width1  -1 # we remove -1 from the width since we start with 1 pixel already (the top one)
	Ybot1   = Ytop1  + Height1 -1 # idem for the height

	Xright2 = Xleft2 + Width2  -1
	Ybot2   = Ytop2  + Height2 -1

	# determine the (x, y)-coordinates of the top left and bottom right points of the intersection rectangle
	Xleft  = max(Xleft1, Xleft2)
	Ytop   = max(Ytop1, Ytop2)
	Xright = min(Xright1, Xright2)
	Ybot   = min(Ybot1, Ybot2)
	
	# Generate a Roi for the BBox just to be able to check that the BBox are not contained within another
	Roi1 = Roi(Xleft1, Ytop1, Width1, Height1)
	Roi2 = Roi(Xleft2, Ytop2, Width2, Height2)
	
	# Get boolean if BBox within another one (simply test contain with each corner point)
	Roi1_in_Roi2 = Roi2.contains(Xleft1, Ytop1) and  Roi2.contains(Xright1, Ytop1) and Roi2.contains(Xleft1, Ybot1) and Roi2.contains(Xright1, Ybot1)
	Roi2_in_Roi1 = Roi1.contains(Xleft2, Ytop2) and  Roi1.contains(Xright2, Ytop2) and Roi1.contains(Xleft2, Ybot2) and Roi1.contains(Xright2, Ybot2)
	
	if Roi1_in_Roi2 or Roi2_in_Roi1:
		print '1 BBox is included within the other'
		IoU = 1 # otherwise using the formula below we have value below 1 eventhough the bbox are included
	
	elif Xright<Xleft or Ybot<Ytop : #  (Y axis oriented towards the bottom of the screen) Check that for the intersection box, Xtop,Ytop is indeed on the top left of Xbot,Ybot otherwise it means that there is no intersection (bbox is inverted)
		print 'No overlap'
		IoU = 0 
	
	else:
		# Compute area of the intersecting box
		Inter = (Xright - Xleft + 1) * (Ybot - Ytop + 1) # +1 since we are dealing with pixels. See a 1D example with 3 pixels for instance
		#print('Intersection area : ', Inter)

		# Compute area of the union as Sum of the 2 BBox area - Intersection
		Union = Width1 * Height1 + Width2 * Height2 - Inter
		#print('Union : ', Union)
		
		# Compute Intersection over union
		IoU = Inter/Union
	
	print 'IoU : ', IoU
	return IoU




def NMS(List_Hit, scoreThreshold=None, sortDescending=True, N=1000, maxOverlap=0.7):
	'''
	Perform Non-Maxima supression : it compares the hits after maxima/minima detection, and removes the ones that are too close (too large overlap)
	This function works both with an optionnal threshold on the score, and number of detected bbox

	if a scoreThreshold is specified, we first discard any hit below/above the threshold (depending on sortDescending)
	if sortDescending = True, the hit with score below the treshold are discarded (ie when high score means better prediction ex : Correlation)
	if sortDescending = False, the hit with score above the threshold are discared (ie when low score means better prediction ex : Distance measure)

	Then the hit are ordered so that we have the best hits first.
	Then we iterate over the list of hits, taking one hit at a time and checking for overlap with the previous validated hit (the Final Hit list is directly iniitialised with the first best hit as there is no better hit with which to compare overlap)	
	
	This iteration is terminate once we have collected N best hit, or if there are no more hit left to test for overlap 
   
   INPUT
	- ListHit		: 	a list of hit as dictionnaries, with at least an item 'BBox'=(x,y,width,height) and 'Score'=(float)
						Extra fileds are possible ex:
						{'TemplateName'= (string),'BBox'=(x,y,width,height),'Score'=(float)}
						
	- scoreThreshold : Float (or None), used to remove hit with too low prediction score. 
					   If sortDescending=True (ie we use a correlation measure so we want to keep large scores) the scores above that threshold are kept
					   While if we use sortDescending=False (we use a difference measure ie we want to keep low score), the scores below that threshold are kept
					   
	- N				 : number of best hit to return (by increasing score). Min=1, eventhough it does not really make sense to do NMS with only 1 hit
	- maxOverlap	 : float between 0 and 1, the maximal overlap authorised between 2 bounding boxes, above this value, the bounding box of lower score is deleted
	- sortDescending : use True when high score means better prediction, False otherwise (ex : if score is a difference measure, then the best prediction are low difference and we sort by ascending order)

	OUTPUT
	List_nHit : List of the best detection after NMS, it contains max N detection (but potentially less)
	'''
	if len(List_Hit)<=1:
		FinalHit = List_Hit
			
	else:
		# Apply threshold on prediction score
		if scoreThreshold==None :
			List_ThreshHit = List_Hit[:] # copy to avoid modifying the input list in place
		
		elif sortDescending : # We keep hit above the threshold
			List_ThreshHit = [dico for dico in List_Hit if dico['Score']>=scoreThreshold]

		elif not sortDescending : # We keep hit below the threshold
			List_ThreshHit = [dico for dico in List_Hit if dico['Score']<=scoreThreshold]
		
		
		# Sort score to have best predictions first (important as we loop testing the best boxes against the other boxes)
		if sortDescending:
			List_ThreshHit.sort(key=lambda dico: dico['Score'], reverse=True) # Hit = [list of (x,y),score] - sort according to descending (best = high correlation)
		else:
			List_ThreshHit.sort(key=lambda dico: dico['Score']) # sort according to ascending score (best = small difference)
		#print "Sorted List", List_ThreshHit
		
		# Split the inital pool into Final Hit that are kept and restHit that can be tested
		# Initialisation : 1st keep is kept for sure, restHit is the rest of the list
		print "\nInitialise final hit list with first best hit"
		FinalHit = [List_ThreshHit[0]]
		restHit	 = List_ThreshHit[1:]
		
		print "-> Final hit list"
		for hit in FinalHit: print hit
		
		print "\n-> Remaining hit list"
		for hit in restHit: print hit
		
		
		
		# Loop to compute overlap
		while len(FinalHit)<N and restHit : # second condition is restHit is not empty
			
			# Report state of the loop
			print "\n\n\nNext while iteration"
			
			print "-> Final hit list"
			for hit in FinalHit: print hit
			
			print "\n-> Remaining hit list"
			for hit in restHit: print hit
			
			# pick the next best peak in the rest of peak
			test_hit  = restHit[0]
			test_bbox = test_hit['BBox']
			print "\nTest BBox:{} for overlap against higher score bboxes".format(test_bbox)
			 
			# Loop over hit in FinalHit to compute successively overlap with test_peak
			for hit in FinalHit: 
				
				# Recover Bbox from hit
				bbox2 = hit['BBox']	 
				
				# Compute the Intersection over Union between test_peak and current peak
				IoU = computeIoU(test_bbox, bbox2)
				
				# Initialise the boolean value to true before test of overlap
				ToAppend = True 
		
				if IoU>maxOverlap:
					ToAppend = False
					print "IoU above threshold\n"
					break # no need to test overlap with the other peaks
				
				else:
					print "IoU below threshold\n"
					# no overlap for this particular (test_peak,peak) pair, keep looping to test the other (test_peak,peak)
					continue
		  
			
			# After testing against all peaks (for loop is over), append or not the peak to final
			if ToAppend:
				# Move the test_hit from restHit to FinalHit
				print "Append {} to list of final hits and remove it from Remaining hit list".format(test_hit)
				FinalHit.append(test_hit)
				restHit.remove(test_hit)
				
			else:
				# only remove the test_peak from restHit
				print "Remove {} from Remaining hit list".format(test_hit)
				restHit.remove(test_hit)
		
		
		# Once function execution is done, return list of hit without overlap
		print "\nCollected N expected hit, or no hit left to test"
	
	
	print "NMS over\n"
	return FinalHit



	
if __name__ == "__main__":
	Hit1 = {'TemplateName':"Initial",'BBox':(780, 350, 700, 480), 'Score':0.8}
	Hit2 = {'TemplateName':"Initial",'BBox':(806, 416, 716, 442), 'Score':0.6}
	Hit3 = {'TemplateName':"Initial",'BBox':(1074, 530, 680, 390), 'Score':0.4}

	ListHit = [Hit1, Hit2, Hit3]

	ListFinalHit = NMS(ListHit)

	print ListFinalHit