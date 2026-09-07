<!-- last_verified: 2026-09-07 -->
# App Workflows - ProspectsRadar

Parcours utilisateurs et flux de travail clés dans **ProspectsRadar**.

---

## 1. Pipeline de Prospection & Dashboard Agence

Le tableau de bord principal (`/`) est la console centrale de l'agence pour prospecter les e-commerçants invisibles aux moteurs IA :

1. **Consultation des KPIs globaux** :
   - Volume total de leads pré-qualifiés.
   - Taux de douleur critique (boutiques avec un score IA < 40/100).
   - Score moyen de visibilité IA sur le marché cible.
   - Top 5 des failles techniques les plus fréquentes (Schema.org incomplet, blocage `GPTBot`, absence de `llms.txt`).

2. **Filtrage par Vertical** :
   - L'utilisateur filtre par secteur : *Shopify France*, *Mode & Beauté*, *Maison & Déco*, etc.
   - La liste se met à jour instantanément via TanStack Query (`useLeads`).

3. **Consultation d'un Lead & Pitch Commercial** :
   - L'agence clique sur **"Voir le pitch"** sur une ligne de prospect.
   - Une modale s'ouvre avec :
     - Le score global et la ventilation par pilier.
     - Les coordonnées du décideur identifié (Nom, Poste, Email vérifié, Profil LinkedIn).
     - L'angle de prospection pré-rédigé citant exactement les failles de la boutique.
     - Un bouton **"Copier le pitch"** en 1 clic.

4. **Exportation des Leads vers un Outil Cold Mail** :
   - L'utilisateur clique sur **"Exporter CSV"**.
   - L'API génère un CSV pré-formaté compatible avec *Instantly*, *Smartlead*, *Lemlist* ou un CRM (*HubSpot*).

5. **Téléchargement du Rapport d'Audit PDF** :
   - L'utilisateur clique sur l'icône **PDF** d'un lead.
   - Un rapport d'audit vectoriel complet en marque blanche est généré à la volée par ReportLab.

---

## 2. Audit Instantané en Direct (Scanner URL)

1. L'agence souhaite tester une boutique spécifique qui ne figure pas encore dans la liste.
2. L'utilisateur saisit l'URL dans la section **Scanner en direct** et valide.
3. Le backend exécute :
   - L'analyse des directives de crawl (`robots.txt`, bots IA).
   - L'extraction et la validation du JSON-LD Schema.org (`Product`, `Offer`, `shippingDetails`).
   - Le ratio bruit DOM / pureté sémantique.
   - La simulation d'achat agentique (extraction sans JS).
   - La vérification de `/llms.txt`.
4. Le résultat s'affiche en temps réel avec le score /100, les éléments cassés et les correctifs techniques préconisés.

---

## 3. Authentification & Gestion de Compte

1. Inscription sur `/signup` (email/mot de passe ou lien magique OTP).
2. Confirmation par email (interceptée localement par Mailpit à `:54324`).
3. Connexion sur `/signin`.
4. Gestion du profil sur `/account`.

---

## 4. Abonnements & Facturation Stripe

1. L'agence accède à `/billing` pour consulter les forfaits (Starter, Pro, Agence Illimitée).
2. Le bouton **Passer à l'offre supérieure** redirige vers Stripe Checkout.
3. Les webhooks Stripe mettent à jour automatiquement le statut dans Supabase.
4. Le portail de facturation Stripe permet de gérer ou résilier l'abonnement à tout moment.
