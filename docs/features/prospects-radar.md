<!-- last_verified: 2026-09-07 -->
# Feature: ProspectsRadar - Moteur de Qualification de Leads IA

## 1. Description & Proposition de Valeur

**ProspectsRadar** transforme l'audit technique d'invisibilité IA (AEO / Answer Engine Optimization / LLM Shopping) en **pipeline commercial clé en main pour les agences web, SEO et e-commerce**.

Au lieu de vendre un simple audit, l'agence reçoit chaque semaine un flux de leads e-commerce pré-qualifiés avec :
- Un score d'invisibilité IA déterministe (0 à 100) calculé sur 5 piliers techniques.
- Les failles exactes identifiées (balises manquantes, blocage robots.txt, bruit DOM, absence de llms.txt).
- Les coordonnées des décideurs (CEO, Fondateurs, Directeurs E-commerce) enrichies.
- Un angle d'approche commercial (cold email) personnalisé et pré-rédigé, prêt à être copié ou importé dans un outil de cold mailing (Instantly, Smartlead, Lemlist).
- Un rapport d'audit PDF en marque blanche généré pour chaque prospect.

---

## 2. Les 5 Piliers du Scoring (0 - 100)

| Pilier | Poids | Description & Critères |
| :--- | :--- | :--- |
| **1. Crawl & WAF (IA Bot Access)** | 20% | Analyse de `robots.txt` et headers WAF. Détecte si `GPTBot`, `ClaudeBot`, `PerplexityBot` ou `Google-Extended` sont bloqués. |
| **2. Données Structurées Schema.org** | 25% | Extraction JSON-LD `Product` & `Offer`. Vérifie la présence des champs vitaux pour les agents d'achat IA : `price`, `availability`, `shippingDetails`, `hasMerchantReturnPolicy`. |
| **3. Pureté Sémantique & Bruit DOM** | 20% | Ratio de contenu utile / bruit HTML. Présence de balises `h1`, métadonnées OpenGraph et volume de scripts tiers polluant le contexte des LLMs. |
| **4. Simulation Acheteur IA (Fallback)** | 20% | Capacité d'un agent LLM à extraire le prix, la devise, le nom et la disponibilité directement depuis le DOM sans JavaScript activé. |
| **5. Protocoles Agentiques (llms.txt)** | 15% | Présence et validité de `/llms.txt` ou d'un endpoint agentique pour le catalog crawling des modèles de langage. |

Un score global **inférieur à 40/100** indique un prospect avec une douleur critique (**Critical Pain**), idéal pour la prospection d'agence.

---

## 3. Endpoints API

Tous les endpoints respectent l'architecture en couches (`runtime` -> `service` -> `repo`).

### `GET /leads`
Renvoie la liste des prospects qualifiés avec filtrage par vertical.
* **Paramètre Query** : `vertical` (`all`, `shopify_fr`, `mode_beaute`, `maison_deco`)
* **Réponse** : Liste d'objets `ProspectLead` (scores, décideur, pitch, faiblesses, statut d'opportunité).

### `GET /leads/stats`
Renvoie les agrégations pour les KPI cards de l'agence :
* `total_leads` : Nombre total de prospects qualifiés.
* `critical_pain_count` : Prospects avec score < 40.
* `critical_pain_rate` : Pourcentage de prospects critiques (opportunités fortes).
* `average_score` : Score moyen du vertical.
* `top_failing_pillars` : Répartition des failles les plus fréquentes.

### `POST /scan`
Audit instantané en direct d'une URL e-commerce.
* **Payload** : `{"url": "https://boutique-exemple.com"}`
* **Réponse** : `AuditResult` complet avec détail des 5 piliers, score global, éléments cassés (`broken_items`) et correctifs recommandés (`fix_diffs`).

### `POST /leads/batch`
Lancement asynchrone d'une campagne de scan massif sur un vertical e-commerce (`shopify_fr`, etc.).

### `GET /leads/export.csv`
Téléchargement instantané d'un fichier CSV formaté pour import direct dans Instantly, Smartlead ou HubSpot (colonnes : Domain, Contact Name, Email, LinkedIn, Score, Pitch Subject, Pitch Body).

### `GET /leads/{id}/pdf`
Génération et streaming d'un rapport PDF vectoriel d'audit technique (généré par ReportLab).

---

## 4. Composants Frontend

* `apps/web/src/components/dashboard/radar-stats-cards.tsx` : 4 cartes KPI en temps réel.
* `apps/web/src/components/dashboard/prospects-table.tsx` : Tableau dynamique avec modale de consultation du pitch commercial, filtre par vertical, badges de criticité et boutons d'export.
* `apps/web/src/components/dashboard/live-scan-card.tsx` : Scanner interactif pour auditer n'importe quelle URL en direct.
* `apps/web/src/lib/api-client.ts` & `apps/web/src/lib/queries.ts` : Couche TanStack Query unifiée.
