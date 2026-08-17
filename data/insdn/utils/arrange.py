from pathlib import Path
from argparse import ArgumentParser
import shutil

OVS_FILES : list[str] = [
    "docker_brute-force-attack-brup-suite.pcap_Flow.csv",
    "docker_brute-force-attack-hydra.pcap_Flow.csv",
    "docker-interface_Probe.pcap_Flow.csv",
    "Docker-Interface_reverse-shell.pcap_Flow.csv",
    "Docker-Interface_SQL-Injection.pcap_Flow.csv",
    "Docker_interface-XSS_Burp.pcap_Flow.csv",
    "h4-DDoS-ICMP.pcap_Flow.csv",
    "h4-DDoS-SYN.pcap_Flow.csv",
    "h4-DDoS-UDP.pcap_Flow.csv",
    "h4_DoS_hulk.pcap_Flow.csv",
    "h4_DoS-Slowloris_Apache killer.pcap_Flow.csv",
    "h4_DoS-Slowloris.pcap_Flow.csv",
    "h4_DoS-Slowloris_R-U-Dead-Yet or Rudy.pcap_Flow.csv",
    "h4_DoS-Slowloris_Slow Read.pcap_Flow.csv",
    "h4_DoS_TorshHummer.pcap_Flow.csv",
    "h4-HTTP-flood.pcap_Flow.csv",
    "h4-TCP-flood.pcap_Flow.csv",
    "h4-UDP-flood.pcap_Flow.csv",
    "ONOS_Botnet.pcap_Flow.csv",
    "ONOS_brute-force-attack-brup-suite.pcap_Flow.csv",
    "ONOS_brute-force-attack-hydra.pcap_Flow.csv",
    "ONOS-DDoS-ICMP.pcap_Flow.csv",
    "ONOS-DDoS-SYN.pcap_Flow.csv",
    "ONOS-DDoS-UDP.pcap_Flow.csv",
    "ONOS_Dos-hulk.pcap_Flow.csv",
    "ONOS-HTTP-flood.pcap_Flow.csv",
    "ONOS-interface_XSS_Burp.pcap_Flow.csv",
    "ONOS_Probe-Docker.pcap_Flow.csv",
    "ONOS_Probe-Vhosts.pcap_Flow.csv",
    "ONOS_reverse-shell.pcap_Flow.csv",
    "ONOS_Slowloris_Apache killer.pcap_Flow.csv",
    "ONOS_Slowloris.pcap_Flow.csv",
    "ONOS_Slowloris_R-U-Dead-Yet or Rudy.pcap_Flow.csv",
    "ONOS_Slowloris_Slow Read.pcap_Flow.csv",
    "ONOS_SQL-Injection.pcap_Flow.csv",
    "ONOS-TCP-flood.pcap_Flow.csv",
    "ONOS_torshhummer.pcap_Flow.csv",
    "ONOS-UDP-flood.pcap_Flow.csv",
    "S1_Botnet.pcap_Flow.csv",
    "S1_interface-Probe.pcap_Flow.csv",
]

NORMAL_FILE_PATTERN : str = 'Normal*.csv'

METASPLOITABLE2_FILES : list[str] = [
    "metasploitable2-BRF_telnet.pcap_Flow.csv",
    "metasploitable2-BRF_tomcat_apache.pcap_Flow.csv",
    "metasploitable-2_ddos-icmp.pcap_Flow.csv",
    "metasploitable-2_ddos-SYN.pcap_Flow.csv",
    "metasploitable-2_ddos-UDP.pcap_Flow.csv",
    "metasploitable-2_distcc-exploit.pcap_Flow.csv",
    "metasploitable-2_dos-slowloris.pcap_Flow.csv",
    "metasploitable-2_dos_syn.pcap_Flow.csv",
    "metasploitable-2-irc_exploit.pcap_Flow.csv",
    "metasploitable-2_probe_msf__scan.pcap_Flow.csv",
    "metasploitable2_probe_wmap_scan.pcap_Flow.csv",
    "metasploitable-2_samba_exploit.pcap_Flow.csv",
    "metasploitable2-VSFTPD_exploit.pcap_Flow.csv",
    "ONOS_BRF_telnet.pcap_Flow.csv",
    "ONOS_-BRF_tomcat_apache.pcap_Flow.csv",
    "ONOS_DDoS_ICMP.pcap_Flow.csv",
    "ONOS_DDoS_SYN.pcap_Flow.csv",
    "ONOS_DDoS_TCP.pcap_Flow.csv",
    "ONOS_distcc_exploit.pcap_Flow.csv",
    "ONOS_DoS_slowloris.pcap_Flow.csv",
    "ONOS_DoS-SYN.pcap_Flow.csv",
    "ONOS_irc_exploit.pcap_Flow.csv",
    "ONOS__probe_msf__scan.pcap_Flow.csv",
    "ONOS_samba_exploit.pcap_Flow.csv",
    "ONOS_Scan_probe_wmap_scan.pcap_Flow.csv",
    "ONOS_VSFTPD_exploit.pcap_Flow.csv",
]

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('input_folder')
    parser.add_argument('output_folder')
    args = parser.parse_args()
    input_folder = Path(args.input_folder)
    output_folder = Path(args.output_folder)

    Ovs : Path = output_folder / 'OVS'
    Normal : Path = output_folder / 'Normal'
    Metasploitable : Path = output_folder / 'metasploitable-2'
    Ovs.mkdir(parents=True, exist_ok=True)
    Normal.mkdir(parents=True, exist_ok=True)
    Metasploitable.mkdir(parents=True, exist_ok=True)

    for f in input_folder.rglob(NORMAL_FILE_PATTERN):
        shutil.move(str(f), str(Normal / f.name))

    for f in OVS_FILES:
        src : Path = input_folder / f
        if src.exists():
            shutil.move(str(src), str(Ovs/f))
        else:
            print(f'File not found: {f}')

    for f in METASPLOITABLE2_FILES:
        src : Path = input_folder / f
        if src.exists():
            shutil.move(str(src), str(Metasploitable/f))
        else:
            print(f'File not found: {f}')

