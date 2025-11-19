#!/usr/bin/env bash
# LAN Topology Mapper (Proxmox-safe + heuristic depth/tree)

set -e

echo "=== LAN Mapper Starting ==="
echo

### ====================================================================================
### DETECT REAL LAN INTERFACE (PROXMOX-FRIENDLY)
### ====================================================================================

# Get all interfaces with IPv4, exclude unwanted virtual/tunnel interfaces
VALID_IFACES=$(ip -o -4 addr show \
    | awk '{print $2}' \
    | grep -Ev '^(lo|tailscale0|wg[0-9]|veth|fwbr|fwpr|fwln|docker[0-9]*)' \
    | sort -u)

# Prefer vmbr interfaces (Proxmox bridges)
if echo "$VALID_IFACES" | grep -q "^vmbr"; then
    LAN_IFACE=$(echo "$VALID_IFACES" | grep "^vmbr" | head -1)
else
    LAN_IFACE=$(echo "$VALID_IFACES" | head -1)
fi

if [[ -z "$LAN_IFACE" ]]; then
    echo "❌ ERROR: No valid LAN interface found."
    exit 1
fi

SUBNET=$(ip -4 addr show "$LAN_IFACE" | grep -oP '(?<=inet\s)\d+\.\d+\.\d+\.\d+/\d+')

if [[ -z "$SUBNET" ]]; then
    echo "❌ ERROR: Interface $LAN_IFACE has no IPv4 assigned."
    exit 1
fi

GATEWAY=$(ip route | grep "^default" | awk '{print $3}')

echo "🔎 Using LAN interface: $LAN_IFACE"
echo "🔎 Subnet: $SUBNET"
echo "🌐 Gateway: $GATEWAY"
echo


### ====================================================================================
### REQUIREMENTS CHECK
### ====================================================================================

for cmd in arp-scan nmap snmpwalk lldpctl dig avahi-resolve-address; do
    if ! command -v $cmd &>/dev/null; then
        echo "❌ Missing: $cmd"
        echo "Install with: sudo apt install -y arp-scan nmap snmp snmp-mibs-downloader lldpd dnsutils avahi-utils"
        exit 1
    fi
done

TEMP_DIR="./lanmap_tmp"
mkdir -p "$TEMP_DIR"


### ====================================================================================
### 1. ARP SCAN
### ====================================================================================

echo "📡 Waking up devices (ping sweep)..."
# Quick ping sweep to populate ARP table and wake devices
fping -a -g "$SUBNET" -r 1 -t 50 >/dev/null 2>&1 || true

echo "📡 Running ARP scan on $LAN_IFACE..."
arp-scan --interface="$LAN_IFACE" --localnet --retry=2 > "$TEMP_DIR/arp.txt"
echo "✔ ARP scan complete."
echo


### ====================================================================================
### 2. NMAP HOST DISCOVERY
### ====================================================================================

echo "📡 Running Nmap ping sweep..."
nmap -sn "$SUBNET" -oG "$TEMP_DIR/nmap.txt" >/dev/null
echo "✔ Nmap scan complete."
echo


### ====================================================================================
### 3. HOSTNAME COLLECTION (DNS + mDNS)
### ====================================================================================

echo "🔤 Collecting hostnames (DNS + mDNS)..."

> "$TEMP_DIR/hosts.txt"

grep "Status: Up" "$TEMP_DIR/nmap.txt" | awk '{print $2}' | while read IP; do
    HOST=$(dig -x $IP +short 2>/dev/null | sed 's/\.$//')

    if [[ -z "$HOST" ]]; then
        HOST=$(avahi-resolve-address "$IP" 2>/dev/null | awk '{print $2}' | sed 's/\.$//')
    fi

    if [[ -z "$HOST" ]]; then
        # Try NetBIOS lookup (Samba)
        HOST=$(nmblookup -A "$IP" 2>/dev/null | grep -v "Looking up" | grep "<00>" | head -1 | awk '{print $1}')
    fi

    echo "$IP | ${HOST:-Unknown}" >> "$TEMP_DIR/hosts.txt"
done

echo "✔ Hostname collection complete."
echo


### ====================================================================================
### 4. LLDP NEIGHBOR TOPOLOGY
### ====================================================================================

echo "🔗 Gathering LLDP topology..."

if ! pgrep lldpd >/dev/null; then
    echo "Starting lldpd daemon..."
    # Start lldpd detached from stdout/stderr to prevent hanging the pipe
    lldpd -d >/dev/null 2>&1 &
    sleep 2
