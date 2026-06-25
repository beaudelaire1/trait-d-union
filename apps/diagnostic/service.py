"""Service de diagnostic de site web — outil interne TUS.

Effectue 7 catégories de checks sur un site client :
  1. Performance  — temps de réponse, taille, compression
  2. SEO          — title, meta, h1, OG, structured data, robots, sitemap
  3. Sécurité     — HTTPS, headers (HSTS, CSP, X-Frame, etc.)
  4. Accessibilité— alt tags, lang, viewport, contraste hints
  5. Mobile       — viewport, responsive hints, tap targets
  6. SSL          — certificat, expiration, protocole
  7. Standards    — doctype, charset, W3C hints, liens internes cassés
"""
import re
import socket
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone as tz
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# ── Timeouts & limits ────────────────────────────────────────────────
REQUEST_TIMEOUT = 15
MAX_INTERNAL_LINKS_CHECK = 20
_LINK_CHECK_WORKERS = 5   # parallélisme pour les HEAD requests
_CATEGORY_WORKERS = 7     # une catégorie par thread
USER_AGENT = (
    "Mozilla/5.0 (compatible; TUS-Diagnostic/1.0; "
    "+https://www.traitdunion.it)"
)


def run_diagnostic(url: str) -> dict:
    """Point d'entrée principal : lance tous les checks et retourne le rapport.

    Returns:
        {
            "url": str,
            "overall_score": int (0-100),
            "categories": { name: {score, max, items: [{name, passed, detail}]} },
            "external_tools": [...],
            "duration": float,
        }
    """
    start = time.monotonic()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    session.max_redirects = 5

    # Fetch principal
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        return _error_result(url, str(exc), time.monotonic() - start)

    soup = BeautifulSoup(resp.text, "lxml") if resp.headers.get(
        "content-type", ""
    ).startswith("text/html") else None

    hostname = parsed.hostname or ""

    # ── Lancer les 7 catégories en parallèle ────────────────────────
    # Chaque check est indépendant ; on les soumet tous en même temps et on
    # collecte les résultats au fur et à mesure qu'ils arrivent.
    _checks = {
        "performance": lambda: _check_performance(resp),
        "seo":         lambda: _check_seo(url, resp, soup),
        "securite":    lambda: _check_security(resp),
        "accessibilite": lambda: _check_accessibility(soup),
        "mobile":      lambda: _check_mobile(soup),
        "ssl":         lambda: _check_ssl(hostname),
        "standards":   lambda: _check_standards(url, resp, soup, session),
    }
    categories = {}
    with ThreadPoolExecutor(max_workers=_CATEGORY_WORKERS) as _pool:
        _futures = {_pool.submit(fn): name for name, fn in _checks.items()}
        for _fut in as_completed(_futures):
            _name = _futures[_fut]
            try:
                categories[_name] = _fut.result()
            except Exception as _exc:
                categories[_name] = _score(
                    [{"name": "Erreur", "passed": False, "detail": str(_exc)}],
                    _name,
                )

    # ── Score global (moyenne pondérée) ──────────────────────────────
    weights = {
        "performance": 1.5,
        "seo": 1.5,
        "securite": 2.0,
        "accessibilite": 1.0,
        "mobile": 1.0,
        "ssl": 1.5,
        "standards": 0.5,
    }
    total_w = sum(weights.values())
    weighted = sum(
        (cat["score"] / max(cat["max"], 1)) * weights.get(name, 1)
        for name, cat in categories.items()
    )
    overall = round((weighted / total_w) * 100)

    duration = round(time.monotonic() - start, 2)
    encoded_url = requests.utils.quote(url, safe="")

    return {
        "url": url,
        "final_url": resp.url,
        "status_code": resp.status_code,
        "overall_score": min(overall, 100),
        "categories": categories,
        "external_tools": _external_tools(url, hostname, encoded_url),
        "duration": duration,
    }


