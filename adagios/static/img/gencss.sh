#!/bin/bash

# This script generates CSS for sprite type pictures.
#
# First you need to convert all images to 16X16 (imagemagick)
# Second, imagemagick montage them into a single image
# 

x=0
y=0
for i in /tmp/glyphicons_free/glyphicons/png/glyphicons_*png
do
	class=$(echo $i|sed 's/^.*[0-9]_//g'|sed 's/_/-/g'|sed 's/.png$//')
	echo ".glyph-${class} {"
	echo "	background-position: -$(( ${x} * 16 ))px -$(( ${y} * 16 ))px;"
	echo "}"
	#echo ${y}/${x} ${class}

	x=$(( $x + 1 ))
	if [ $x -gt 19 ]; then
		x=0
		y=$(( $y + 1 ))
	fi
	if [ $y -gt 19 ]; then
		break
	fi
done

