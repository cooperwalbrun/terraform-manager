#!/bin/bash

pip-compile --upgrade --output-file=requirements/base.txt

IS_LINUX=$(python -c "import sys; print(sys.platform in ['linux2', 'linux'])")
if [ "$IS_LINUX" == "True" ]; then
  echo "-r base.txt" > requirements/linux.txt

  # Add system-dependent logic here as needed (like we did for Windows)
fi

IS_WINDOWS=$(python -c "import sys; print(sys.platform in ['win32', 'cygwin', 'msys'])")
if [ "$IS_WINDOWS" == "True" ]; then
  echo "-r base.txt" > requirements/windows.txt

  # Copy the pywin32 line from the base.txt requirements to the windows.txt requirements
  # This uses a regular expression, so just add pipe delimiters to handle multiple dependencies
  sed '/pywin32.*/!d' requirements/base.txt >> requirements/windows.txt

  # Remove the pywin32 line from the base.txt requirements
  # This uses a regular expression, so just add pipe delimiters to handle multiple dependencies
  sed -i '/pywin32.*/d' requirements/base.txt
fi
