# TerrainWithHole
This repository is made to learn how to make hole in terrain.
I tried two methods. The first is to partly remove geometry data from terrain by using memoryview. 
The second is to draw a shape on a hightmap by OpenCV, make the shape transparent, and use 'discard' in a shader, which was inspired by the panda3D community site "https://discourse.panda3d.org/". 
The first way does not need to use 'discard' in shaders.
And made it possible for the character to go through the hole by embedding a plane model under ground near the hole, and ignoring the collision between the character and terrain if the embedded plane model is detected by ray cast. 

# Requirements
* Panda3D 1.10.14
* numpy 2.1.2
  
# Environment
* Python 3.11
* Windows11

# Usage
* Execute a command below on your command line.
```
>>>python terrain_with_hole.py
```
# Controls:
* Press [Esc] to quit.
* Press [up arrow] key to go foward.
* Press [left arrow] key to turn left.
* Press [right arrow] key to turn right.
* Press [down arrow] key to go back.
* Press [ D ] key to toggle debug ON and OFF.
