#!/bin/sh

echo_verbose() {
    if [ "$verbose" = "true" ]; then
        echo "$@"
    fi
}

# check if verbose is set ("-v" or "--verbose")
verbose=false
if [ "$1" = "-v" ] || [ "$1" = "--verbose" ]; then
    verbose=true
fi

# verify that script is run from curr directory
if [ ! -f "get_dataset.sh" ]; then
    echo "Error: this script must be run from inside 'data/cicids2017/engelen_paper'"
    exit 1
fi

echo_verbose "downloading zip file"
wget https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip

echo_verbose "unzipping dataset"
unzip CICIDS2017_improved.zip

echo_verbose "removing zip file"
rm CICIDS2017_improved.zip

echo_verbose "merging csv files"
python3 merge_csvs.py

# NOTE: uncomment this to remove the split files (needed only for `pragmatic_assessment`)
# for file in *.csv; do
# 	if [ "$file" != "cicids2017.csv" ]; then
# 		rm "$file"
# 		echo_verbose "removed $file"
# 	fi
# done
