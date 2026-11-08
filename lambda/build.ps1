# Empaqueta la Lambda en build\lambda_deployment.zip (Windows PowerShell).
# Uso, desde la carpeta lambda\:   .\build.ps1
# Si PowerShell bloquea el script:  powershell -ExecutionPolicy Bypass -File .\build.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Remove-Item -Recurse -Force package, build -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path package, build | Out-Null

# ask-sdk-core es Python puro, así que se puede instalar desde Windows sin problemas.
python -m pip install --upgrade -r requirements.txt -t package

Copy-Item lambda_function.py package\
Copy-Item -Recurse vigilante package\vigilante
Get-ChildItem -Recurse -Directory -Filter __pycache__ package | Remove-Item -Recurse -Force

# El .zip debe tener lambda_function.py en la RAÍZ (no dentro de una carpeta).
# Se usa Python (no Compress-Archive) porque PowerShell 5.1 guarda rutas con "\"
# y Lambda (Linux) no encontraría el paquete vigilante/.
python -c "import shutil; shutil.make_archive('build/lambda_deployment', 'zip', 'package')"
Write-Host "Listo: build\lambda_deployment.zip"
