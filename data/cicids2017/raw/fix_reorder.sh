#!/usr/bin/env bash
# install dependencies (note: reordercap is included in wireshark): 
#    sudo apt install pcapfix wireshark
# 
# usage: 
#    chmod +x fix_reorder.sh
#    ./fix_reorder.sh /path/to/pcap/folder

# @author: Hélène Huang

set -euo pipefail


PCAP_DIR="${1:?Usage: $0 /path/to/pcap/folder}"

# verify required tools are available
for tool in pcapfix reordercap; do
    command -v "$tool" &>/dev/null || { echo "ERROR: '$tool' not found in PATH"; exit 1; }
done

# find all .pcap and .pcapng files (non-recursive)
mapfile -t PCAP_FILES < <(find "$PCAP_DIR" -maxdepth 1 -type f \( -iname "*.pcap" -o -iname "*.pcapng" \))

[[ ${#PCAP_FILES[@]} -eq 0 ]] && { echo "No pcap files found in: $PCAP_DIR"; exit 1; }

echo "Found ${#PCAP_FILES[@]} file(s) to process in: $PCAP_DIR"

for PCAP in "${PCAP_FILES[@]}"; do
    echo ""
    echo "==> Processing: $(basename "$PCAP")"

    TMP1="${PCAP}.fixed"
    TMP2="${PCAP}.reordered"

    # step 1: pcapfix
    echo "    [1/2] pcapfix..."
    if ! pcapfix -o "$TMP1" "$PCAP"; then
        echo "    WARNING: pcapfix failed, using original file"
    fi

    # if pcapfix produced no output, fall back to original
    if [[ ! -s "$TMP1" ]]; then
        cp "$PCAP" "$TMP1"
    fi

    # step 2: reordercap
    echo "    [2/2] reordercap..."
    if ! reordercap "$TMP1" "$TMP2"; then
        echo "    ERROR: reordercap failed, skipping file"
        rm -f "$TMP1" "$TMP2"
        continue
    fi

    # replace original only if result is valid
    if [[ -s "$TMP2" ]]; then
        mv -f "$TMP2" "$PCAP"
        echo "    Done."
    else
        echo "    ERROR: output file is empty, original not overwritten"
    fi

    #cleanup
    rm -f "$TMP1"
done

echo ""
echo "All files processed successfully."