fi

lldpctl > "$TEMP_DIR/lldp.txt" || echo "⚠ No LLDP data found."

echo "✔ LLDP scan complete."
echo


### ====================================================================================
### 5. SNMP DEVICE DISCOVERY
### ====================================================================================

echo "🔍 Attempting SNMP discovery (community: public)..."

> "$TEMP_DIR/snmp.txt"

while read -r line; do
    ip=$(echo "$line" | cut -d'|' -f1 | tr -d ' ')
    [[ -z "$ip" ]] && continue
    # timeout 1s, 1 retry
    snmpwalk -v2c -c public -t 1 -r 1 "$ip" 1.3.6.1.2.1.1.5.0 \
        >> "$TEMP_DIR/snmp.txt" 2>/dev/null || true
done < "$TEMP_DIR/hosts.txt"

echo "✔ SNMP sweep done."
echo


### ====================================================================================
### 6. CLASSIFY HOSTS & ESTIMATE DEPTH
### ====================================================================================

echo "🧠 Classifying hosts and estimating depth..."

declare -A host_name
declare -A host_role
declare -A depth

# Parse hosts and classify based on hostname patterns
while read -r line; do
    ip=$(echo "$line" | cut -d'|' -f1 | tr -d ' ')
    name=$(echo "$line" | cut -d'|' -f2- | sed 's/^ //g')

    [[ -z "$ip" ]] && continue

    host_name["$ip"]="$name"

    lname=$(echo "$name" | tr 'A-Z' 'a-z')

    role="unknown"

    # Extract MAC for OUI lookup
    mac=$(grep "$ip" "$TEMP_DIR/arp.txt" | awk '{print $2}' | head -1)
    
    if [[ "$ip" == "$GATEWAY" ]]; then
        role="gateway/router"
    elif [[ "$lname" == *"routerboard"* ]]; then
        role="gateway/router"
    elif [[ "$lname" == *"tl-sg"* ]] || [[ "$lname" == *"tp-link"* ]] || [[ "$lname" == *"tplink"* ]] || [[ "$lname" == *"unifi"* ]] || [[ "$lname" == *"cisco"* ]] || [[ "$lname" == *"netgear"* ]]; then
        role="switch/ap"
    elif [[ "$lname" == *"firewalla"* ]]; then
        role="firewall"
    elif [[ "$lname" == *"nas"* ]] || [[ "$lname" == *"ugreen"* ]] || [[ "$lname" == *"synology"* ]] || [[ "$lname" == *"qnap"* ]]; then
        role="nas"
    elif [[ "$lname" == *"jellyfin"* ]] || [[ "$lname" == *"wizarr"* ]] || [[ "$lname" == *"b2backup"* ]] || [[ "$lname" == *"postgres"* ]] || [[ "$lname" == *"onyx"* ]] || [[ "$lname" == *"n8n"* ]] || [[ "$lname" == *"grafana"* ]] || [[ "$lname" == *"prometheus"* ]]; then
        role="service"
    elif [[ "$lname" == *"server"* ]] || [[ "$lname" == *"debian"* ]] || [[ "$lname" == *"ubuntu"* ]] || [[ "$lname" == *"centos"* ]] || [[ "$lname" == *"redhat"* ]] || [[ "$lname" == *"fedora"* ]] || [[ "$lname" == *"arch"* ]] || [[ "$lname" == *"manjaro"* ]] || [[ "$lname" == *"linux"* ]]; then
        role="server"
    elif [[ "$lname" == *"desktop"* ]] || [[ "$lname" == *"g-pro"* ]] || [[ "$lname" == *"laptop"* ]] || [[ "$lname" == *"iphone"* ]] || [[ "$lname" == *"android"* ]]; then
        role="client"
    fi

    # Fallback: Check MAC OUI for virtualization
    if [[ "$role" == "unknown" && -n "$mac" ]]; then
        # Common Virtualization OUIs
        if [[ "$mac" =~ ^(02:42:ac|00:50:56|00:0c:29|00:05:69|00:16:3e|00:15:5d|00:1c:42|00:03:ff) ]]; then
             role="service" # Likely a container or VM
        fi
    fi

    host_role["$ip"]="$role"
done < "$TEMP_DIR/hosts.txt"