# =====================================================================
# 1. PERFORMANCE
# =====================================================================
def _check_performance(resp):
    items = []
    # Temps de réponse
    elapsed_ms = round(resp.elapsed.total_seconds() * 1000)
    items.append({
        "name": "Temps de réponse",
        "passed": elapsed_ms < 2000,
        "detail": f"{elapsed_ms} ms" + (" ✓" if elapsed_ms < 1000 else " ⚠ > 1s" if elapsed_ms < 2000 else " ✗ > 2s"),
    })
    # Taille de la page
    size_kb = round(len(resp.content) / 1024, 1)
    items.append({
        "name": "Taille de la page",
        "passed": size_kb < 3000,
        "detail": f"{size_kb} Ko" + (" ✓" if size_kb < 1000 else " ⚠ volumineuse" if size_kb < 3000 else " ✗ très lourde"),
    })
    # Compression
    encoding = resp.headers.get("Content-Encoding", "")
    has_compression = encoding in ("gzip", "br", "deflate")
    items.append({
        "name": "Compression (gzip/br)",
        "passed": has_compression,
        "detail": encoding if has_compression else "Aucune compression détectée",
    })
    # Cache headers
    cache = resp.headers.get("Cache-Control", "")
    has_cache = bool(cache and ("max-age" in cache or "public" in cache))
    items.append({
        "name": "Cache-Control",
        "passed": has_cache,
        "detail": cache[:80] if cache else "Absent",
    })
    return _score(items, "Performance")


# =====================================================================
# 2. SEO
# =====================================================================
def _check_seo(url, resp, soup):
    items = []
    if not soup:
        return _score([{"name": "HTML", "passed": False, "detail": "Pas de contenu HTML"}], "SEO")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    items.append({
        "name": "Balise <title>",
        "passed": 10 <= len(title) <= 70,
        "detail": f'"{title[:60]}" ({len(title)} car.)' if title else "Absente",
    })
    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc = meta_desc.get("content", "") if meta_desc else ""
    items.append({
        "name": "Meta description",
        "passed": 50 <= len(desc) <= 160,
        "detail": f'"{desc[:80]}…" ({len(desc)} car.)' if desc else "Absente",
    })
    # H1
    h1s = soup.find_all("h1")
    items.append({
        "name": "Balise <h1>",
        "passed": len(h1s) == 1,
        "detail": f"{len(h1s)} trouvée(s)" + (f' : "{h1s[0].get_text(strip=True)[:50]}"' if len(h1s) == 1 else ""),
    })
    # Canonical
    canonical = soup.find("link", attrs={"rel": "canonical"})
    items.append({
        "name": "Canonical URL",
        "passed": canonical is not None,
        "detail": canonical.get("href", "")[:80] if canonical else "Absente",
    })
    # Open Graph
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_img = soup.find("meta", attrs={"property": "og:image"})
    items.append({
        "name": "Open Graph (og:title + og:image)",
        "passed": og_title is not None and og_img is not None,
        "detail": f"title={'✓' if og_title else '✗'} image={'✓' if og_img else '✗'}",
    })
    # Structured data (JSON-LD)
    ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    items.append({
        "name": "Données structurées (JSON-LD)",
        "passed": len(ld_scripts) > 0,
        "detail": f"{len(ld_scripts)} bloc(s) JSON-LD" if ld_scripts else "Aucun",
    })
    # robots.txt + sitemap.xml en parallèle
    def _fetch_robots():
        try:
            r = requests.get(urljoin(url, "/robots.txt"), timeout=5, headers={"User-Agent": USER_AGENT})
            return r.status_code == 200 and len(r.text) > 10
        except Exception:
            return False

    def _fetch_sitemap():
        try:
            r = requests.get(urljoin(url, "/sitemap.xml"), timeout=5, headers={"User-Agent": USER_AGENT})
            return r.status_code == 200 and "urlset" in r.text.lower()
        except Exception:
            return False

    with ThreadPoolExecutor(max_workers=2) as _pool:
        _f_robots = _pool.submit(_fetch_robots)
        _f_sitemap = _pool.submit(_fetch_sitemap)
        has_robots = _f_robots.result()
        has_sitemap = _f_sitemap.result()

    items.append({
        "name": "robots.txt",
        "passed": has_robots,
        "detail": "Présent" if has_robots else "Absent ou vide",
    })
    items.append({
        "name": "sitemap.xml",
        "passed": has_sitemap,
        "detail": "Présent" if has_sitemap else "Absent ou invalide",
    })
    return _score(items, "SEO")


