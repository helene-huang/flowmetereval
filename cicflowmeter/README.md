# Extract flow data with CICFlowMeter

This directory contains two CICFlowMeter implementations as Git submodules:

- `engelen/CICFlowMeter`: the latest Engelen implementation (ref. Liu, Engelen et al.)
- `hhuang/CICFlowMeter`: the Huang et al. implementation with the feature fixes

## Requirements

- Docker with access to the Docker daemon
- `reordercap` and `capinfos`, provided by Wireshark
- Enough free disk space for the source capture and an ordered copy
- Enough memory for the selected dataset and JVM configuration

On Ubuntu, the capture tools can be installed with:

```sh
sudo apt install wireshark-common
```

`pcapfix` is optional. It is useful when a checksum fails or Wireshark cannot
parse a capture. A capture that matches its supplied checksum and is read fully
by `reordercap` does not normally need to be repaired.

Install it separately if a damaged capture requires repair:

```sh
sudo apt install pcapfix
```

Reordering requires enough space for another copy of each capture. Repairing
with `pcapfix` can temporarily require one more full copy. The checked-in
CIC-IDS 2017 configurations allocate an 8 GB JVM heap; the InSDN configurations
allocate up to 40 GB and therefore require a machine sized accordingly.

## Extract flow data from PCAP files

### 1. Fix and reorder packets by timestamp

Use `data/cicids2017/raw/fix_reorder.sh` and `data/insdn/utils/fix_reorder.sh` to apply the necessary fixes to the datasets.
They process every PCAP in a directory and replace each source file in place, so use them only on a working-copy directory
containing complete captures.

### 2. Set the paths

The repository provides these implementation and dataset combinations:

| Implementation | Dataset | Configuration |
| --- | --- | --- |
| Engelen | CIC-IDS 2017 | `engelen/configs/cicids2017.mk` |
| Engelen | InSDN | `engelen/configs/insdn.mk` |
| Huang | CIC-IDS 2017 | `hhuang/configs/cicids2017.mk` |
| Huang | InSDN | `hhuang/configs/insdn.mk` |

A configuration file looks like this:
```sh
IMAGE_NAME=hhuang/cicflowmeter
PATH_TO_CIC=hhuang/CICFlowmeter
PATH_TO_PCAP=../data/cicids2017/raw/out
PATH_TO_CSV=../data/cicids2017/hhuang_fix/unlabeled
JVM_OPTIONS="-Xmx8g"
```

Change `PATH_TO_PCAP` to the directory where your reordered and fixed PCAP files are stored.

#### Notes about CIC-IDS 2017

The official filenames are case-sensitive. In particular, note that Wednesday uses a lowercase `w` in `workingHours`.

The five names expected by the labeling script are:

```text
Monday-WorkingHours.pcap
Tuesday-WorkingHours.pcap
Wednesday-workingHours.pcap
Thursday-WorkingHours.pcap
Friday-WorkingHours.pcap
```

### 3. Verify the selected pinned submodule and build the image

Initialize the submodule if necessary:

```sh
git submodule update --init --recursive
git submodule status
```

Expected output:

```
 4dd5319ad36457010d7a406505790b17a5828108 cicflowmeter/engelen/CICFlowmeter (heads/master)
 59fe2917ee3f649a8ac7d11f4d4af985f9f3c095 cicflowmeter/hhuang/CICFlowmeter (heads/fix/packet-segment-lengths)
```


Build and tag the image with the exact source revision:

```sh
make build CONFIG=hhuang/configs/cicids2017.mk
make build CONFIG=engelen/configs/cicids2017.mk
```

Confirm that the resulting image records the expected revision:

```sh
make validate CONFIG=hhuang/configs/cicids2017.mk
make validate CONFIG=engelen/configs/cicids2017.mk
```

Expected output:
```
sha256:0d5170c8b8abede941c32877c24229333d1065a25c68c547b401564a313ca318
sha256:6222c5fbf479fc9b8dbbc669c7ebc74c0173ffe37d310d2ec242f28d2f70eb1f
```

### 4. Run CICFlowmeter

Use the same configuration selected when building the image.

#### Extract multiple PCAPs

Place all ordered captures in `PATH_TO_PCAP` from the selected configuration,
then run:

```sh
make run CONFIG=hhuang/configs/cicids2017.mk
```

The `run` target reads every PCAP from `PATH_TO_PCAP`, applies the JVM options
from the configuration, and moves the generated CSV files to `PATH_TO_CSV`.
Both paths are defined in the selected configuration file.

Override the configured input directory if needed:

```sh
make run \
    CONFIG=hhuang/configs/cicids2017.mk \
    PATH_TO_PCAP=/path/to/ordered/pcaps
```

#### Extract a single PCAP

Place the capture in a directory by itself and override `PATH_TO_PCAP`:

```sh
make run \
    CONFIG=hhuang/configs/cicids2017.mk \
    PATH_TO_PCAP=/path/to/single/ordered/pcap
```

The commands run in the foreground, and the temporary container is removed
automatically when extraction finishes.

### 5. Fix output ownership

Docker may create the CSV files as `root`. If necessary, change the ownership of
the configured output directory after extraction:

```sh
sudo chown -R "$(id -u):$(id -g)" /path/to/output/csv
```

### 6. Check the output

A successful run prints `is done`, the packet statistics, and `Completed!`
before returning. The generated files are located in `PATH_TO_CSV` from the
selected configuration.

Basic checks are usually sufficient:

```sh
ls -lh /path/to/output/csv
head -n 1 /path/to/output/csv/example.pcap_Flow.csv
wc -l /path/to/output/csv/example.pcap_Flow.csv
```

The expected columns depend on the selected CICFlowmeter implementation and
revision.

## Troubleshooting

- If CICFlowmeter reports disordered packets, stop the run, remove the partial
  CSV, reorder the source capture, and run the extraction again.
- If the run is interrupted or fails, a partial CSV may remain in
  `PATH_TO_PCAP` because the Makefile moves files only after Docker succeeds.
- If Docker exits with code 137, check the available memory and `JVM_OPTIONS`
  in the selected configuration.
- If the image or output schema is unexpected, run `make validate` with the
  same `CONFIG`; rebuild that configuration if the image ID is not the expected
  one.
- If Docker cannot access `/var/run/docker.sock`, configure Docker access for
  the current user before retrying.