# Initialize depth: default unknown (99)
while read -r line; do
    ip=$(echo "$line" | cut -d'|' -f1 | tr -d ' ')
    [[ -z "$ip" ]] && continue
    depth["$ip"]=99
done < "$TEMP_DIR/hosts.txt"

# Set gateway depth
depth["$GATEWAY"]=0

# Heuristic depth based on role
for ip in "${!depth[@]}"; do
    if [[ "$ip" == "$GATEWAY" ]]; then
        depth["$ip"]=0
        continue
    fi

    role="${host_role[$ip]}"

    case "$role" in
        "gateway/router")
            depth["$ip"]=0
            ;;
        "switch/ap"|"firewall")
            depth["$ip"]=1
            ;;
        "server"|"nas"|"service"|"client")
            depth["$ip"]=2
            ;;
        *)
            # leave as 99 if truly unknown; or set to 2 as "somewhere behind infra"
            depth["$ip"]=2
            ;;
    esac
done


### ====================================================================================
### 7. WRITE OUTPUT MAP
### ====================================================================================

OUTPUT="network_map.txt"
echo "### LAN NETWORK MAP" > "$OUTPUT"
echo "Generated: $(date)" >> "$OUTPUT"
echo >> "$OUTPUT"

echo "Gateway: $GATEWAY (${host_name[$GATEWAY]})" >> "$OUTPUT"
echo "LAN Interface: $LAN_IFACE" >> "$OUTPUT"
echo "Subnet: $SUBNET" >> "$OUTPUT"
echo >> "$OUTPUT"

echo "=== Devices Found ===" >> "$OUTPUT"
while read -r line; do
    ip=$(echo "$line" | cut -d'|' -f1 | tr -d ' ')
    name="${host_name[$ip]}"
    role="${host_role[$ip]}"
    d="${depth[$ip]}"
    printf "%-15s | %-35s | role=%-15s | depth=%s\n" "$ip" "$name" "$role" "$d" >> "$OUTPUT"
done < "$TEMP_DIR/hosts.txt"
echo >> "$OUTPUT"

echo "=== LLDP Topology (raw) ===" >> "$OUTPUT"
cat "$TEMP_DIR/lldp.txt" >> "$OUTPUT"
echo >> "$OUTPUT"

echo "=== SNMP Hostnames (sysName) ===" >> "$OUTPUT"
cat "$TEMP_DIR/snmp.txt" >> "$OUTPUT"
echo >> "$OUTPUT"


### ====================================================================================
### 8. HEURISTIC TOPOLOGY TREE
### ====================================================================================

{
    echo "=== Heuristic Topology Tree ==="
    echo

    echo "Gateway (depth 0):"
    echo "  - $GATEWAY (${host_name[$GATEWAY]}) [${host_role[$GATEWAY]}]"
    echo

    echo "Infrastructure (depth 1: switches / AP / firewall):"
    for ip in "${!host_role[@]}"; do
        if [[ "${host_role[$ip]}" == "switch/ap" || "${host_role[$ip]}" == "firewall" ]]; then
            printf "  - %-15s (%s) [%s]\n" "$ip" "${host_name[$ip]}" "${host_role[$ip]}"
        fi
    done | sort
    echo

    echo "Servers / NAS / Services (depth 2):"
    for ip in "${!host_role[@]}"; do
        case "${host_role[$ip]}" in
            "server"|"nas"|"service")
                printf "  - %-15s (%s) [%s]\n" "$ip" "${host_name[$ip]}" "${host_role[$ip]}"
                ;;
        esac
    done | sort
    echo

    echo "Clients (depth 2):"
    for ip in "${!host_role[@]}"; do
        if [[ "${host_role[$ip]}" == "client" ]]; then
            printf "  - %-15s (%s) [%s]\n" "$ip" "${host_name[$ip]}" "${host_role[$ip]}"
        fi
    done | sort
    echo

    echo "Unknown-role devices (depth 2):"
    for ip in "${!host_role[@]}"; do
        if [[ "${host_role[$ip]}" == "unknown" && "$ip" != "$GATEWAY" ]]; then
            printf "  - %-15s (%s) [%s]\n" "$ip" "${host_name[$ip]}" "${host_role[$ip]}"
        fi
    done | sort
    echo

} >> "$OUTPUT"


echo
echo "🎉 Network map generated:"
echo "   → $OUTPUT"
echo
echo "You can view it with:"
echo "   cat $OUTPUT"
echo

# Cleanup background processes
pkill lldpd || true
