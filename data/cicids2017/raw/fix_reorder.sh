#!/usr/bin/env bash
# install dependencies (note: reordercap is included in wireshark): 
#    sudo apt install pcapfix wireshark
# 
# usage: 
#    chmod +x fix_reorder.sh
#    ./fix_reorder.sh /path/to/pcap/folder [/path/to/output/folder]

# @author: Hélène Huang

set -euo pipefail


PCAP_DIR="${1:?Usage: $0 /path/to/pcap/folder [/path/to/output/folder]}"
OUTPUT_DIR="${2:-}"

if [[ $# -gt 2 ]]; then
    echo "Usage: $0 /path/to/pcap/folder [/path/to/output/folder]"
    exit 1
fi

if [[ -n "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR"
fi

# verify required tools are available
for tool in pcapfix reordercap; do
    command -v "$tool" &>/dev/null || { echo "ERROR: '$tool' not found in PATH"; exit 1; }
done

# find all .pcap and .pcapng files (non-recursive)
PCAP_FILES=()
while IFS= read -r -d '' PCAP; do
    PCAP_FILES+=("$PCAP")
done < <(find "$PCAP_DIR" -maxdepth 1 -type f \( -iname "*.pcap" -o -iname "*.pcapng" \) -print0)

[[ ${#PCAP_FILES[@]} -eq 0 ]] && { echo "No pcap files found in: $PCAP_DIR"; exit 1; }

echo "Found ${#PCAP_FILES[@]} file(s) to process in: $PCAP_DIR"

for PCAP in "${PCAP_FILES[@]}"; do
    echo ""
    echo "==> Processing: $(basename "$PCAP")"

    OUTPUT_PCAP="$PCAP"
    if [[ -n "$OUTPUT_DIR" ]]; then
        OUTPUT_PCAP="$OUTPUT_DIR/$(basename "$PCAP")"
    fi

    TMP1="${OUTPUT_PCAP}.fixed"
    TMP2="${OUTPUT_PCAP}.reordered"

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

    # replace the destination only if the result is valid
    if [[ -s "$TMP2" ]]; then
        mv -f "$TMP2" "$OUTPUT_PCAP"
        echo "    Done: $OUTPUT_PCAP"
    else
        echo "    ERROR: output file is empty, destination not overwritten"
    fi

    #cleanup
    rm -f "$TMP1"
done

echo ""
echo "All files processed successfully."