# =====================================================================
# 3. SÉCURITÉ (Headers)
# =====================================================================
def _check_security(resp):
    items = []
    h = resp.headers

    # HTTPS
    items.append({
        "name": "HTTPS",
        "passed": resp.url.startswith("https://"),
        "detail": "✓ Connexion chiffrée" if resp.url.startswith("https://") else "✗ HTTP non sécurisé",
    })
    # HSTS
    hsts = h.get("Strict-Transport-Security", "")
    items.append({
        "name": "HSTS (Strict-Transport-Security)",
        "passed": bool(hsts),
        "detail": hsts[:80] if hsts else "Absent — navigateurs peuvent revenir en HTTP",
    })
    # CSP
    csp = h.get("Content-Security-Policy", "")
    items.append({
        "name": "Content-Security-Policy",
        "passed": bool(csp),
        "detail": csp[:100] + "…" if len(csp) > 100 else csp if csp else "Absent — vulnérable aux injections",
    })
    # X-Frame-Options
    xfo = h.get("X-Frame-Options", "")
    items.append({
        "name": "X-Frame-Options",
        "passed": xfo.upper() in ("DENY", "SAMEORIGIN"),
        "detail": xfo if xfo else "Absent — vulnérable au clickjacking",
    })
    # X-Content-Type-Options
    xcto = h.get("X-Content-Type-Options", "")
    items.append({
        "name": "X-Content-Type-Options",
        "passed": xcto.lower() == "nosniff",
        "detail": xcto if xcto else "Absent",
    })
    # Referrer-Policy
    rp = h.get("Referrer-Policy", "")
    items.append({
        "name": "Referrer-Policy",
        "passed": bool(rp),
        "detail": rp if rp else "Absent",
    })
    # Permissions-Policy
    pp = h.get("Permissions-Policy", "")
    items.append({
        "name": "Permissions-Policy",
        "passed": bool(pp),
        "detail": pp[:100] if pp else "Absent",
    })
    # Server header leak
    server = h.get("Server", "")
    items.append({
        "name": "Server header masqué",
        "passed": not server or server.lower() in ("cloudflare", "nginx", ""),
        "detail": f'Exposé : "{server}"' if server and server.lower() not in ("cloudflare", "nginx") else "OK",
    })
    return _score(items, "Sécurité")


# =====================================================================
# 4. ACCESSIBILITÉ
# =====================================================================
def _check_accessibility(soup):
    items = []
    if not soup:
        return _score([{"name": "HTML", "passed": False, "detail": "Pas de HTML"}], "Accessibilité")

    # Lang attribute
    html_tag = soup.find("html")
    lang = html_tag.get("lang", "") if html_tag else ""
    items.append({
        "name": 'Attribut lang sur <html>',
        "passed": bool(lang),
        "detail": f'lang="{lang}"' if lang else "Absent — lecteurs d'écran perdus",
    })
    # Images sans alt
    images = soup.find_all("img")
    no_alt = [img for img in images if not img.get("alt")]
    items.append({
        "name": "Images avec alt",
        "passed": len(no_alt) == 0,
        "detail": f"{len(images)} images, {len(no_alt)} sans alt" if images else "Aucune image trouvée",
    })
    # Form labels
    inputs = soup.find_all(["input", "select", "textarea"])
    inputs = [i for i in inputs if i.get("type") not in ("hidden", "submit", "button")]
    no_label = []
    for inp in inputs:
        inp_id = inp.get("id", "")
        has_label = bool(inp_id and soup.find("label", attrs={"for": inp_id}))
        has_aria = bool(inp.get("aria-label") or inp.get("aria-labelledby"))
        if not has_label and not has_aria:
            no_label.append(inp.get("name", inp.get("id", "?")))
    items.append({
        "name": "Labels de formulaire",
        "passed": len(no_label) == 0,
        "detail": f"{len(inputs)} champs, {len(no_label)} sans label/aria" if inputs else "Aucun formulaire",
    })
    # Skip navigation link
    skip = (
        soup.find("a", attrs={"href": "#main"})
        or soup.find("a", attrs={"href": "#content"})
        or soup.find("a", attrs={"href": "#main-content"})
    )
    items.append({
        "name": "Skip navigation",
        "passed": skip is not None,
        "detail": "Lien trouvé" if skip else "Absent — accessibilité au clavier réduite",
    })
    # Heading hierarchy
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    levels = [int(h.name[1]) for h in headings]
    has_hierarchy = len(levels) > 0 and levels[0] == 1
    skips = any(levels[i+1] - levels[i] > 1 for i in range(len(levels)-1)) if len(levels) > 1 else False
    items.append({
        "name": "Hiérarchie des titres",
        "passed": has_hierarchy and not skips,
        "detail": f"Niveaux : {' → '.join(f'h{l}' for l in levels[:8])}" + (" ⚠ saut" if skips else ""),
    })
    return _score(items, "Accessibilité")


