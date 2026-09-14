# Raw PCAP files

This is the default directory for storing raw PCAP files of the CIC-IDS 2017 dataset. The files can be downloaded from the [CIC website](https://cicresearch.ca/CICDataset/CIC-IDS-2017/).

## Requirements

```sh
apt install pcapfix wireshark tcpdump
```

The `wireshark` package provides `reordercap`, `editcap`, and `mergecap`.

## Fix and reorder the PCAP files

To reproduce the results of the paper, keep duplicate packets by using `--no-dedup`. From the repository root, run:

```bash
cd data/cicids2017/raw
sh ./deduplicate.sh --no-dedup /path/to/pcaps /path/to/pcaps
```
or, equivalently, just
```bash
cd data/cicids2017/raw
sh ./fix_reorder.sh /path/to/pcaps
```

By default, `fix_reorder.sh` replaces the input files. To keep the originals, provide an output directory:

```bash
sh ./fix_reorder.sh /path/to/pcaps /path/to/reordered-pcaps
```

## Reordered file checksums

```
36ad129a083d9db424cbd3b2a7c345fa  Monday-WorkingHours.pcap
435403f09ddb08a4355905517a8323ee  Tuesday-WorkingHours.pcap
eed9c22b766ece94d338eaf68d6d0375  Wednesday-workingHours.pcap
2e78f30bae5402882285f58ea0bbb25e  Thursday-WorkingHours.pcap
e02b8878c6d960a5b2594e7c3e43bfa0  Friday-WorkingHours.pcap
```

## Other deduplication options

`deduplicate.sh` also implements the [Lanvin](https://github.com/GintsEngelen/CNS2022_Code/pull/1) and [Liu](https://github.com/GintsEngelen/CNS2022_Code/pull/4) approaches:

```bash
sh ./deduplicate.sh [--no-fix-reorder] [--no-dedup|--lanvin-dedup|--liu-dedup] input_directory output_directory
```

Use `--no-fix-reorder` only when the input files have already been fixed and reordered.
