/*
 * This macro allows to do a 2-step template matching
 * The first template allows to find an object and the second template finds a sub-object within the previously found object
 * Therefore the second template must be smaller than the first one
 * Both detection (1st and 2nd template) are returned in the ROI manager
 * 
 */
#@ImagePlus (Label="Template1") temp1
#@ImagePlus (Label="Template2") temp2
#@ImagePlus (Label="Image") image

// Show all ROI and associate with Slices 
roiManager("Show All");
roiManager("Associate", "true");

// Get image names
selectImage(temp1);
Temp1_title = getTitle();
//print(Temp1_title);

selectImage(temp2);
Temp2_title = getTitle();
//print(Temp2_title);

selectImage(image);
Image_title = getTitle();
//print(Image_title);

// Call 1st template matching
Start_Temp1 = getTime();
run("Template Matching Image", "template=" + Temp1_title + " image=" + Image_title + " rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_templates=1 score_threshold=0.50 min_peak_height=0.10 maximal_overlap=0.25 add_roi");
Stop_Temp1 = getTime();

AverageTimeTemp1 = (Stop_Temp1 - Start_Temp1)/96;

// Loop over stack
print("Average time per image(ms)");
setBatchMode(true); // do not open extracted slices
selectImage(image);
Roi.remove;
n = nSlices;
for (i=1; i<=n; i++) {

	Start_Temp2 = getTime();
	
	// Isolate slice from stack (to perform the second template matching with a custom search ROI for that slice)
	selectImage(image); //important here to select back the image when entering a new iteration
	setSlice(i);
	run("Duplicate...", "title=Slice");
	
	// Set search ROI on isolated slice
	roiManager("select", i-1); // i-1 since ROI manager starts at 0
	Roi.getBounds(x, y, width, height);
	makeRectangle(x, y, width, height);

	// Run template matching on slice with search ROI
	run("Template Matching Image", "template=" + Temp2_title + " image=Slice flip_template_vertically rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_templates=2 score_threshold=0.50 min_peak_height=0 maximal_overlap=0.25 add_roi");

	// Close hidden Slice image
	selectImage("Slice");
	close();
	
	// Rename and Set Z-position of the last found ROI
	nRoi = roiManager("count");

	// Eye 1
	roiManager("select", nRoi-1);
	run("Properties... ", "position="+i); // Set slice position
	InitName = call("ij.plugin.frame.RoiManager.getName", nRoi-1);
	roiManager("rename", i + substring(InitName, 1));

	// Eye 2
	roiManager("select", nRoi-2);
	run("Properties... ", "position="+i); // Set slice position
	InitName = call("ij.plugin.frame.RoiManager.getName", nRoi-2);
	roiManager("rename", i + substring(InitName, 1));
	Roi.remove; // the stack is displayed back at the first slice for some reason

	Stop_Temp2 = getTime();
	AverageTimeTemp2 = Stop_Temp2 - Start_Temp2;

	print(AverageTimeTemp1+AverageTimeTemp2);
}

// Again make sure that all ROI are displayed and associated to the slices
roiManager("Show All");
roiManager("Associate", "true");