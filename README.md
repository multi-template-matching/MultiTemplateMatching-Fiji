[![DOI](https://zenodo.org/badge/DOI/10.1186/s12859-020-3363-7.svg)](https://doi.org/10.1186/s12859-020-3363-7)
![Twitter Follow](https://img.shields.io/twitter/follow/LauLauThom?style=social)

# Installation

## Via the Fiji updater
Tick the __Multi-Template-Matching__ AND __IJ-OpenCV__ update site of the Fiji udpater.  
A new entry will show up in the Plugin Menu (all the way down) after restarting Fiji.

## Manual installation
You can also do a manual installation by copying the files in the right place.  
This can be useful if you would like to use a previous version that is not available via the update site, but which is archived in the releases tab.  
You still need to tick the IJ-OpenCV update site in the Fiji updater to install the dependencies.  

Then you can download the files either on the main page above this readme, by clicking the green button with the arrow pointing down *Code* then *Download ZIP*.  
You can download the zip of previous versions on the [release tab](https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/releases), below asset select *Source code (zip)*.  
Unzip the file and copy the folder Fiji.app to an existing Fiji installation.  
More precisly copy the unzipped into the same parent directory than your current Fiji's Fiji.app (like the Desktop) to merge both directories: the files from Multi-Template-Matching will automatically be copied ot the right subdirectories.  

# Documentation
Template matching is an algorithm that can be used for object-detections in images.  
The algorithm computes the probability to find one (or several) template images provided by the user.  
See the [wiki section](https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/wiki/) for the documentation.  

You can find a similar implementation in:
- [Python](https://github.com/multi-template-matching/MultiTemplateMatching-Python)
- [KNIME](https://github.com/multi-template-matching/MultipleTemplateMatching-KNIME) relying on the python implementation



# Citation
If you use this implementation for your research, please cite:
  
Thomas, L.S.V., Gehrig, J. _Multi-template matching: a versatile tool for object-localization in microscopy images._     
BMC Bioinformatics 21, 44 (2020). https://doi.org/10.1186/s12859-020-3363-7

# Related resources
## IJ-OpenCV
This plugin is using OpenCV in Fiji thanks to [IJ-OpenCV](https://github.com/joheras/IJ-OpenCV).

see also:  
_Domínguez, César, Jónathan Heras, and Vico Pascual. "IJ-OpenCV: Combining ImageJ and OpenCV for processing images in biomedicine." Computers in biology and medicine 84 (2017): 189-194._

   
# Licence
<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br />The content of this wiki (including illustrations and videos) is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.

As a derived work of IJ-OpenCV, the source codes are licensed under GPL-3.

# Origin of the work
This work has been part of the PhD project of **Laurent Thomas** under supervision of **Dr. Jochen Gehrig** at ACQUIFER.   

<img src="https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/blob/master/Images/Acquifer_Logo_60k_cmyk_300dpi.png" alt="Fish" width="400" height="80">     

# Funding
This project has received funding from the European Union’s Horizon 2020 research and innovation program under the Marie Sklodowska-Curie grant agreement No 721537 ImageInLife.  

<p float="left">
<img src="https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/blob/master/Images/ImageInlife.png" alt="ImageInLife" width="130" height="100">
<img src="https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/blob/master/Images/MarieCurie.jpg" alt="MarieCurie" width="130" height="130">
</p>


# Examples

## Zebrafish head detection
<img src="https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/blob/master/Images/FishRoi.JPG" alt="Fish" width="300" height="300"> 
<img src="https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/blob/master/Images/Montage_Head.png" alt="MontageHead" width="500" height="300">

Dataset available on Zenodo  
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2650162.svg)](https://doi.org/10.5281/zenodo.2650162)


## Medaka larvae detections
<img src="https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/blob/master/Images/EggDetected.png" alt="MedakaEgg" width="250" height="250">
<img src="https://github.com/multi-template-matching/MultiTemplateMatching-Fiji/blob/master/Images/MontageEgg.png" alt="MontageEgg" width="650" height="250">  

Image courtesy Jakob Gierten (COS, Heidelberg)  
Dataset available on Zenodo    
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2650147.svg)](https://doi.org/10.5281/zenodo.2650147)
