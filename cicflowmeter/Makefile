CONFIG ?= hhuang/config/cicids2017.mk
include $(CONFIG)

build:
	docker build -t $(IMAGE_NAME) $(PATH_TO_CIC)

run:
	# NOTE: Override the path to the pcap files if needed
	# `make run PATH_TO_PCAP=/path/to/pcap/files`
	docker run -e JAVA_TOOL_OPTIONS=$(JVM_OPTIONS) --rm -v $(PATH_TO_PCAP):/tmp/pcap $(IMAGE_NAME):latest /tmp/pcap/ /tmp/pcap/
	mkdir -p $(PATH_TO_CSV)
	mv $(PATH_TO_PCAP)/*.csv $(PATH_TO_CSV)
