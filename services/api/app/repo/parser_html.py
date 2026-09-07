"""DOM fallback parsers for e-commerce products and semantic purity analyzer."""

import re
from typing import Any

from bs4 import BeautifulSoup


def parse_price_text(text: str) -> tuple[str | None, str | None]:
    """Extract numeric price and currency from a string."""
    if not text:
        return None, None
    raw = text.strip()

    currency = None
    if "£" in raw or "gbp" in raw.lower():
        currency = "GBP"
    elif "€" in raw or "eur" in raw.lower():
        currency = "EUR"
    elif "$" in raw or "usd" in raw.lower():
        currency = "USD"
    elif "chf" in raw.lower():
        currency = "CHF"

    m = re.search(r"(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)", raw)
    if m:
        num_str = m.group(1).replace(" ", "").replace("\xa0", "")
        if "," in num_str and "." in num_str:
            num_str = num_str.replace(",", "")
        elif "," in num_str:
            num_str = num_str.replace(",", ".")
        try:
            val = float(num_str)
            if 0.5 <= val <= 100_000:
                return f"{val:.2f}", currency or "EUR"
        except ValueError:
            pass
    return None, None


def extract_price_from_html(soup: BeautifulSoup) -> tuple[str | None, str | None, str | None]:
    """Extract price using OpenGraph, microdata and standard CSS classes."""
    for prop in ["og:price:amount", "product:price:amount"]:
        meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if meta and meta.get("content"):
            curr_meta = soup.find("meta", property=prop.replace(":amount", ":currency"))
            curr = curr_meta.get("content", "EUR").upper() if curr_meta else "EUR"
            p_val, _ = parse_price_text(meta["content"])
            if p_val:
                return p_val, curr, f"Meta {prop}"

    for val in ["price", "lowPrice"]:
        elem = soup.find(attrs={"itemprop": val})
        if elem:
            content = elem.get("content") or elem.get_text(strip=True)
            p_val, curr = parse_price_text(content)
            if p_val:
                return p_val, curr or "EUR", f"itemprop {val}"

    for cls in ["price", "product-price", "current-price", "price-item", "offer-price"]:
        for tag in soup.find_all(class_=re.compile(rf"\b{cls}\b", re.IGNORECASE)):
            txt = tag.get_text(" ", strip=True)
            if any(sym in txt for sym in ["€", "$", "£", "EUR"]):
                p_val, curr = parse_price_text(txt)
                if p_val:
                    return p_val, curr or "EUR", f"CSS .{cls}"

    return None, None, None


def extract_product_name(soup: BeautifulSoup, domain: str) -> str:
    """Extract product name from OpenGraph, H1, or Title."""
    for prop in ["og:title", "twitter:title"]:
        meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if meta and meta.get("content"):
            title = meta["content"].strip()
            if len(title) >= 3 and title.lower() != domain.lower():
                return title

    h1 = soup.find("h1")
    if h1:
        txt = h1.get_text(strip=True)
        if 3 <= len(txt) <= 120 and not any(
            b in txt.lower() for b in ["accueil", "panier", "connexion", "404"]
        ):
            return txt

    if soup.title and soup.title.string:
        raw_title = soup.title.string.strip()
        for sep in [" | ", " - ", " — ", " \u2013 ", " : "]:
            if sep in raw_title:
                raw_title = raw_title.split(sep)[0].strip()
                break
        clean_dom = domain.lower().replace("www.", "")
        raw_title = re.sub(re.escape(clean_dom), "", raw_title, flags=re.IGNORECASE).strip(" -|:\u2014\u2013")
        if len(raw_title) >= 3:
            return raw_title

    return "Boutique E-commerce"


def extract_stock_from_html(soup: BeautifulSoup) -> bool | None:
    """Detect availability keywords in HTML."""
    elem = soup.find(attrs={"itemprop": "availability"})
    if elem:
        txt = (elem.get("href") or elem.get("content") or elem.get_text(strip=True)).lower()
        if "instock" in txt:
            return True
        if "outofstock" in txt:
            return False

    body_text = soup.get_text(" ", strip=True).lower()
    if re.search(r"\b(in stock|en stock|disponible|en réserve)\b", body_text):
        return True
    if re.search(r"\b(out of stock|rupture de stock|épuisé|indisponible)\b", body_text):
        return False
    return None


def analyze_semantic_purity(soup: BeautifulSoup, raw_html_len: int) -> dict[str, Any]:
    """Measure text-to-noise ratio and estimated token consumption (Pillar 3)."""
    clone = BeautifulSoup(str(soup), "html.parser")
    body = clone.find("body") or clone
    for tag in body.find_all(
        ["script", "style", "noscript", "svg", "nav", "footer", "header", "iframe"]
    ):
        tag.decompose()

    clean_text = body.get_text(separator=" ", strip=True)
    clean_len = len(clean_text)
    token_est = max(int(clean_len / 4), 100)
    noise_pct = max(0, min(100, int((1.0 - (clean_len / max(raw_html_len, 1))) * 100)))

    score = 100
    details = []

    if token_est > 3500:
        score -= 40
        details.append(f"Consommation de tokens excessive (~{token_est} tokens)")
    elif token_est > 1800:
        score -= 20
        details.append(f"Volume de tokens modéré (~{token_est} tokens)")
    else:
        details.append(f"Excellente concision sémantique (~{token_est} tokens)")

    if noise_pct > 85:
        score -= 25
        details.append(f"Pollution DOM élevée : {noise_pct}% de code non textuel")
    else:
        score += 10
        details.append(f"Ratio de contenu utile sain (bruit DOM : {noise_pct}%)")

    score = max(10, min(100, score))
    return {
        "score": score,
        "tokens": token_est,
        "noise_pct": noise_pct,
        "status": f"{token_est} tokens ({noise_pct}% bruit)",
        "details": details,
    }
