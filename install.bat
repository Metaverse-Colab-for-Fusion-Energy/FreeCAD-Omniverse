@echo off
 
echo 'Beginning installation of FreeCAD-Omniverse Connector'

echo 'Pulling Connect Sample v202.0'
 
git clone https://github.com/raska-s/ovConnectSample.git temp


Remove-Item -LiteralPath ".\temp\.git" -Force -Recurse

robocopy .\temp .\omniConnect /e

Remove-Item -LiteralPath ".\temp" -Force -Recurse