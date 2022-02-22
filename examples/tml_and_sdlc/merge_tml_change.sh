#!/bin/bash
#
# Simple bash implementation of merging changes from a copied ThoughtSpot object back into the original file
# Preserves git change tracking and the GUID of the original object so it can be republished as update to ThoughtSpot
# Does not include deleting the child object on disk or on ThoughtSpot, or any git commits
#

# Copy first line from original / parent into tmp file
sed -n 1p $1 > tmp.tml
# Copy all lines from the the child / modified copy
sed 1d $2 >> tmp.tml
# Copy the temp contents into the original file, to keep the change tracking in Git
cp tmp.tml $1
# Delete temp file
rm tmp.tml