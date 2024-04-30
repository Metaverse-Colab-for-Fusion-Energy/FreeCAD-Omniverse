@echo off
 
echo 'Beginning installation of FreeCAD-Omniverse Connector'
 
git clone https://github.com/raska-s/ovConnectSample.git temp

copy .\temp\* .\omniConnect

del .\temp\ -r -fo