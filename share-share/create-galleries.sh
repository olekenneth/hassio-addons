find . -type f -name '*.jpg' -exec sh -c 'for d; do dirname "$d"; done' sh {} + | sort -u -o jpeg_dirs.txt
while read line; do gallery-init -p $line; done < jpeg_dirs.txt
gallery-build
