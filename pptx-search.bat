@echo off
setlocal EnableDelayedExpansion

:: Usage: pptx-search.bat "search term"
if "%~1"=="" (
    echo Usage: pptx-search.bat "search term"
    exit /b 1
)

:: Create a temporary directory for extraction
set "TEMP_DIR=%TEMP%\pptx_search_%RANDOM%"
mkdir "%TEMP_DIR%" 2>nul

:: Process each PPTX file in the current directory
for %%F in (*.pptx) do (
    echo Processing: %%F
    
    :: Extract the PPTX to the temp directory
    7z x "%%F" -o"%TEMP_DIR%\%%~nF" -y > nul
    
    :: Search through the extracted XML files, focusing on slide content
    cd "%TEMP_DIR%\%%~nF"
    for %%X in (ppt\slides\slide*.xml) do (
        rg -i "%~1" "%%X" > nul
        if !errorlevel! == 0 (
            echo Found in %%F - Slide %%~nX
            rg -i --context 1 "%~1" "%%X"
            echo.
        )
    )
    cd "%CD%"
    
    :: Clean up extracted files
    rd /s /q "%TEMP_DIR%\%%~nF"
)

:: Remove temporary directory
rd /s /q "%TEMP_DIR%"
endlocal