IMAGE_NAME=engelen/cicflowmeter
PATH_TO_CIC=engelen/CICFlowmeter
PATH_TO_PCAP=../data/insdn/raw
PATH_TO_CSV=../data/insdn/engelen_latest/unlabeled
JVM_OPTIONS="-Xmx40g -Xms16g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -verbose:gc"