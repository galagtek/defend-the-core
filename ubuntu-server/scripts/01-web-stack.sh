#!/usr/bin/env bash
# ============================================================
# Ubuntu Server — Pile Web (Nginx + PostgreSQL)
# ============================================================
# Installe et durcit Nginx (reverse proxy interne) et PostgreSQL.
# Le serveur écoute sur 80/443, accessible uniquement via le
# reverse proxy de la DMZ (10.10.20.10).
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

log "=== Installation pile Web (Nginx + PostgreSQL) ==="

# --- 1. Nginx ---
log "Installation Nginx..."
apt-get install -y -qq nginx

# Désactivation de la page par défaut (sécurité : ne pas exposer d'info)
rm -f /etc/nginx/sites-enabled/default

# Configuration Nginx durcie
cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 768;
}

http {
    sendfile on;
    tcp_nopush on;
    types_hash_max_size 2048;
    server_tokens off;  # Cacher la version de Nginx

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logs
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    gzip on;

    # En-têtes de sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

# Site par défaut (écoute sur 80, redirige vers 443)
cat > /etc/nginx/sites-available/metier << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;

    # Certificats (à générer avec Let's Encrypt ou autosignés pour le labo)
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root /var/www/metier;
    index index.html index.php;

    location / {
        try_files $uri $uri/ =404;
    }

    # Bloquer l'accès aux fichiers cachés (.git, .env, etc.)
    location ~ /\. {
        deny all;
    }
}
EOF
ln -sf /etc/nginx/sites-available/metier /etc/nginx/sites-enabled/metier

# Génération certificat autosigné (labo)
if [[ ! -f /etc/ssl/certs/nginx-selfsigned.crt ]]; then
    log "Génération certificat autosigné (labo)..."
    mkdir -p /var/www/metier
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/nginx-selfsigned.key \
        -out /etc/ssl/certs/nginx-selfsigned.crt \
        -subj "/C=FR/ST=Paris/L=Paris/O=DefendTheCore/CN=ubuntu-web"
fi

# Page d'accueil basique
echo "<!DOCTYPE html><html><head><title>Defend-The-Core</title></head>" > /var/www/metier/index.html
echo "<body><h1>Serveur metier Defend-The-Core</h1><p>Zone critique - VLAN 30</p></body></html>" >> /var/www/metier/index.html
chown -R www-data:www-data /var/www/metier

systemctl restart nginx
systemctl enable nginx
log "Nginx configuré (HTTPS, en-têtes sécurité, server_tokens off)."

# --- 2. PostgreSQL ---
# Détection dynamique de la version (robuste quelle que soit la version Ubuntu)
# PostgreSQL 14 sur Ubuntu 22.04, 16 sur 24.04, 18 sur 26.04...
apt-get install -y -qq postgresql postgresql-contrib

# Récupération automatique de la version installée (bonne pratique : pas de codage en dur)
PG_VERSION=$(ls /etc/postgresql/ 2>/dev/null | head -1)
if [[ -z "$PG_VERSION" ]]; then
    # Fallback : interroger psql si le répertoire n'est pas standard
    PG_VERSION=$(psql --version 2>/dev/null | awk '{print $3}' | cut -d. -f1)
fi
log "PostgreSQL $PG_VERSION détecté et installé."

# Durcissement PostgreSQL (chemins construits dynamiquement)
PG_CONF="/etc/postgresql/${PG_VERSION}/main/postgresql.conf"
PG_HBA="/etc/postgresql/${PG_VERSION}/main/pg_hba.conf"

# Écoute uniquement sur localhost (pas d'exposition réseau)
sed -i "s/^#listen_addresses.*/listen_addresses = 'localhost'/" "$PG_CONF"
sed -i "s/^#password_encryption.*/password_encryption = scram-sha-256/" "$PG_CONF"

# pg_hba : authentification par mot de passe (scram) uniquement en local
cat > "$PG_HBA" << 'EOF'
# TYPE  DATABASE  USER  ADDRESS       METHOD
local   all       all                 peer
host    all       all   127.0.0.1/32  scram-sha-256
host    all       all   ::1/128       scram-sha-256
# Pas de connexion externe (la BDD n'est pas exposée sur le réseau)
EOF
chown postgres:postgres "$PG_HBA"
chmod 640 "$PG_HBA"

systemctl restart postgresql
systemctl enable postgresql
log "PostgreSQL configuré (écoute localhost, scram-sha-256, pas d'accès réseau)."

log "=== Pile Web installée et durcie ==="
log "Prochaine étape : bash 02-harden-ssh.sh"
