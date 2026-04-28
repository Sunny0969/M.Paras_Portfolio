# -*- coding: utf-8 -*-
"""Assemble truemark_website_final.html: one file, mobile (<=992) + desktop (>=993) via @media layers."""
import re
from pathlib import Path

import os

ROOT = Path(__file__).parent
MOBILE = ROOT / "Truemark_mobile.html"
DESKTOP = ROOT / "truemark_website_final.html"
OUT = DESKTOP
BP_MAX = 992

GLOBAL_BASE = """
/* === Merged: shared base === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --green: #22c55e;
  --green-dim: #4ade80;
  --green-bg: rgba(34,197,94,0.06);
  --green-border: rgba(34,197,94,0.18);
  --blue: #3b82f6;
  --blue-dim: #93c5fd;
  --bg-primary: #04060c;
  --bg-secondary: #02040a;
  --bg-card: rgba(255,255,255,0.02);
  --border: rgba(255,255,255,0.07);
  --border-hover: rgba(255,255,255,0.12);
  --text-primary: #ffffff;
  --text-secondary: rgba(255,255,255,0.5);
  --text-muted: rgba(255,255,255,0.35);
  --font-display: 'poppins';
  --font-body: 'poppins';
  --radius: 12px;
  --radius-lg: 18px;
  --section-pad: 88px 48px;
}
html { scroll-behavior: smooth; }
body {
  font-family: var(--font-body);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}
.layout-mobile { }
.layout-desktop { display: none; }
@media (min-width: 993px) {
  .layout-mobile { display: none !important; }
  .layout-desktop { display: block !important; }
}
""".strip()


def pop_keyframes(s: str) -> tuple[list[str], str]:
    kfs: list[str] = []
    i, n = 0, len(s)
    out = []
    while i < n:
        j = s.find("@keyframes", i)
        if j < 0:
            out.append(s[i:])
            break
        out.append(s[i:j])
        ob = s.find("{", j)
        if ob < 0:
            out.append(s[j:])
            break
        depth, k = 0, ob
        while k < n:
            if s[k] == "{":
                depth += 1
            elif s[k] == "}":
                depth -= 1
                if depth == 0:
                    kfs.append(s[j : k + 1])
                    i = k + 1
                    break
            k += 1
        else:
            out.append(s[j:])
            break
    return kfs, "".join(out)


def dedupe_keyframes(kfs: list[str]) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for b in kfs:
        m = re.search(r"@keyframes\s+([\w-]+)", b)
        name = m.group(1) if m else ""
        if name in seen:
            continue
        if name:
            seen.add(name)
        out.append(b)
    return "\n".join(out)


def fix_mobile_hrefs(html: str) -> str:
    for a in ("services", "work", "packages", "templates", "about", "contact"):
        html = re.sub(rf'href="#{a}"', f'href="#m-{a}"', html)
    return html


def fix_mobile_ids_html(html: str) -> str:
    for a, b in (
        ("hamburger", "m-hamburger"),
        ("navDrawer", "m-navDrawer"),
        ("hero", "m-hero"),
        ("services", "m-services"),
        ("servicesScroll", "m-servicesScroll"),
        ("scrollDots", "m-scrollDots"),
        ("work", "m-work"),
        ("packages", "m-packages"),
        ("templates", "m-templates"),
        ("reviewsScroll", "m-reviewsScroll"),
        ("reviewDots", "m-reviewDots"),
        ("about", "m-about"),
        ("contact", "m-contact"),
    ):
        html = re.sub(rf'\bid="{a}"', f'id="{b}"', html)
    return fix_mobile_hrefs(html)


def fix_mobile_ids_css(css: str) -> str:
    for sec in ("hero", "services", "work", "packages", "templates", "about", "contact"):
        css = re.sub(rf"#{re.escape(sec)}\b", f"#m-{sec}", css)
    return css.replace("#reviewsScroll", "#m-reviewsScroll")


def fix_mobile_script_1(js: str) -> str:
    js = js.replace("getElementById('hamburger')", "getElementById('m-hamburger')")
    js = js.replace("getElementById('navDrawer')", "getElementById('m-navDrawer')")
    js = js.replace("getElementById('servicesScroll')", "getElementById('m-servicesScroll')")
    js = js.replace("const dots = document.querySelectorAll('.scroll-dot');", "const dots = document.getElementById('m-scrollDots')?.querySelectorAll('.scroll-dot') || [];")
    return js


def fix_mobile_script_2(js: str) -> str:
    js = js.replace("getElementById('reviewsScroll')", "getElementById('m-reviewsScroll')")
    js = js.replace("querySelectorAll('#reviewDots .scroll-dot')", "querySelectorAll('#m-reviewDots .scroll-dot')")
    return js


def strip_mob_css_reset(css: str) -> str:
    css = re.sub(r"/\* =+ RESET[^*]+\*/\s*", "", css, count=1)
    css = re.sub(
        r"\*\s*,\s*\*::before\s*,\s*\*::after\s*\{[^}]+\}\s*",
        "",
        css,
        count=1,
    )
    css = re.sub(r":root\s*\{[^}]+\}\s*", "", css, count=1)
    css = re.sub(r"html\s*\{[^}]+\}\s*", "", css, count=1)
    css = re.sub(r"body\s*\{[^}]+\}\s*", "", css, count=1, flags=re.DOTALL)
    return fix_mobile_ids_css(css)


def strip_desk_block_comment(css: str) -> str:
    m = re.search(
        r"/\* ={10,}[\s\S]*?Fraunces.*?\*+/\s*",
        css,
    )
    if m:
        return css[: m.start()] + css[m.end() :]
    return css


