#!/usr/bin/env bash
# Recon for an unknown networked robot (Challenge 06). Only run against devices you are allowed to test
# (the hackathon provides the Plato robots for exactly this).   usage: ./recon.sh <robot-ip>
set -u
IP="${1:?usage: recon.sh <ip>}"
OUT="recon_$IP"; mkdir -p "$OUT"
echo "== ping";       ping -c 2 -W 1 "$IP" | tail -2
echo "== top ports";  nmap -Pn -T4 --top-ports 1000 "$IP" -oN "$OUT/nmap_top.txt" | grep -E "open|filtered" || true
echo "== all ports (background-worthy)"; nmap -Pn -T4 -p- "$IP" -oN "$OUT/nmap_all.txt" | grep open || true
echo "== service versions on open ports"
PORTS=$(grep -oE '^[0-9]+/tcp +open' "$OUT"/nmap_*.txt | cut -d/ -f1 | sort -un | paste -sd,)
[ -n "$PORTS" ] && nmap -Pn -sV -p "$PORTS" "$IP" -oN "$OUT/nmap_sv.txt" | grep -E "open" || echo "no open tcp ports found"
echo "== http probes"
for p in 80 8080 8000 5000 3000 9090; do
  curl -s -m 2 -o /dev/null -w "port $p -> HTTP %{http_code}\n" "http://$IP:$p/" 2>/dev/null | grep -v "000" || true
done
echo "Results in $OUT/. Next: open web UIs in a browser, 'adb connect $IP:5555', 'ssh user@$IP', capture traffic with wireshark/tcpdump while using the vendor app."
