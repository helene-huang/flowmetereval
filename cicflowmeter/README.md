# How to run a specific version of CICFlowmeter
From the current directory (/cicflowmeter), run the following commands to
## Build the docker image of CICFlowmeter
```sh
make build CONFIG=path/to/file.mk
```
## Run the docker image to extract CSV from PCAPs
```sh
make run CONFIG=path/to/file.mk
```
## Content of the file.mk
The file.mk contains the required information used by the Makefile. It includes:
* IMAGE_NAME: docker image name, used for build and run scripts
* PATH_TO_CIC: relative path to the Dockerfile of the targeted CICFlowmeter version (always consider this directory as the root)
* PATH_TO_PCAP: relative path to the PCAPs folder (always consider this directory as the root)
* PATH_TO_CSV: relative path to the output folder where the CSVs shall be stored (always consider this directory as the root)
* JVM_OPTIONS: used to configure variables such as MAX_HEAP_SIZE, MEMORY ROTATION, etc.