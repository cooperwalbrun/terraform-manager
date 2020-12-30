#!/bin/bash

pip-compile --upgrade --output-file=requirements/base.txt

echo "-r base.txt" > requirements/linux.txt
echo "-r base.txt" > requirements/windows.txt

# Copy the pywin32 line from the base.txt requirements to the windows.txt requirements
# This uses a regular expression, so just add pipe delimiters to handle multiple dependencies
sed '/pywin32.*/!d' requirements/base.txt >> requirements/windows.txt

# Remove the pywin32 line from the base.txt requirements
# This uses a regular expression, so just add pipe delimiters to handle multiple dependencies
sed -i '/pywin32.*/d' requirements/base.txt
