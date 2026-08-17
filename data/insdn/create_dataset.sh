#/bin/sh

PROFILE=$1
. $PROFILE

# Transforms PCAPNG into PCAP
mapfile -t PCAPNG_FILES < <(find . -type f -iname "*.pcapng")
mapfile -t PCAP_FILES   < <(find . -type f -iname "*.pcap")

for src in "${PCAP_FILES[@]}"; do
  mv "$src" "./raw/$(basename "$src")"
done


for src in "${PCAPNG_FILES[@]}"; do
  dst="./raw/$(basename "${src%.*}").pcap"
  editcap -F pcap "$src" "$dst"
done

# Transform PCAPs into atomic CSVs
echo "Start by fixing corrupted PCAPs and reorder them"
./utils/fix_reorder.sh raw/
cd ../../cicflowmeter
echo "Build CICFlowmeter image"
make build CONFIG=$CIC_CONF
echo "Extract flow features from PCAP files"
make run CONFIG=$CIC_CONF

cd ../data/insdn/
echo "Arrange CSVs into appropriate folders for later processing"
uv run -m utils.arrange  $DATA_DIR/unlabeled $DATA_DIR/unlabeled

# Create InSDN CSVs
mkdir -p "$DATA_DIR/labeled"
echo "Put labels on metasploitable flows"
uv run -m utils.labelize $DATA_DIR/unlabeled/metasploitable-2/ $DATA_DIR/labeled/metasploitable-2/
echo "Put labels on OVS flows"
uv run -m utils.labelize $DATA_DIR/unlabeled/OVS/ $DATA_DIR/labeled/OVS/
echo "Put labels on Normal flows"
uv run -m utils.labelize $DATA_DIR/unlabeled/Normal/ $DATA_DIR/labeled/Normal/

mkdir -p "$DATA_DIR/final"
echo "Merge datasets into three CSVs"
uv run -m utils.merge_csvs $DATA_DIR/labeled/metasploitable-2/ $DATA_DIR/final/metasploitable-2.csv
uv run -m utils.merge_csvs $DATA_DIR/labeled/OVS/ $DATA_DIR/final/OVS.csv
uv run -m utils.merge_csvs $DATA_DIR/labeled/Normal/ $DATA_DIR/final/Normal.csv

# Merge into one CSV
echo "Merge datasets into single CSV"
uv run -m utils.merge_csvs $DATA_DIR/final/ $DATA_DIR/final/insdn.csv