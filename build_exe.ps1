$ErrorActionPreference = "Stop"

$python = "C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe"
$condaBin = "C:/ProgramData/spyder-6/envs/spyder-runtime/Library/bin"

& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --noconsole `
  --name TenderMonitor `
  --add-data "config;config" `
  --add-binary "$condaBin/libcrypto-3-x64.dll;." `
  --add-binary "$condaBin/libssl-3-x64.dll;." `
  --add-binary "$condaBin/sqlite3.dll;." `
  --add-binary "$condaBin/ffi-8.dll;." `
  --add-binary "$condaBin/libbz2.dll;." `
  --add-binary "$condaBin/liblzma.dll;." `
  --add-binary "$condaBin/tcl86t.dll;." `
  --add-binary "$condaBin/tk86t.dll;." `
  --add-binary "$condaBin/yaml.dll;." `
  app_gui.py

Write-Host "Build completed: dist/TenderMonitor.exe"
