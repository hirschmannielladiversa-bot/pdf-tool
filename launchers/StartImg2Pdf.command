#!/bin/zsh
cd "$(dirname "$0")/.." || exit 1
python3 "./src/img2pdf.py" --select-files
