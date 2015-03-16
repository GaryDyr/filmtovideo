# filmtovideo
Explore and devise process to convert projected film, e.g. 8mm, to digital video.
Explore and devise process to convert projected film, e.g. 8mm, to digital video.

Project explores the issues and demonstrates the feasibility of using a digital camcorder 
or camera in video mode for recording of projected 8 mm film. The concept is to use software 
to remove or reduce the impact of the projector shutter shadow image on each frame of digital video. 
The methods used involve identifying the position of the shutter image on a video frame and 
removing it from the video frame, using a projector-specific luminance profile of the shutter image. 

A detailed and large MSWord document file explores the shutter image characteristics and its 
relationship to the video recording process, and presents a proof of concept software solution
to removing or reducing the shutter image impact on a video frame. 

The work is dependent on a variety of software tools with scripts to explore the 
conversion process and remove the shutter image, includingImageJ/FIJI, MS Excel, R, and VirtualDub.  
The main scripts to reduce or remove shutter shadows are written in python/jython for use with ImageJ
or FIJI. They work, they are not pretty, and are definitely not the most efficient. More sophisticated
input on the luminance control of the removal process is needed.
