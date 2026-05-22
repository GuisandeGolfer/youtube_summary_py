#!/bin/bash

output="clipboard.txt"

# Empty the output file first (optional)
>"$output"

# Patterns to include
patterns=("*.py" "*.html" "*.md")

for pattern in "${patterns[@]}"; do
  for file in $pattern; do
    # Skip if no files match this pattern
    [ -e "$file" ] || continue

    echo "----- START OF $file -----" >>"$output"
    cat "$file" >>"$output"
    echo -e "\n----- END OF $file -----\n" >>"$output"
  done
done

echo "Done! Combined .py, .html, and .md files saved to $output"
