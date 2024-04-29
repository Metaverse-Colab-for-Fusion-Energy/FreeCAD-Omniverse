# FreeCAD Connector for NVIDIA Omniverse
This software connects CAD geometry on FreeCAD to NVIDIA Omniverse.

This has been tested for Windows devices (Win 10 & 11) with both local and remote Omniverse Nucleus setups, using Omniverse Connect Sample 202.0

## Installation
1. Clone this repository to your FreeCAD \Mod directory. Typically, this is C:\Users\username\AppData\Roaming\FreeCAD\Mod
2. Install Omniverse Connect Sample using the Omniverse Launcher. This package has been tested up to Connect Sample version 202.0
3. Copy the entire installation folder of Omniverse Connect Sample to this repository's directory. This is typically located in C:\USERNAME\AppData\Local\ov\pkg. 
4. Move the contents of ./omniConnect into the newly pasted Omniverse Connect Sample directory. 
5. Rename Omniverse Connect Sample directory name as 'omniConnect'
6. Go to /omniConnect directory, and run "repo.bat build --stage"
7. Installation complete.

NOTE: EXTRA PACKAGES NEED TO BE INSTALLLED IN THE LOCAL PYTHON.EXE OF OMNIVERSE CONNECT SAMPLE. TODO PUT STEPS FOR THIS AND MAYBE AUTOMATE
List of extra packages: open3d
