@echo off
setlocal enabledelayedexpansion

rem A script to clean the folder and return it to the initial condition



if not exist ".\omniConnect\build.bat" (
    echo OV connector not built yet, nothing to clean. Cancelling script.
    exit /b
)


echo === CLEANING FREECAD OMNIVERSE CONNECTOR ===
call .\omniConnect\build.bat --clean

REM Define the directory
set target_dir=.\omniConnect

REM List of files and directories to keep
set keep_files="run_py_omni_client.bat" "run_py_omni_live_client.bat"
set keep_dirs="source" "source/pyOmniFreeCAD"

REM Change directory to the target directory
cd %target_dir%

REM Debugging output to check the current directory and the files to keep
rem echo Current directory: %cd%
rem echo Keeping files: %keep_files%
rem echo Keeping directories: %keep_dirs%
rem echo.

REM Delete all files except the ones listed in keep_files
for %%f in (*.*) do (
    set "delete_file=true"
    for %%k in (%keep_files%) do (
        if /I "%%f"=="%%~k" (
            set "delete_file=false"
            rem echo Skipping file %%f
        )
    )
    if "!delete_file!"=="true" (
        rem echo Deleting file %%f
        del "%%f"
    )
)

REM Delete all directories except the ones listed in keep_dirs
for /D %%d in (*) do (
    set "delete_dir=true"
    for %%k in (%keep_dirs%) do (
        if /I "%%d"=="%%~k" (
            set "delete_dir=false"
            rem echo Skipping directory %%d
        )
    )
    if "!delete_dir!"=="true" (
        rem echo Deleting directory %%d
        rd /s /q "%%d"
    )
)

if exist "..\session_local" (
	rd ..\session_local /s /q
)


echo === CLEANING COMPLETE ===
REM End script
endlocal
