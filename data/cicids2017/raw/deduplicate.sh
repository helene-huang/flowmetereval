#!/bin/bash
# Default mode
# 
# deduplicate.sh calls fix_reorder.sh prior to fixing the duplicated packets
# Behaviour:
# * if no deduplication is provided, applies no-dedup by default
# * --lanvin-dedup for applying Lanvin deduplication method (described below in comments)
# * --liu-dedup for applying Liu deduplication method (described below).
# * --no-dedup stands for no-deduplication, it only applies fix_reorder.sh
# 
# The flag --no-fix-reorder is used to bypass the fix_reorder.sh script
# 
# Usage: ./deduplicate.sh [--no-dedup, --lanvin-dedup, --liu-dedup] inp_file out_file
# @Author: Sébastien Bois (integrates code pieces from Maxime Lanvin and Lisa Liu)

MODE="no-dedup"
FIX_REORDER=1
POSITIONAL=()

# Parse all arReorderingguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-dedup|--lanvin-dedup|--liu-dedup)
      MODE="${1#--}"
      shift
      ;;
    --no-fix-reorder)
      FIX_REORDER=0
      shift
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

INPUT_FOLDER="${POSITIONAL[0]}"
OUTPUT_FOLDER="${POSITIONAL[1]}"

# Validate required arguments
if [[ -z "$INPUT_FOLDER" || -z "$OUTPUT_FOLDER" ]]; then
  echo "Error: input_file and output_file are required."
  echo "Usage: $0 [--no-fix-reorder] [--no-dedup|--lanvin-dedup|--liu-dedup] input_file output_file"
  exit 1
fi

echo "Fix and reorder : $FIX_REORDER"
echo "Mode: $MODE"
echo "Input:  $INPUT_FOLDER"
echo "Output: $OUTPUT_FOLDER"

mkdir -p $OUTPUT_FOLDER

# Fix & reorder script from Hélène
if (( $FIX_REORDER == 1 )) ; then
  bash ./fix_reorder.sh $INPUT_FOLDER
fi

# Remove deduplicates depending on the choosen mode
DEDUP_THRESHOLD=0.0005

# Dispatch
case "$MODE" in
  lanvin-dedup)
    # Lanvin preprocessing applies editcap on every packets and removes those who are identical and fall into a 500µs time window
    echo "Running Lanvin dedup..."
    for pcap in $(find $INPUT_FOLDER -type f -iname "*.pcap" -printf "%f\n"); do
        echo Deduplicating $pcap...
        editcap -w $DEDUP_THRESHOLD $INPUT_FOLDER/$pcap "$OUTPUT_FOLDER/$pcap"
    done
    echo Duplicated packets have been removed from all the PCAP files in $INPUT_FOLDER
    ;;
  liu-dedup)
    # Liu raised that non-duplicated packets which are very similar and fall under the time window might suffer from this approach
    # At the end, there is a gap of 2M packets between Lanvin and Liu packets. By gap, we mean the difference in nbr of packets removed.
    echo "Running Liu dedup..."

    # --------- Code from Lisa Liu w/ iteration loop fixed
    temp_folder_dedup=$OUTPUT_FOLDER/TempDeduplicated
    temp_folder_orig=$OUTPUT_FOLDER/TempOriginal
    mkdir -p $temp_folder_dedup
    mkdir -p $temp_folder_orig

    # MAC addresses characterisation:     
    # 00:c1:b1:14:eb:31 CISCO router, appears in 80% of the L2 source field because overwrites it when routing the packets
    # 01:00:0c:cc:cc:cc, 01:00:5e:00:00:16, 01:80:c2:00:00:0e: never appear in the traffic
    # 24:6e:96:4a:37:7a : used for communications with scanners/printers, LLMNR requests and stuff
    mac_list=("00:c1:b1:14:eb:31" "01:00:0c:cc:cc:cc" "01:00:5e:00:00:16" "24:6e:96:4a:37:7a" "01:80:c2:00:00:0e")
    mac_filter_no="not ("

    for i in "${mac_list[@]}"; do
        mac_filter_no+="ether src $i or "
    done
    
    # IP characterisation
    # 224.0.0.0/4 : IPv4 multicast network
    # 192.168.0.0/16 : Victim network (extended, /24 would have been sufficient to cover it but let's keep it as a catch-all CIDR)
    mac_filter_no=${mac_filter_no::-4} # delete the last " && "
    mac_filter_no+=") and (ether dst ff:ff:ff:ff:ff:ff or ((src net 192.168.0.0/16 or src net 224.0.0.0/4) and (dst net 192.168.0.0/16 or dst net 224.0.0.0/4)))"
    mac_filter_yes="not (${mac_filter_no})"

    for pcap in $(find $INPUT_FOLDER -type f -iname "*.pcap" -printf "%f\n"); do
    # Filter by MAC address and place resultant pcap files in the temp folders
        tcpdump -r "$INPUT_FOLDER/$pcap" -w ${temp_folder_orig}/$pcap -s 0 "${mac_filter_yes}"
        tcpdump -r "$INPUT_FOLDER/$pcap" -w ${temp_folder_dedup}/$pcap -s 0 "${mac_filter_no}"
        # Remove duplicated traffic with editcap in dedup folder
        editcap -w $DEDUP_THRESHOLD ${temp_folder_dedup}/$pcap ${temp_folder_dedup}/temp_$pcap

        # Merge de-duplicated and original pcaps and move to main output folder
        mergecap -w $OUTPUT_FOLDER/$pcap ${temp_folder_dedup}/temp_$pcap ${temp_folder_orig}/$pcap
    done

    rm -rf $temp_folder_dedup
    rm -rf $temp_folder_orig
    ;;
esac