def remove_desk_responsive_block(css: str) -> str:
    i = css.find("/* ============ RESPONSIVE")
    j = css.find("/* ===== THANK YOU", i) if i >= 0 else -1
    if i >= 0 and j > i:
        return css[:i] + "\n" + css[j:]
    return css


def strip_desk_dev_banner(css: str) -> str:
    return re.sub(
        r"/\* ={5,}[\s\S]*?TRUEMARK TEMPLATES[\s\S]*?\*+/\s*",
        "",
        css,
        count=1,
    )


def strip_desk_css_reset(css: str) -> str:
    css = strip_desk_block_comment(css)
    css = strip_desk_dev_banner(css)
    css = re.sub(
        r"\*\s*,\s*\*::before\s*,\s*\*::after\s*\{[^}]+\}\s*",
        "",
        css,
        count=1,
    )
    css = re.sub(r":root\s*\{[^}]+\}\s*", "", css, count=1)
    css = re.sub(r"html\s*\{[^}]+\}\s*", "", css, count=1)
    css = re.sub(
        r"body\s*\{[^}]+\}\s*",
        "",
        css,
        count=1,
        flags=re.DOTALL,
    )
    return remove_desk_responsive_block(css)


def main() -> None:
    dsk0 = DESKTOP.read_text(encoding="utf-8")
    if 'class="layout-mobile"' in dsk0 and os.environ.get("TRUEMARK_REBUILD") != "1":
        raise SystemExit(
            "Refusing to rebuild: truemark_website_final.html already contains merged layouts. "
            "Restore a desktop-only HTML backup as the DESKTOP path, or run with TRUEMARK_REBUILD=1 if you know what you are doing."
        )
    mob = MOBILE.read_text(encoding="utf-8")
    dsk = dsk0

    m_styles = re.findall(r"<style>([\s\S]*?)</style>", mob, re.I)
    d_styles = re.findall(r"<style>([\s\S]*?)</style>", dsk, re.I)
    m_main = m_styles[0] if m_styles else ""
    d_main = d_styles[0] if d_styles else ""
    d_end = d_styles[1] if len(d_styles) > 1 else ""

    m_bundle = re.search(
        r"<script>(\n// =+ HAMBURGER[\s\S]*?)</script>\s*<style>([\s\S]*?)</style>\s*<script>([\s\S]*?)</script>",
        mob,
    )
    if not m_bundle:
        raise SystemExit("Mobile script bundle not found")
    s1, extra_css, s2 = m_bundle.group(1), m_bundle.group(2), m_bundle.group(3)
    s1, s2 = fix_mobile_script_1(s1), fix_mobile_script_2(s2)
    extra_css = fix_mobile_ids_css(extra_css)

    kf: list[str] = []
    t, m_main = pop_keyframes(m_main)
    kf += t
    t, d_main = pop_keyframes(d_main)
    kf += t
    t, d_end = pop_keyframes(d_end)
    kf += t
    m_main = strip_mob_css_reset(m_main)
    d_main = strip_desk_css_reset(d_main)

    b0 = mob.find("<body>") + 6
    b1 = mob.find("<script>\n// ===== HAMBURGER")
    mob_html = fix_mobile_ids_html(mob[b0:b1].strip())

    bds = dsk.find("<body>") + 6
    bde = dsk.find("<!-- Thank You Popup", bds)
    desk_html = dsk[bds:bde].strip() if bde > bds else dsk[bds : dsk.rfind("</body>")]

    t0 = dsk.find("<!-- Thank You Popup -->")
    t1 = dsk.find("\n\n<style>", t0) if t0 >= 0 else -1
    thank = dsk[t0:t1].strip() if t0 >= 0 and t1 > t0 else ""

    d_js_m = re.search(
        r"<script>\s*(document\.getElementById\('contactForm'[\s\S]*?)</script>\s*</body>",
        dsk,
        re.I,
    )
    d_js = d_js_m.group(1) if d_js_m else ""
    d_js = d_js.replace(
        "document.querySelectorAll('.form-input')",
        "document.querySelectorAll('#contactForm .form-input')",
    )
    d_js = d_js.replace(
        "document.querySelectorAll('.pkg-btn')",
        "document.querySelectorAll('.layout-desktop .pkg-btn')",
    )
    d_js = d_js.replace(
        "document.getElementById('contact')",
        "document.querySelector('.layout-desktop #contact')",
    )

    mobile_css_block = f"{m_main.rstrip()}\n\n{extra_css.rstrip()}\n"
    mobile_layer = f"@media (max-width: {BP_MAX}px) {{\n{mobile_css_block}}}\n"
    end_part = f"\n{d_end.rstrip()}\n" if d_end.strip() else ""
    desk_layer = f"@media (min-width: 993px) {{\n{d_main.rstrip()}{end_part}}}\n"

    mob_scripts = f"<script>\n{s1}\n</script>\n\n<script>\n{s2}\n</script>"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TrueMark Templates | Social Media Management &amp; Graphic Design | US &amp; UK</title>
<meta name="description" content="Done-for-you monthly social media packages, graphic design, and Canva templates for businesses across the US and UK. Top Rated on Upwork. Book a free call today.">
<meta name="keywords" content="social media management, graphic design, Canva templates, healthcare marketing, real estate marketing, small business design, US UK">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;900&display=swap" rel="stylesheet">
<style>
{GLOBAL_BASE}

{dedupe_keyframes(kf)}

{mobile_layer}
{desk_layer}
</style>
</head>
<body>
<div class="layout-mobile">
{mob_html}
</div>
<div class="layout-desktop">
{desk_html}
</div>
{thank}

<script>
{d_js}
</script>
{mob_scripts}
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print("Wrote", OUT, "chars", len(page))


if __name__ == "__main__":
    main()
