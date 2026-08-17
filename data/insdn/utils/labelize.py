import pandas as pd
import polars as pl
from argparse import ArgumentParser
from pathlib import Path

file_label : dict[str, str] = {
    'metasploitable2-BRF_telnet.pcap_Flow.csv' : 'BFA',
    'metasploitable2-BRF_tomcat_apache.pcap_Flow.csv' : 'BFA',
    'metasploitable2_probe_wmap_scan.pcap_Flow.csv' : 'Probe',
    'metasploitable2-VSFTPD_exploit.pcap_Flow.csv' : 'U2R',
    'metasploitable-2_ddos-icmp.pcap_Flow.csv' : 'DDoS',
    'metasploitable-2_ddos-SYN.pcap_Flow.csv' : 'DDoS',
    'metasploitable-2_ddos-UDP.pcap_Flow.csv' : 'DDoS',
    'metasploitable-2_distcc-exploit.pcap_Flow.csv' : 'U2R',
    'metasploitable-2_dos-slowloris.pcap_Flow.csv' : 'DoS',
    'metasploitable-2_dos_syn.pcap_Flow.csv' : 'DoS',
    'metasploitable-2-irc_exploit.pcap_Flow.csv' : 'U2R',
    'metasploitable-2_probe_msf__scan.pcap_Flow.csv' : 'Probe',
    'metasploitable-2_samba_exploit.pcap_Flow.csv' : 'U2R',
    'ONOS_BRF_telnet.pcap_Flow.csv' : 'BFA',
    'ONOS_-BRF_tomcat_apache.pcap_Flow.csv' : 'BFA',
    'ONOS_DDoS_ICMP.pcap_Flow.csv' : 'DDoS',
    'ONOS_DDoS_SYN.pcap_Flow.csv' : 'DDoS',
    'ONOS_DDoS_TCP.pcap_Flow.csv' : 'DDoS',
    'ONOS_distcc_exploit.pcap_Flow.csv' : 'U2R',
    'ONOS_DoS_slowloris.pcap_Flow.csv' : 'DoS',
    'ONOS_DoS-SYN.pcap_Flow.csv' : 'DoS',
    'ONOS_irc_exploit.pcap_Flow.csv' : 'U2R',
    'ONOS__probe_msf__scan.pcap_Flow.csv' : 'Probe',
    'ONOS_samba_exploit.pcap_Flow.csv' : 'U2R',
    'ONOS_Scan_probe_wmap_scan.pcap_Flow.csv' : 'Probe',
    'ONOS_VSFTPD_exploit.pcap_Flow.csv' : 'U2R',
    'Normal-h3_1.pcap_Flow.csv' : 'Normal',
    'Normal-h3_2.pcap_Flow.csv' : 'Normal',
    'Normal-h3_3.pcap_Flow.csv' : 'Normal',
    'Normal-h3_4.pcap_Flow.csv' : 'Normal',
    'Normal-h3_5.pcap_Flow.csv' : 'Normal',
    'Normal-h3_6.pcap_Flow.csv' : 'Normal',
    'Normal-h3_8.pcap_Flow.csv' : 'Normal',
    'Normal-h3_9.pcap_Flow.csv' : 'Normal',
    'Normal-h3_10.pcap_Flow.csv' : 'Normal',
    'Normal-h3_11.pcap_Flow.csv' : 'Normal',
    'Normal-h3_12.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_1.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_2.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_3.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_4.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_5.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_6.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_8.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_9.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_11.pcap_Flow.csv' : 'Normal',
    'Normal-ONOS_12.pcap_Flow.csv' : 'Normal',
    'Normal_ONOS.gz_10.pcap_Flow.csv' : 'Normal',
    'docker_brute-force-attack-brup-suite.pcap_Flow.csv' : 'BFA',
    'docker_brute-force-attack-hydra.pcap_Flow.csv' : 'BFA',
    'docker-interface_Probe.pcap_Flow.csv' : 'Probe',
    'Docker-Interface_reverse-shell.pcap_Flow.csv' : 'Web-attacks',
    'Docker-Interface_SQL-Injection.pcap_Flow.csv' : 'Web-attacks',
    'Docker_interface-XSS_Burp.pcap_Flow.csv' : 'Web-attacks',
    'h4-DDoS-ICMP.pcap_Flow.csv' : 'DDoS',
    'h4-DDoS-SYN.pcap_Flow.csv' : 'DDoS',
    'h4-DDoS-UDP.pcap_Flow.csv' : 'DDoS',
    'h4_DoS_hulk.pcap_Flow.csv' : 'DoS',
    'h4_DoS-Slowloris.pcap_Flow.csv' : 'DoS',
    'h4_DoS-Slowloris_Apache killer.pcap_Flow.csv' : 'DoS',
    'h4_DoS-Slowloris_R-U-Dead-Yet or Rudy.pcap_Flow.csv' : 'DoS',
    'h4_DoS-Slowloris_Slow Read.pcap_Flow.csv' : 'DoS',
    'h4_DoS_TorshHummer.pcap_Flow.csv' : 'DoS',
    'h4-HTTP-flood.pcap_Flow.csv' : 'DoS',
    'h4-TCP-flood.pcap_Flow.csv' : 'DoS',
    'h4-UDP-flood.pcap_Flow.csv' : 'DoS',
    'ONOS_Botnet.pcap_Flow.csv' : 'Botnet',
    'ONOS_brute-force-attack-brup-suite.pcap_Flow.csv' : 'BFA',
    'ONOS_brute-force-attack-hydra.pcap_Flow.csv' : 'BFA',
    'ONOS-DDoS-ICMP.pcap_Flow.csv' : 'DDoS',
    'ONOS-DDoS-SYN.pcap_Flow.csv': 'DDoS',
    'ONOS-DDoS-UDP.pcap_Flow.csv' : 'DDoS',
    'ONOS_Dos-hulk.pcap_Flow.csv' : 'DoS',
    'ONOS-HTTP-flood.pcap_Flow.csv' : 'DoS',
    'ONOS-interface_XSS_Burp.pcap_Flow.csv' : 'Web-attacks',
    'ONOS_Probe-Docker.pcap_Flow.csv' : 'Probe',
    'ONOS_Probe-Vhosts.pcap_Flow.csv' : 'Probe',
    'ONOS_reverse-shell.pcap_Flow.csv' : 'Web-attacks',
    'ONOS_Slowloris.pcap_Flow.csv' : 'DoS',
    'ONOS_Slowloris_Apache killer.pcap_Flow.csv' : 'DoS',
    'ONOS_Slowloris_R-U-Dead-Yet or Rudy.pcap_Flow.csv' : 'DoS',
    'ONOS_Slowloris_Slow Read.pcap_Flow.csv' : 'DoS',
    'ONOS_SQL-Injection.pcap_Flow.csv' : 'Web-attacks',
    'ONOS-TCP-flood.pcap_Flow.csv' : 'DoS',
    'ONOS_torshhummer.pcap_Flow.csv' : 'DoS',
    'ONOS-UDP-flood.pcap_Flow.csv' : 'DoS',
    'S1_Botnet.pcap_Flow.csv' : 'Botnet',
    'S1_interface-Probe.pcap_Flow.csv' : 'Probe',
}

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('input_folder')
    parser.add_argument('output_folder')
    
    args = parser.parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    csv_files = list(Path(input_folder).rglob('*.csv'))
    for f in csv_files:
        if f.name not in file_label:
            print(f"The file {f.name} does not appear in the label maps. Passing to next file")
            continue
        df = pl.read_csv(f, infer_schema_length=10000000000)
        df = df.with_columns(
            pl.lit(file_label[f.name]).alias('Label')
        )
        # print(f'{output_folder}{f.name}')
        df.write_csv(f'{output_folder}{f.name}')