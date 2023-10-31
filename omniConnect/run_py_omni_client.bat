@echo off

setlocal

pushd "%~dp0"

set ROOT_DIR=%~dp0
set USD_LIB_DIR=%ROOT_DIR%_build\windows-x86_64\release
set PYTHON=%ROOT_DIR%_build\target-deps\python\python.exe

set PATH=%PATH%;%USD_LIB_DIR%
set PYTHONPATH=%USD_LIB_DIR%\python;%USD_LIB_DIR%\bindings-python

if not exist "%PYTHON%" (
    echo Python, USD, and Omniverse Client libraries are missing.  Run "repo.bat build --stage" to retrieve them.
    popd
    exit /b
)

rem "%PYTHON%" source\pyHelloWorld\helloWorld.py %*

rem "%PYTHON%" source\pyHelloWorld\connectSampleLib.py --existing_nucleus_usd omniverse://localhost/Users/test/sandbox/defeature_simplify_from_step.usda%*

"%PYTHON%" source\pyHelloWorld\connectSampleLib.py %*

popd

EXIT /B %ERRORLEVEL%