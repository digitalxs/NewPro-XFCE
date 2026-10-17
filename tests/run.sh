#!/bin/sh
# Run the NewPro-XFCE test suite from the repository root.
cd "$(dirname "$0")/.." && exec python3 -m unittest discover -s tests -t . -v "$@"
