@echo off
setlocal

set "MSVC_DIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207"
set "SDK_INC=C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0"
set "SDK_LIB=C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0"

set "PATH=%MSVC_DIR%\bin\Hostx64\x64;C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64;%PATH%"
set "INCLUDE=%MSVC_DIR%\include;%SDK_INC%\ucrt;%SDK_INC%\shared;%SDK_INC%\um"
set "LIB=%MSVC_DIR%\lib\x64;%SDK_LIB%\ucrt\x64;%SDK_LIB%\um\x64"

if not exist build mkdir build

echo [Build 1/3] Compiling main_demo.exe...
cl.exe /nologo /O2 /W4 /utf-8 /I include src\my_malloc.c src\main_demo.c /Fe:build\main_demo.exe /Fo:build\
if errorlevel 1 exit /b 1

echo [Build 2/3] Compiling test_my_malloc.exe...
cl.exe /nologo /O2 /W4 /utf-8 /I include src\my_malloc.c tests\test_my_malloc.c /Fe:build\test_my_malloc.exe /Fo:build\
if errorlevel 1 exit /b 1

echo [Build 3/3] Compiling benchmark_malloc.exe...
cl.exe /nologo /O2 /W4 /utf-8 /I include src\my_malloc.c tests\benchmark_malloc.c /Fe:build\benchmark_malloc.exe /Fo:build\
if errorlevel 1 exit /b 1

echo.
build\main_demo.exe
if errorlevel 1 exit /b 1

echo.
build\test_my_malloc.exe
if errorlevel 1 exit /b 1

echo.
build\benchmark_malloc.exe
if errorlevel 1 exit /b 1

endlocal
