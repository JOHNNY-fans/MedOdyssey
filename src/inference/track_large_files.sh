#!/bin/bash
find . -type f -size +50M | while read filename; do
    git lfs track "$filename"
    echo "$filename" >> .gitattributes
done