# =====================================================================
# 5. MOBILE
# =====================================================================
def _check_mobile(soup):
    items = []
    if not soup:
        return _score([{"name": "HTML", "passed": False, "detail": "Pas de HTML"}], "Mobile")

    # Viewport meta
    viewport = soup.find("meta", attrs={"name": "viewport"})
    vp_content = viewport.get("content", "") if viewport else ""
    items.append({
        "name": "Meta viewport",
        "passed": "width=device-width" in vp_content,
        "detail": vp_content[:80] if vp_content else "Absent — pas de responsive",
    })
    # Font-size minimum (heuristic: check for very small fixed fonts)
    styles = soup.find_all("style")
    small_fonts = any("font-size:" in str(s) and re.search(r"font-size:\s*[0-9]px", str(s)) for s in styles)
    items.append({
        "name": "Pas de polices < 10px",
        "passed": not small_fonts,
        "detail": "Polices inline très petites détectées" if small_fonts else "OK",
    })
    # Touch-friendly: check for very small clickable elements (heuristic)
    small_links = soup.find_all("a", style=re.compile(r"font-size:\s*[0-8]px"))
    items.append({
        "name": "Liens tactiles accessibles",
        "passed": len(small_links) == 0,
        "detail": f"{len(small_links)} liens potentiellement trop petits" if small_links else "OK",
    })
    # No horizontal scroll hint: check for fixed-width elements
    fixed_width = soup.find_all(style=re.compile(r"width:\s*\d{4,}px"))
    items.append({
        "name": "Pas d'éléments trop larges",
        "passed": len(fixed_width) == 0,
        "detail": f"{len(fixed_width)} éléments avec largeur fixe > 999px" if fixed_width else "OK",
    })
    return _score(items, "Mobile")


# =====================================================================
# 6. SSL
# =====================================================================
def _check_ssl(hostname):
    items = []
    if not hostname:
        return _score([{"name": "Hostname", "passed": False, "detail": "Introuvable"}], "SSL")

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                protocol = ssock.version()

                # Certificat valide
                items.append({
                    "name": "Certificat SSL valide",
                    "passed": True,
                    "detail": f"Émetteur : {cert.get('issuer', (({'commonName': '?'},),))[0][0][1] if cert.get('issuer') else '?'}",
                })
                # Expiration
                not_after = cert.get("notAfter", "")
                if not_after:
                    expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=tz.utc)
                    days_left = (expiry - datetime.now(tz.utc)).days
                    items.append({
                        "name": "Expiration du certificat",
                        "passed": days_left > 30,
                        "detail": f"{days_left} jours restants (expire le {expiry.strftime('%d/%m/%Y')})",
                    })
                # Protocol
                items.append({
                    "name": "Protocole TLS",
                    "passed": protocol in ("TLSv1.2", "TLSv1.3"),
                    "detail": protocol,
                })
    except ssl.SSLCertVerificationError as e:
        items.append({"name": "Certificat SSL", "passed": False, "detail": f"Invalide : {e}"})
    except Exception as e:
        items.append({"name": "Connexion SSL", "passed": False, "detail": f"Erreur : {e}"})

    return _score(items, "SSL")


