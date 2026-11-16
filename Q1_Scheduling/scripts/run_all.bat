@echo off
setlocal
cd /d "%~dp0\.."

set "MSVC_DIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207"
set "SDK_INC=C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0"
set "SDK_LIB=C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0"
set "PATH=%MSVC_DIR%\bin\Hostx64\x64;C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64;%PATH%"
set "INCLUDE=%MSVC_DIR%\include;%SDK_INC%\ucrt;%SDK_INC%\shared;%SDK_INC%\um"
set "LIB=%MSVC_DIR%\lib\x64;%SDK_LIB%\ucrt\x64;%SDK_LIB%\um\x64"

if not exist build mkdir build

echo ========================================================================
echo [Q1_Scheduling] Building Native C11 Bitboard/SWAR Engine...
echo ========================================================================
cl.exe /nologo /O2 /W4 /utf-8 src_native\fast_scheduler.c /Fe:build\fast_scheduler.exe /Fo:build\
if errorlevel 1 exit /b 1

echo.
build\fast_scheduler.exe
if errorlevel 1 exit /b 1

echo.
echo ========================================================================
echo [Q1_Scheduling] Running Python Main Demonstration...
echo ========================================================================
python -m src.main
if errorlevel 1 exit /b 1

echo.
echo ========================================================================
echo [Q1_Scheduling] Running Python Unit Test Suite...
echo ========================================================================
python -m unittest tests.test_scheduling -v
if errorlevel 1 exit /b 1

endlocal
