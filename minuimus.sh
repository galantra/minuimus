#!/bin/bash

# Define an array to store the folder paths
folders=(
    "C:\Users\emanresu\Pictures\Bing-Bilder"
)

# Iterate over each folder in the array
for folder in "${folders[@]}"; do
    # Find all JPG and PNG files in the folder
    # Pass them to xargs for further processing using Minuimus tool
    # The -P option specifies the number of parallel processes to run
    # The -0 option ensures filenames with spaces are handled correctly
    # The -n option sets the maximum number of arguments passed to each command
    # The command "perl minuimus.pl" is executed on each batch of files

    find "$folder" -type f \( -name "*.jpg" -o -name "*.png" \) -print0 | xargs -P 4 -0 -n 4 perl minuimus.pl --zip-7z # --jpg-webp --png-webp
done