# =====================================================================
# 7. STANDARDS
# =====================================================================
def _check_standards(url, resp, soup, session):
    items = []
    if not soup:
        return _score([{"name": "HTML", "passed": False, "detail": "Pas de HTML"}], "Standards")

    # DOCTYPE
    doctype = "<!doctype html>" in resp.text[:100].lower()
    items.append({
        "name": "DOCTYPE HTML5",
        "passed": doctype,
        "detail": "Présent" if doctype else "Absent",
    })
    # Charset
    charset_meta = soup.find("meta", attrs={"charset": True}) or soup.find(
        "meta", attrs={"http-equiv": re.compile(r"content.type", re.I)}
    )
    items.append({
        "name": "Charset UTF-8",
        "passed": charset_meta is not None,
        "detail": "Déclaré" if charset_meta else "Absent",
    })
    # Favicon
    favicon = soup.find("link", attrs={"rel": re.compile(r"icon", re.I)})
    items.append({
        "name": "Favicon",
        "passed": favicon is not None,
        "detail": favicon.get("href", "")[:60] if favicon else "Absent",
    })
    # Liens internes cassés (sample)
    internal_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") or href.startswith(url):
            full = urljoin(url, href)
            if full not in internal_links:
                internal_links.append(full)
    broken = []
    links_to_check = internal_links[:MAX_INTERNAL_LINKS_CHECK]

    def _head(link):
        try:
            r = session.head(link, timeout=5, allow_redirects=True)
            return link, r.status_code
        except Exception:
            return link, None

    with ThreadPoolExecutor(max_workers=_LINK_CHECK_WORKERS) as _pool:
        for link, code in _pool.map(_head, links_to_check):
            if code is None:
                broken.append(f"{link} → timeout")
            elif code >= 400:
                broken.append(f"{link} → {code}")
    items.append({
        "name": f"Liens internes ({min(len(internal_links), MAX_INTERNAL_LINKS_CHECK)} testés)",
        "passed": len(broken) == 0,
        "detail": f"{len(broken)} cassé(s)" + (f" : {', '.join(broken[:3])}" if broken else ""),
    })
    # Mixed content hint
    http_resources = soup.find_all(
        ["img", "script", "link"], src=re.compile(r"^http://")
    ) + soup.find_all(
        ["img", "script", "link"], href=re.compile(r"^http://")
    )
    items.append({
        "name": "Pas de contenu mixte (HTTP dans HTTPS)",
        "passed": len(http_resources) == 0,
        "detail": f"{len(http_resources)} ressource(s) HTTP" if http_resources else "OK",
    })
    return _score(items, "Standards")


# =====================================================================
# HELPERS
# =====================================================================
def _score(items, label):
    """Calcule le score d'une catégorie."""
    passed = sum(1 for i in items if i["passed"])
    return {
        "label": label,
        "score": passed,
        "max": len(items),
        "percent": round((passed / max(len(items), 1)) * 100),
        "items": items,
    }


def _error_result(url, error, duration):
    return {
        "url": url,
        "final_url": url,
        "status_code": 0,
        "overall_score": 0,
        "categories": {},
        "external_tools": [],
        "duration": round(duration, 2),
        "error": str(error),
    }


def _external_tools(url, hostname, encoded_url):
    """Liens vers les outils de diagnostic externes gratuits."""
    return [
        {
            "name": "Google PageSpeed Insights",
            "url": f"https://pagespeed.web.dev/analysis?url={encoded_url}",
            "icon": "⚡",
            "category": "Performance",
        },
        {
            "name": "GTmetrix",
            "url": f"https://gtmetrix.com/?url={encoded_url}",
            "icon": "📊",
            "category": "Performance",
        },
        {
            "name": "Mozilla Observatory",
            "url": f"https://observatory.mozilla.org/analyze/{hostname}",
            "icon": "🛡️",
            "category": "Sécurité",
        },
        {
            "name": "SSL Labs",
            "url": f"https://www.ssllabs.com/ssltest/analyze.html?d={hostname}",
            "icon": "🔒",
            "category": "SSL",
        },
        {
            "name": "Security Headers",
            "url": f"https://securityheaders.com/?q={encoded_url}&followRedirects=on",
            "icon": "🔐",
            "category": "Sécurité",
        },
        {
            "name": "WAVE Accessibility",
            "url": f"https://wave.webaim.org/report#/{url}",
            "icon": "♿",
            "category": "Accessibilité",
        },
        {
            "name": "Google Rich Results",
            "url": f"https://search.google.com/test/rich-results?url={encoded_url}",
            "icon": "🔍",
            "category": "SEO",
        },
        {
            "name": "W3C Validator",
            "url": f"https://validator.w3.org/nu/?doc={encoded_url}",
            "icon": "✅",
            "category": "Standards",
        },
        {
            "name": "Google Mobile-Friendly",
            "url": f"https://search.google.com/test/mobile-friendly?url={encoded_url}",
            "icon": "📱",
            "category": "Mobile",
        },
    ]
