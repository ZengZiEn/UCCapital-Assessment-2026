@echo off
setlocal
cd /d "%~dp0\.."

echo ========================================================================
echo [Step 1/5] Running Q1_Scheduling (C11 Bitboard + Python Main and Tests)...
echo ========================================================================
call Q1_Scheduling\scripts\run_all.bat
if errorlevel 1 exit /b 1

echo.
echo ========================================================================
echo [Step 2/5] Building and Running Q2_MemoryAllocator (Demo, Tests, Benchmark)...
echo ========================================================================
pushd Q2_MemoryAllocator
call scripts\build_and_run.bat
if errorlevel 1 (
    popd
    exit /b 1
)
popd

echo.
echo ========================================================================
echo [Step 3/5] Running Q3_PatternAnalysis (C11 Monte Carlo + Python Main and Tests)...
echo ========================================================================
call Q3_PatternAnalysis\scripts\run_all.bat
if errorlevel 1 exit /b 1

echo.
echo ========================================================================
echo [Step 4/5] Generating Main Technical Report PDF...
echo ========================================================================
python docs_and_tools\pdf_generator\build_report.py
if errorlevel 1 exit /b 1

echo.
echo ========================================================================
echo [Step 5/5] Generating Workflow and Thought Process PDF...
echo ========================================================================
python docs_and_tools\pdf_generator\build_workflow_pdf.py
if errorlevel 1 exit /b 1

echo.
echo ========================================================================
echo [Cleanup] Removing intermediate .obj and __pycache__ files...
echo ========================================================================
python -c "import os, shutil; [shutil.rmtree(os.path.join(r,d), True) for r,ds,_ in os.walk('.') for d in list(ds) if d=='__pycache__']; [os.remove(os.path.join(r,f)) for r,_,fs in os.walk('.') for f in fs if f.endswith(('.obj','.pyc'))]"

echo ========================================================================
echo [SUCCESS] Full pipeline verified and both PDF reports updated!
echo ========================================================================
endlocal
