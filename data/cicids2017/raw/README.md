# RAW PCAP files

This is the default directory for storing raw PCAP files of the CIC-IDS 2017 dataset. The raw PCAP files can be downloaded from the CIC website: [link](https://cicresearch.ca/CICDataset/CIC-IDS-2017/)

## Scripts

### Requirements

```bash
sudo apt install pcapfix wireshark tcpdump
```

With the previous version using `tshark`, it was recommanded to run `--liu-dedup` with 15GB of memory available.
Using `tcpdump`, it only requires 4GB.

### fix_reorder.sh
This script calls `pcapfix` and `reorderpcap` to
* repair damaged .pcap and .pcapng files
* reorder by ascending timestamps the packets of the captures

### deduplicate.sh
Calls `fix_reorder.sh` and provides two packet deduplication approaches:
* the one from [Lanvin](https://github.com/GintsEngelen/CNS2022_Code/pull/1)
* the one from [Liu](https://github.com/GintsEngelen/CNS2022_Code/pull/4)

Those can be executed using the following syntax:
```bash
./deduplicate.sh [--no-fix-reorder] [--no-dedup|--lanvin-dedup|--liu-dedup] input_file output_file
```

By default, --no-dedup is choosen and the script `fix_reorder.sh` is called. To bypass this script, the flag `--no-fix-reorder` can be set.