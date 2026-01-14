#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Lance ce script en root: sudo bash install.sh"
  exit 1
fi

echo "[1/6] Paquets de base..."
apt-get update
apt-get install -y ca-certificates curl gnupg git

echo "[2/6] Installation Docker (si absent)..."
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
  echo "Docker déjà installé."
fi

echo "[3/6] Préparation du .env..."
if [[ ! -f .env ]]; then
  cp .env.example .env
  # secret simple auto
  SECRET=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)
  sed -i "s/^DJANGO_SECRET_KEY=.*/DJANGO_SECRET_KEY=${SECRET}/" .env
  echo "✅ .env créé (pense à ajuster EMAIL / hosts / debug)."
else
  echo ".env déjà présent."
fi

echo "[4/6] Build & start..."
docker compose up -d --build

echo "[5/6] Création superuser Django..."
echo "👉 On va créer un compte admin. Suis les prompts."
docker compose exec web python manage.py createsuperuser

echo "[6/6] Terminé."
echo "✅ Panel: http://IP_DU_SERVEUR:${PANEL_PORT:-8000}"
echo "✅ Admin Django: http://IP_DU_SERVEUR:${PANEL_PORT:-8000}/admin/"
