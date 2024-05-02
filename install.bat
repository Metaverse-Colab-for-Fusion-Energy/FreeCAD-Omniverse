@echo off
 
echo 'Beginning installation of FreeCAD-Omniverse Connector'

echo 'Pulling Connect Sample v202.0'
 
git clone https://github.com/raska-s/ovConnectSample.git temp


rd ".\temp\.git\" /q /s

robocopy .\temp .\omniConnect /e

rd ".\temp\" /s /q