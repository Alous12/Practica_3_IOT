#!/usr/bin/env bash
# Empaqueta la Lambda en build/lambda_deployment.zip (Linux/macOS/Git Bash).
set -euo pipefail
cd "$(dirname "$0")"

rm -rf package build
mkdir -p package build
python3 -m pip install --upgrade -r requirements.txt -t package
cp lambda_function.py package/
cp -r vigilante package/
find package -name __pycache__ -type d -prune -exec rm -rf {} +

# lambda_function.py debe quedar en la raíz del .zip
python3 -c "import shutil; shutil.make_archive('build/lambda_deployment', 'zip', 'package')"
echo "Listo: build/lambda_deployment.zip"
