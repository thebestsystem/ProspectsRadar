# ProspectsRadar

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![React 19](https://img.shields.io/badge/React-19-149eca?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.11+-009688?logo=fastapi)
![TypeScript](https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white)

> **« Des leads e-commerce pré-qualifiés sur leur visibilité IA — avec un angle de prospection déjà écrit pour chacun. »**

**ProspectsRadar** est une plateforme SaaS B2B conçue pour les agences SEO, web et e-commerce. Elle qualifie automatiquement des milliers de boutiques e-commerce en calculant leur score d'invisibilité face aux moteurs de recherche IA (ChatGPT Search, Perplexity, Google AI Overviews, Claude), extrait les failles techniques précises, enrichit les coordonnées des décideurs (CEO, Fondateurs, Directeurs E-commerce) et génère des angles de prospection commerciale prêts à l'envoi.

---

## Ce que fournit ProspectsRadar

* **Scoring Déterministe 5 Piliers (0 à 100)** :
  1. **Crawl & WAF** : Blocages dans `robots.txt` des bots IA (`GPTBot`, `ClaudeBot`, `PerplexityBot`, etc.).
  2. **Schema.org JSON-LD** : Validation stricte des données `Product` & `Offer` indispensables aux agents IA (`price`, `availability`, `shippingDetails`, `hasMerchantReturnPolicy`).
  3. **Pureté Sémantique & Bruit DOM** : Détection des scripts tiers polluant le contexte des LLMs, ratio texte/balisage HTML.
  4. **Simulation Acheteur IA** : Capacité d'un agent autonome à extraire le produit et son prix sans exécution JavaScript.
  5. **Protocoles Agentiques** : Détection et validation du standard `/llms.txt`.

* **Identification des Prospects à Forte Douleur (< 40/100)** :
  Ciblage automatique des boutiques souffrant d'invisibilité critique (perte directe de trafic et de ventes IA).

* **Enrichissement des Décideurs** :
  Nom, poste (CEO, Fondateur, Head of E-commerce), email vérifié et lien LinkedIn.

* **Génération Automatique de Pitchs Commerciaux** :
  Un cold email rédigé sur-mesure pour chaque boutique, citant précisément ses faiblesses techniques pour maximiser le taux de réponse.

* **Exports Prêts pour vos Outils de Prospection** :
  - **Export CSV** : Compatible en 1 clic avec *Instantly*, *Smartlead*, *Lemlist* ou votre CRM (*HubSpot*).
  - **Rapports d'Audit PDF** : Compilés en marque blanche avec ReportLab pour transmission en pièce jointe ou lien public.

* **Audit Instantané d'URL** :
  Module de scan en temps réel pour auditer n'importe quel site e-commerce à la volée.

---

## Architecture du Projet

Le projet est un monorepo pnpm structuré selon les meilleures pratiques d'ingénierie logicielle :

```
apps/web/               Frontend Next.js 16 (App Router, Tailwind v4, shadcn/ui, TanStack Query)
services/api/           Backend FastAPI (architecture en couches strictes : types/config/repo/service/runtime)
packages/shared/        Types TypeScript partagés (synchronisés avec les modèles Pydantic)
docs/                   Documentation vivante (spécifications, workflows, sécurité, fiabilité)
infra/railway/          Configuration de déploiement Railway (recommandé)
```

### Invariants d'Architecture Backend

Le backend respecte une séparation stricte des responsabilités à sens unique :
`types` → `config` → `repo` → `service` → `runtime`

* Aucun import inverse toléré.
* Pas d'accès direct à la base ou au réseau hors de la couche `repo/`.
* Pas de logique métier dans les routeurs (`runtime/`).
* Tous les fichiers restent sous la barre des 300 lignes de code.
* 100% vérifié par des tests structurels automatisés (`pnpm check:structure`).

---

## Démarrage Rapide (Développement Local)

### Prérequis
* **Node.js** : version 20+ (ou Node LTS)
* **pnpm** : version 9+
* **Python** : version 3.11+

### Installation

1. **Cloner le projet et installer les dépendances JavaScript :**
   ```bash
   pnpm install
   ```

2. **Configurer l'environnement virtuel Python :**
   ```bash
   cd services/api
   python -m venv .venv
   # Windows :
   .venv\Scripts\activate
   # macOS / Linux :
   source .venv/bin/activate
   pip install -r requirements.txt
   cd ../..
   ```

3. **Variables d'environnement :**
   ```bash
   cp .env.example .env
   ```
   *Les valeurs de développement par défaut permettent de démarrer immédiatement l'application.*

4. **Lancer la stack complète :**
   ```bash
   pnpm dev
   ```
   * Frontend accessible sur : `http://localhost:3000`
   * Backend API accessible sur : `http://127.0.0.1:8000`

---

## Commandes Principales

| Commande | Action |
| :--- | :--- |
| `pnpm dev` | Démarre simultanément le web Next.js et l'API FastAPI |
| `pnpm dev:web` | Démarre uniquement le frontend web |
| `pnpm dev:api` | Démarre uniquement le backend API |
| `pnpm build` | Compile et vérifie les types de l'application Next.js |
| `pnpm lint` | Linter frontend (ESLint) |
| `pnpm test:web` | Tests unitaires frontend (Vitest) |
| `pnpm lint:api` | Linter backend (Ruff) |
| `pnpm test:api` | Tests automatisés backend (Pytest) |
| `pnpm check:structure` | Vérification stricte des frontières architecturales |

---

## Déploiement

Le déploiement recommandé pour ProspectsRadar est **Railway** pour l'ensemble de la stack (Web + API) :
* **Processus continus** : Le crawler asynchrone et la génération de PDF nécessitent un environnement sans les limitations de timeout du serverless.
* **Fichiers prêts à l'emploi** : [apps/web/railway.json](file:///apps/web/railway.json) et [services/api/railway.json](file:///services/api/railway.json) sont déjà configurés.
* Consultez le guide complet dans [infra/railway/README.md](file:///infra/railway/README.md).

---

## Documentation

* [docs/features/prospects-radar.md](docs/features/prospects-radar.md) — Spécification détaillée du moteur de scoring et qualification.
* [docs/app-workflows.md](docs/app-workflows.md) — Parcours utilisateurs et cas d'usage agences.
* [ARCHITECTURE.md](ARCHITECTURE.md) — Détail des couches techniques et flux de données.
* [docs/stripe-setup.md](docs/stripe-setup.md) — Guide de configuration de la facturation Stripe.

---

## Licence

Sous licence **MIT**.