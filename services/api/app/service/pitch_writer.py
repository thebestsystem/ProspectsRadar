"""Pitch writer: generates tailored cold outreach emails citing exact AI visibility flaws."""

from app.types.scanner import BrokenItem, DecisionMaker


def generate_cold_pitch(
    domain: str,
    company_name: str,
    score: int,
    broken_items: list[BrokenItem],
    failing_pillars: list[str],
    dm: DecisionMaker,
) -> str:
    """Compose ultra-targeted cold email using real audit score and detected flaws."""
    first_name = dm.name.split()[0] if dm.name else "Bonjour"
    clean_domain = domain.lower().replace("www.", "")

    flaws_text = []
    for item in broken_items[:2]:
        flaws_text.append(f"- {item.title} ({item.impact})")

    flaws_bullets = "\n".join(flaws_text) if flaws_text else "- Manque de balises structurées Schema.org\n- Absence du protocole llms.txt"

    subject = f"Audit visibilité IA de {clean_domain} (score : {score}/100)"

    body = f"""Bonjour {first_name},

J'ai passé {clean_domain} sur notre scanner de visibilité pour moteurs IA (ChatGPT Search, Perplexity, Gemini).

Le constat chiffré : votre boutique obtient un score de {score}/100.

En analysant le code source de vos fiches produits, voici les 2 points de friction majeurs qui bloquent aujourd'hui les agents d'achat IA :
{flaws_bullets}

Résultat : lorsqu'un internaute demande à ChatGPT ou Perplexity une recommandation dans votre catégorie, vos concurrents qui ont ce balisage sont cités en priorité.

Nous avons préparé le correctif technique complet pour {clean_domain} (fichiers JSON-LD validés + manifeste agentique).

Seriez-vous ouvert à ce que je vous transmette le rapport d'audit PDF complet cette semaine ?

Bien à vous,
"""
    return f"Objet : {subject}\n\n{body.strip()}"
