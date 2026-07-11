#!/usr/bin/env bash
# ============================================================
# Ubuntu Server — Durcissement CIS essentiel
# ============================================================
# Applique un sous-ensemble des recommandations CIS Benchmark
# Ubuntu 26.04 (niveau 1). N'est pas exhaustif mais couvre les
# points critiques pour le projet.
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

log "=== Durcissement CIS essentiel (Ubuntu 26.04) ==="

# --- 1. Paramètres noyau (sysctl) ---
log "Durcissement sysctl..."
cat > /etc/sysctl.d/99-dtc-hardening.conf << 'EOF'
# ============================================================
# Durcissement noyau - Defend-The-Core (CIS Level 1)
# ============================================================

# --- Protection réseau ---
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# --- Anti-spoofing ---
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# --- SYN flood ---
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048

# --- Logging ---
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# --- ICMP ---
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1

# --- TCP keepalive (détecter les connexions mortes) ---
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 5

# --- Mémoire & exploitation ---
kernel.randomize_va_space = 2
kernel.yama.ptrace_scope = 2
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.perf_event_paranoid = 2

# --- Système de fichiers ---
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2
fs.suid_dumpable = 0

# --- Divers ---
dev.tty.ldisc_autoload = 0
kernel.core_uses_pid = 1
EOF
sysctl --system >/dev/null 2>&1
log "  sysctl appliqués (99-dtc-hardening.conf)."

# --- 2. Permissions système ---
log "Correction des permissions système..."

# Fichiers critiques
chown root:root /etc/passwd /etc/group /etc/shadow /etc/gshadow
chmod 644 /etc/passwd /etc/group
chmod 640 /etc/shadow /etc/gshadow
chmod 600 /boot/grub/grub.cfg

# Permissions crontab
chown root:root /etc/crontab
chmod 600 /etc/crontab
chown -R root:root /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/cron.monthly /etc/cron.d
chmod -R go-rwx /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/cron.monthly /etc/cron.d

# --- 3. Désactivation des services inutiles ---
log "Désactivation des services inutiles..."
SERVICES_TO_DISABLE=(
    "apport"          # Rapports de crash (info leak)
    "rsync"
    "nfs-common"
    "rpcbind"
    "avahi-daemon"
    "cups"            # Impression
    "speech-dispatcher"
    "bluetooth"
    "modemmanager"
)
for svc in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl list-unit-files | grep -q "$svc"; then
        systemctl disable --now "$svc" 2>/dev/null || true
        log "  $svc désactivé."
    fi
done

# --- 4. Désactivation des modules noyau dangereux ---
log "Blacklist des modules noyau dangereux..."
cat > /etc/modprobe.d/dtc-blacklist.conf << 'EOF'
# Désactivation des protocoles non utilisés (surface d'attaque)
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
# Désactivation USB storage (anti-exfiltration)
install usb-storage /bin/true
# Désactivation firewire/thunderbolt (DMA attacks)
install firewire-core /bin/true
install thunderbolt /bin/true
EOF

# --- 5. Configuration PAM (politique de mots de passe) ---
log "Durcissement PAM (politique mots de passe)..."
cat > /etc/security/pwquality.conf << 'EOF'
# Politique de complexité des mots de passe
minlen = 14           # Longueur minimale 14
minclass = 4          # 4 classes de caractères
maxrepeat = 3         # Max 3 caractères identiques consécutifs
maxclassrepeat = 4    # Max 4 caractères d'une même classe consécutifs
gecoscheck = 1        # Vérifier contre le champ GECOS
dictcheck = 1         # Vérifier contre le dictionnaire
usercheck = 1         # Vérifier contre le nom d'utilisateur
enforcing = 1
EOF

# Politique de verrouillage de compte
cat > /etc/pam.d/common-auth << 'EOF'
# PAM authentification commune durcie
auth    required    pam_tally2.so onerr=fail deny=5 unlock_time=900 audit
auth    [success=1 default=ignore]    pam_unix.so nullok_secure try_first_pass
auth    requisite    pam_deny.so
auth    required    pam_permit.so
auth    optional    pam_cap.so
EOF

# --- 6. Limites de session (anti fork bomb) ---
log "Limites de session..."
cat > /etc/security/limits.d/99-dtc.conf << 'EOF'
# Limites par utilisateur
*    hard    core    0          # Pas de core dumps
*    hard    nproc   4096       # Max processus
*    hard    nofile  65535      # Max fichiers ouverts
*    soft    nofile  65535
root    hard    nproc   unlimited
EOF

# --- 7. Login defs ---
log "Configuration /etc/login.defs..."
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/'   /etc/login.defs
sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   1/'    /etc/login.defs
sed -i 's/^PASS_WARN_AGE.*/PASS_WARN_AGE   7/'    /etc/login.defs
sed -i 's/^UMASK.*/UMASK           027/'          /etc/login.defs

# --- 8. Désactivation IPv6 (si non utilisé) ---
log "Désactivation IPv6 (non utilisé dans le labo)..."
cat >> /etc/sysctl.d/99-dtc-hardening.conf << 'EOF'

# --- IPv6 désactivé (labo IPv4 uniquement) ---
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF
sysctl -p /etc/sysctl.d/99-dtc-hardening.conf >/dev/null 2>&1

log "=== Durcissement CIS terminé ==="
log "Points appliqués :"
log "  - sysctl durcis (réseau, mémoire, kernel)"
log "  - Permissions fichiers critiques (passwd, shadow, crontab)"
log "  - Services inutiles désactivés"
log "  - Modules noyau dangereux blacklistés"
log "  - PAM : politique mots de passe (14 car, 4 classes, verrouillage)"
log "  - Limites session (anti fork bomb)"
log "  - login.defs (90j expiration, umask 027)"
log "  - IPv6 désactivé"
log "=== Ubuntu Server entièrement durci ==="
