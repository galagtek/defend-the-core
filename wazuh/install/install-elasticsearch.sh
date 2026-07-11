#!/usr/bin/env bash
# ============================================================
# Wazuh — Installation Elasticsearch/Kibana (optionnel, standalone)
# ============================================================
# Script ALTERNATIF si vous préférez une stack Elastic séparée du
# Wazuh Indexer (fork). Non requis si install-wazuh-manager.sh a été
# utilisé (le Wazuh Indexer remplace Elasticsearch).
#
# Usage : uniquement si vous voulez un Elasticsearch dédié.
# ============================================================
set -euo pipefail

ELASTIC_VERSION="8.11.0"

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root"; exit 1; }

log "=== Installation Elasticsearch $ELASTIC_VERSION (standalone) ==="

# 1. Pré-requis
apt-get update -qq
apt-get install -y -qq curl gnupg2 apt-transport-https

# 2. Clé GPG Elastic
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | \
    gpg --dearmor -o /usr/share/keyrings/elastic.gpg

# 3. Repository
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" \
    > /etc/apt/sources.list.d/elastic-8.x.list

apt-get update -qq

# 4. Installation
log "Installation Elasticsearch + Kibana..."
apt-get install -y -qq elasticsearch="${ELASTIC_VERSION}" kibana="${ELASTIC_VERSION}"

# 5. Configuration réseau (VLAN 99 uniquement)
log "Configuration réseau (écoute sur 10.10.99.10)..."
cat > /etc/elasticsearch/elasticsearch.yml << 'EOF'
cluster.name: wazuh-cluster
node.name: wazuh-node-1
network.host: 10.10.99.10
http.port: 9200
discovery.type: single-node

# Sécurité : TLS + auth activés par défaut en 8.x
xpack.security.enabled: true
xpack.security.enrollment.enabled: true
EOF

cat > /etc/kibana/kibana.yml << 'EOF'
server.port: 5601
server.host: "10.10.99.10"
server.name: "wazuh-dashboard"
elasticsearch.hosts: ["https://10.10.99.10:9200"]
elasticsearch.ssl.verificationMode: certificate
EOF

# 6. Démarrage
log "Démarrage des services..."
systemctl daemon-reload
systemctl enable --now elasticsearch
systemctl enable --now kibana

# 7. Initialisation des mots de passe
log "Génération des mots de passe Elasticsearch..."
/usr/share/elasticsearch/bin/elasticsearch-setup-passwords auto -b

log "=== Elasticsearch + Kibana installés ==="
log "Kibana : http://10.10.99.10:5601"
log "⚠️ Conservez les mots de passe générés ci-dessus."
