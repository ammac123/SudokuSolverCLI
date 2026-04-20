#!/bin/zsh
for ver in "3.11"; do
    find -f **/*.pth -exec rm {} +;
    uv run app --python="$ver" ;
done
find -f **/*.pth -exec rm {} +;