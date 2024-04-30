@echo off
 
echo 'Beginning installation of FreeCAD-Omniverse Connector'
 
git clone https://github.com/raska-s/ovConnectSample.git temp

robocopy .\temp .\omniConnect /XO

del .\temp