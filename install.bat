@echo off
 
echo Beginning installation of FreeCAD-Omniverse Connector

echo Pulling Connect Sample v202.0...
 
git clone https://github.com/raska-s/ovConnectSample.git temp

rd ".\temp\.git\" /q /s

robocopy .\temp .\omniConnect /e

echo Cleaning dependency directory...

rd ".\temp\" /s /q

echo Building Connect Sample...

call .\omniConnect\repo.bat build --fetch-only

echo Installing Python dependencies...

.\omniConnect\_build\target-deps\python\python.exe -m pip install open3d aioconsole