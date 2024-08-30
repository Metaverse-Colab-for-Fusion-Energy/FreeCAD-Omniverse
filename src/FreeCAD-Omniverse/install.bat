@echo off

rem Can this be made private?? turn into an installer or something..

echo === BEGINNING INSTALLATION OF FREECAD OMNIVERSE CONNECTOR ===

echo --- Pulling Connect Sample v202.0...
 
git clone --quiet https://github.com/Metaverse-Colab-for-Fusion-Energy/ovConnectSample.git temp

rd ".\temp\.git\" /q /s

robocopy .\temp .\omniConnect /e /NFL /NDL /NJH /NJS 

robocopy .\omniConnect\source\PyHelloWorld\omni .\omniConnect\source\pyOmniFreeCAD\omni /e /NFL /NDL /NJH /NJS 

echo --- Cleaning Connect Sample dependency directory...

rd ".\temp\" /s /q

echo --- Fetching Connect Sample dependencies...

call .\omniConnect\repo.bat build --fetch-only

rd .\omniConnect\helloWorld /s /q
rd .\omniConnect\liveSession /s /q
rd .\omniConnect\omnicli /s /q
rd .\omniConnect\omniSensorThread /s /q 

rd .\omniConnect\omniSimpleSensor /s /q
rd .\omniConnect\omniUsdaWatcher /s /q
rd .\omniConnect\omniUsdReader /s /q
rd .\omniConnect\omniUtilsLib /s /q 
rd .\omniConnect\PyHelloWorld /s /q 

echo --- Fetching Python dependencies...

.\omniConnect\_build\target-deps\python\python.exe -m pip install open3d aioconsole --quiet

echo === INSTALLATION COMPLETE ===
