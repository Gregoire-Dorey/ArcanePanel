<p align="center">
  <img src="arcanepanel.png" alt="Arcane Panel" width="140" />
</p>

<h1 align="center">Arcane Panel</h1>

<p align="center">
  Un panel d’admin self-hosted pour gérer tes machines, checks, alertes et jobs — version V1 (Django + Celery).
</p>

<p align="center">
  <!-- "Latest Release / Pre-Release" style comme ton screen -->
  <img alt="Latest Release" src="https://img.shields.io/github/v/release/Gregoire-Dorey/ArcanePanel?label=release&style=flat&logo=github" />
  <img alt="Latest Pre-Release" src="https://img.shields.io/github/v/release/Gregoire-Dorey/ArcanePanel?include_prereleases&label=pre-release&style=flat&logo=github" />
</p>

<p align="center">
  <!-- Badges perso / branding -->
  <img alt="ArcaneCloud" src="https://img.shields.io/badge/ArcaneCloud-Infra%20Panel-5B5BFF?style=flat&logo=icloud&logoColor=white" />
  <img alt="Self-Hosted" src="https://img.shields.io/badge/self--hosted-yes-00C2A8?style=flat&logo=homeassistant&logoColor=white" />
  <img alt="Neon UI" src="https://img.shields.io/badge/ui-neon%20dashboard-9B5CFF?style=flat&logo=electron&logoColor=white" />
  <img alt="Open Source" src="https://img.shields.io/badge/open--source-ready-2EA043?style=flat&logo=opensourceinitiative&logoColor=white" />
</p>

<p align="center">
  <!-- Stack -->
  <img alt="Django" src="https://img.shields.io/badge/Django-5.x-0C4B33?style=flat&logo=django&logoColor=white" />
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white" />
  <img alt="Redis" src="https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white" />
  <img alt="Celery" src="https://img.shields.io/badge/Celery-5.x-37814A?style=flat&logo=celery&logoColor=white" />
  <img alt="Docker Compose" src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white" />
</p>

<p align="center">
  <!-- Repo badges -->
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/Gregoire-Dorey/ArcanePanel?style=flat&logo=git&logoColor=white" />
  <img alt="Issues" src="https://img.shields.io/github/issues/Gregoire-Dorey/ArcanePanel?style=flat&logo=github&logoColor=white" />
  <img alt="Stars" src="https://img.shields.io/github/stars/Gregoire-Dorey/ArcanePanel?style=flat&logo=github&logoColor=white" />
  <img alt="License" src="https://img.shields.io/github/license/Gregoire-Dorey/ArcanePanel?style=flat&logo=law&logoColor=white" />
</p>

---

## 🧠 C’est quoi Arcane Panel ?

**Arcane Panel** est une V1 prête à lancer qui te donne un cockpit unique :
- inventaire (assets),
- supervision (checks + historique),
- alerting (open/close),
- socle “jobs” (actions à exécuter plus tard via agent ou APIs).

Le but : une base solide, simple, extensible, avant d’ajouter **Proxmox / PBS / agents**, etc.

---

## ✨ Features (V1)

### ✅ Assets
- inventaire machines (VM / serveur / NAS / réseau / autre)
- tags (ex: `pve,prod,site-a`)
- activation/désactivation

### ✅ Monitoring (checks)
- `ping` (ICMP)
- `tcp_port` (ex: 22/80/443)
- `http/https` (status attendu configurable)
- `ssl_expiry` (alerte si expiration proche)

### ✅ Alerts
- alertes automatiques à l’échec
- fermeture automatique au retour OK
- historique + détails (asset, type, message)

### ✅ Jobs (socle)
- modèle Job + logs
- prêt pour : restart service / proxmox start/stop / PBS backup trigger / etc.

### ✅ Asynchrone
- Celery Worker (exécution)
- Celery Beat (scheduler)

---

## 📦 Tech stack

- **Backend** : Django 5 + DRF (prêt pour APIs)
- **DB** : PostgreSQL
- **Queue** : Redis
- **Workers** : Celery + Beat
- **Run** : Docker Compose

---

## 🚀 Installation (Debian/Ubuntu)

### 1) Récupérer le projet
```bash
git clone https://github.com/OWNER/REPO.git arcane-panel
cd arcane-panel