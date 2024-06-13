# FreeCAD Connector for NVIDIA Omniverse
This software makes CAD geometry created on FreeCAD available on NVIDIA Omniverse in STEP and USD formats.

![freecad-conn](https://github.com/raska-s/FreeCAD-Omniverse/assets/75393569/d849faed-d431-49b6-a44b-b1243f19e34d)

## System requirements (what we have tested this to work on)
- OS: Windows 10 and 11
- FreeCAD: 0.20, 0.21.1, 0.21.2
- Nucleus: Local and remote
- Omniverse Connect Sample: 202.0
---

## Installation
1. Clone this repository. 

2. Copy and paste the contents of the `src` folder into your FreeCAD \Mod directory. Typically, this is `C:\Users\username\AppData\Roaming\FreeCAD\Mod`

> Note: if the `AppData\Roaming\FreeCAD\Mod` file directory does not exist, you must first initialise this folder. This happens if no FreeCAD addons have been previously installed. To do this, launch FreeCAD, and on the toolbar click `Tools` > `Addon Manager`. If you are using the Addon Manager for the first time, a dialog box will open, warning you that the addons in the Addon manager are not officially part of FreeCAD. It also presents several options related to the Addon Manager's data usage. Adjust those options to your liking and press the `OK` button to continue. The `\Mod` directory should now exist. 

2. Launch the installation by running `install.bat`. This will fetch the dependencies required to run the software. 

3. Installation complete.


## Documentation
> documentation to be added

## TODO
- delete useless pyfiles
- test fresh install again
