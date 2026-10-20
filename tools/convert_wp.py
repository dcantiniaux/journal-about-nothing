#!/usr/bin/env python3
"""Convertit l'export WordPress (WXR) de Journal About Nothing en fichiers Markdown pour Astro.

Usage : python3 tools/convert_wp.py chemin/vers/export.xml

- Seuls les articles et pages publiés SANS mot de passe sont convertis.
- Les adresses d'origine (/AAAA/MM/JJ/slug/) sont conservées dans le champ `path`.
- Les images de journalaboutnothing.com sont réécrites en /wp-content/uploads/... ;
  la liste à télécharger est écrite dans tools/media-list.txt.
"""
import json, re, sys, html, urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from markdownify import MarkdownConverter

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "src/content/posts"
PAGES = ROOT / "src/content/pages"
DATA = ROOT / "src/data"
NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}

CAT_LABELS = {
    "pdocast-philo-pour-enfants": "Podcast philo pour enfants",
    "poesie": "Poésie",
    "psychologie-philosophie-analyse": "Psychologie, philosophie, analyse",
    "brouteur": "Brouteur",
    "journal-intime-de-la-pandemie": "Journal intime de la pandémie",
    "lettres-dinsultes-et-autres-correspondance": "Lettres d’insultes et autres correspondances",
    "tous-a-louest": "Tous à l’ouest !!",
}

# Accroches choisies dans la maquette (à vérifier mot pour mot par l'auteur).
ACCROCHES = {
    "/2024/07/27/conseils-pour-un-enterrement-2/": "Ne soufflez pas sur les bougies, il ne s’agit pas d’un anniversaire.",
    "/2022/04/20/les-lois-fondamentales-de-la-stupidite-humaine/": "L'humanité se divise en quatre grandes catégories : les crétins, les gens intelligents, les bandits, les être stupides.",
    "/2022/06/25/le-neo-feminisme-la-deconstruction-du-feminisme/": "La guillotine médiatique tourne à plein régime.",
    "/2022/01/25/les-surefficients-et-lamour/": "Les légos font mal.",
    "/2021/11/18/vers-la-fin-de-la-voiture-en-ville/": "L’automobiliste est un australopithèque. Le cycliste un gentleman moderne.",
    "/2021/06/11/la-mort-de-la-laicite/": "La laïcité est une vieille dame.",
    "/2021/04/18/quest-ce-quun-pervers-narcissique-chanson-et-decryptage/": "Je chante faux, mais l’idée est assez claire.",
    "/2021/01/05/quest-ce-que-lamour-pour-un-surefficient-mental-la-lettre-de-mon-ami-eric/": "Je vais tenter d’éclairer tes lanternes, même si tu plafonnes à 40 watts.",
}

# Images écartées à la demande de l'auteur, et leur remplaçant éventuel.
IMAGE_OVERRIDES = {
    "/wp-content/uploads/2021/02/973bjwyq_400x400.jpg": "/images/neo-feminisme-fox.jpg",
}

MEDIA = {}  # chemin local -> URL source

MEDIA_RE = re.compile(
    r"https?://(?:i[0-3]\.wp\.com/)?(?:journalaboutnothing\.com|journalaboutnothingblog\.(?:files\.)?wordpress\.com)"
    r"/(?:wp-content/uploads/)?(\d{4}/\d{2}/[^\s\"'?#<>)]+)(?:\?[^\s\"'<>)]*)?"
)
SITE_RE = re.compile(r"^https?://(?:www\.)?(?:journalaboutnothing\.com|journalaboutnothingblog\.wordpress\.com)(/[^\s]*)?$")


def media_local(url):
    m = MEDIA_RE.match(url.strip())
    if not m:
        return None
    rel = urllib.parse.unquote(m.group(1))
    local = "/wp-content/uploads/" + rel
    if local in IMAGE_OVERRIDES:
        return IMAGE_OVERRIDES[local]
    MEDIA[local] = "https://journalaboutnothing.com/wp-content/uploads/" + urllib.parse.quote(rel)
    return local


def rewrite_media_in_text(text):
    return MEDIA_RE.sub(lambda m: media_local(m.group(0)) or m.group(0), text)


def internal_link(href):
    if not href:
        return href
    loc = media_local(href)
    if loc:
        return loc
    m = SITE_RE.match(href.strip())
    if m:
        return m.group(1) or "/"
    return href


def youtube_id(url):
    p = urllib.parse.urlparse(url)
    if p.netloc.endswith("youtu.be"):
        return p.path.strip("/").split("/")[0]
    if "youtube" in p.netloc:
        q = urllib.parse.parse_qs(p.query)
        if "v" in q:
            return q["v"][0]
        m = re.search(r"/(?:embed|shorts|v)/([\w-]+)", p.path)
        if m:
            return m.group(1)
    return None


def embed_html(url, guid=None):
    url = html.unescape(url.replace("\\/", "/")).strip()
    if guid:
        return f'<div class="embed embed-video"><iframe src="https://videopress.com/embed/{guid}" title="Vidéo" loading="lazy" allowfullscreen></iframe></div>'
    p = urllib.parse.urlparse(url)
    host = p.netloc
    yid = youtube_id(url)
    if yid:
        return f'<div class="embed embed-video"><iframe src="https://www.youtube-nocookie.com/embed/{yid}" title="Vidéo YouTube" loading="lazy" allow="encrypted-media; picture-in-picture" allowfullscreen></iframe></div>'
    if "videopress.com" in host:
        m = re.search(r"/(?:v|embed)/(\w+)", p.path)
        if m:
            return embed_html("", guid=m.group(1))
    if "dailymotion.com" in host:
        m = re.search(r"/video/(\w+)", p.path)
        if m:
            return f'<div class="embed embed-video"><iframe src="https://www.dailymotion.com/embed/video/{m.group(1)}" title="Vidéo Dailymotion" loading="lazy" allowfullscreen></iframe></div>'
    if "giphy.com" in host:
        src = url
        if not re.search(r"\.(gif|webp)$", p.path):
            m = re.search(r"([A-Za-z0-9]{8,})/?$", p.path)
            if m:
                src = f"https://media.giphy.com/media/{m.group(1)}/giphy.gif"
        return f'<figure class="gif"><img src="{src}" alt="" loading="lazy"></figure>'
    if host.endswith("twitter.com") or host.endswith("x.com"):
        return f'<p class="embed-link"><a href="{url}">Voir le message sur X</a></p>'
    local = internal_link(url)
    return f'<p class="embed-link"><a href="{local}">{html.escape(url)}</a></p>'


BLOCK_TAGS = r"(?:table|thead|tfoot|caption|col|colgroup|tbody|tr|td|th|div|dl|dd|dt|ul|ol|li|pre|form|map|area|blockquote|address|math|style|p|h[1-6]|hr|fieldset|legend|section|article|aside|hgroup|header|footer|nav|figure|figcaption|details|menu|summary|iframe|video|audio)"


def wpautop(text):
    text = text.replace("\r\n", "\n")
    text = re.sub(r"(<" + BLOCK_TAGS + r"[\s/>])", r"\n\n\1", text)
    text = re.sub(r"(</" + BLOCK_TAGS + r">)", r"\1\n\n", text)
    chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if c.strip()]
    out = []
    for c in chunks:
        if re.match(r"^</?" + BLOCK_TAGS + r"[\s/>]", c):
            out.append(c)
        else:
            out.append("<p>" + c.replace("\n", "<br>\n") + "</p>")
    return "\n".join(out)


class MD(MarkdownConverter):
    def convert_img(self, el, text, *args, **kwargs):
        alt = (el.get("alt") or "").replace("]", "")
        src = el.get("src") or ""
        return f"![{alt}]({src})" if src else ""


def clean_body(raw):
    t = raw or ""
    # Sondages Crowdsignal : dynamiques, retirés.
    t = re.sub(r"<!-- wp:crowdsignal-forms/(\w[\w-]*).*?<!-- /wp:crowdsignal-forms/\1 -->", "", t, flags=re.S)
    t = re.sub(r"<!-- wp:crowdsignal-forms/[^>]*/-->", "", t)
    t = re.sub(r"<!-- wp:jetpack/subscriptions[^>]*?(/-->|-->.*?<!-- /wp:jetpack/subscriptions -->)", "", t, flags=re.S)
    t = re.sub(r"\[jetpack_subscription_form[^\]]*\]", "", t)

    def emb(m):
        attrs = m.group(2) or "{}"
        try:
            a = json.loads(attrs)
        except Exception:
            a = {}
        inner = m.group(3)
        url = a.get("url")
        if not url:
            mm = re.search(r"https?://[^\s<\"]+", inner)
            url = mm.group(0) if mm else ""
        return "\n\n" + embed_html(url) + "\n\n" if url else ""

    t = re.sub(r"<!-- wp:(embed|core-embed/[\w-]+)\s*(\{.*?\})?\s*-->(.*?)<!-- /wp:\1 -->", emb, t, flags=re.S)

    def vid(m):
        attrs = m.group(1) or "{}"
        try:
            a = json.loads(attrs)
        except Exception:
            a = {}
        inner = m.group(2)
        if a.get("guid"):
            return "\n\n" + embed_html("", guid=a["guid"]) + "\n\n"
        mm = re.search(r"https?://videopress\.com/v/(\w+)", inner)
        if mm:
            return "\n\n" + embed_html("", guid=mm.group(1)) + "\n\n"
        return inner

    t = re.sub(r"<!-- wp:video\s*(\{.*?\})?\s*-->(.*?)<!-- /wp:video -->", vid, t, flags=re.S)
    t = re.sub(r"<!-- /?wp:[^>]*-->", "", t)
    t = re.sub(r"\[/?caption[^\]]*\]", "", t)
    if "<p" not in t:
        t = wpautop(t)
    # URL seules sur une ligne (oEmbed des articles classiques)
    def bare(m):
        return "\n" + embed_html(m.group(2)) + "\n"
    t = re.sub(r"(^|\n|<p>)\s*(https?://(?:www\.)?(?:youtube\.com|youtu\.be|dailymotion\.com|videopress\.com|media\.giphy\.com|giphy\.com)[^\s<]+)\s*(?=</p>|\n|$)", bare, t)
    return t


def to_markdown(raw):
    t = clean_body(raw)
    soup = BeautifulSoup(t, "html.parser")
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for s in soup.find_all(["script", "style", "noscript", "form"]):
        s.decompose()
    for img in soup.find_all("img"):
        src = img.get("data-orig-file") or img.get("src") or ""
        img["src"] = internal_link(src)
        for k in list(img.attrs):
            if k not in ("src", "alt"):
                del img[k]
    for a in soup.find_all("a"):
        if a.get("href"):
            a["href"] = internal_link(a["href"])
    for el in soup.find_all(["audio", "source", "video"]):
        if el.get("src"):
            el["src"] = internal_link(el["src"])

    raws = []

    def protect(el, html_str):
        raws.append(html_str)
        el.replace_with(BeautifulSoup(f"<p>RAWBLOCK{len(raws)-1}X</p>", "html.parser"))

    for el in soup.select("div.embed, p.embed-link, figure.gif"):
        protect(el, str(el))
    for el in soup.find_all("audio"):
        src = el.get("src") or (el.find("source") or {}).get("src")
        if src:
            protect(el, f'<audio controls preload="none" src="{src}"></audio>')
    for el in soup.find_all("iframe"):
        src = el.get("src", "")
        if src:
            protect(el, f'<div class="embed embed-video"><iframe src="{src}" title="Contenu intégré" loading="lazy" allowfullscreen></iframe></div>')
    for fig in soup.find_all("figure"):
        imgs = fig.find_all("img")
        if not imgs:
            continue
        cap = fig.find("figcaption")
        cap_html = ""
        if cap:
            cap_html = f"<figcaption>{cap.get_text(' ', strip=True)}</figcaption>"
        if len(imgs) > 1:
            inner = "".join(f'<img src="{i["src"]}" alt="{html.escape(i.get("alt",""))}" loading="lazy">' for i in imgs)
            protect(fig, f'<figure class="gallery">{inner}{cap_html}</figure>')
        elif cap_html:
            i = imgs[0]
            protect(fig, f'<figure><img src="{i["src"]}" alt="{html.escape(i.get("alt",""))}" loading="lazy">{cap_html}</figure>')

    md = MD(heading_style="ATX", bullets="-", strip=["span", "font", "u"], escape_misc=False).convert_soup(soup)
    for i, r in enumerate(raws):
        md = md.replace(f"RAWBLOCK{i}X", "\n\n" + r + "\n\n")
    md = md.replace(" ", " ")
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    return md


def plain(md):
    t = re.sub(r"<[^>]+>", " ", md)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[#>*_`|-]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def make_excerpt(md, limit=190):
    for para in md.split("\n\n"):
        p = para.strip()
        if not p or p.startswith(("<", "!", "#", "|", "---")) or len(plain(p)) < 40:
            continue
        txt = plain(p)
        if len(txt) <= limit:
            return txt
        cut = txt[:limit].rsplit(" ", 1)[0].rstrip(",;:—-")
        return cut + "…"
    return ""


def fm(d):
    lines = ["---"]
    for k, v in d.items():
        lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def comment_text(raw):
    t = BeautifulSoup(raw or "", "html.parser").get_text("\n")
    t = html.unescape(t).replace(" ", " ")
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def main(xml_path):
    ch = ET.parse(xml_path).getroot().find("channel")
    items = ch.findall("item")
    attach = {}
    for it in items:
        if it.find("wp:post_type", NS).text == "attachment":
            attach[it.find("wp:post_id", NS).text] = (it.find("wp:attachment_url", NS).text or "")

    cats = {}
    for c in ch.findall("wp:category", NS):
        slug = c.find("wp:category_nicename", NS).text
        parent = c.find("wp:category_parent", NS).text or None
        name = html.unescape(c.find("wp:cat_name", NS).text or slug)
        cats[slug] = {"slug": slug, "name": CAT_LABELS.get(slug, name), "parent": parent}
    tags = {}
    for t in ch.findall("wp:tag", NS):
        slug = t.find("wp:tag_slug", NS).text
        tags[slug] = html.unescape(t.find("wp:tag_name", NS).text or slug)

    for d in (POSTS, PAGES, DATA):
        d.mkdir(parents=True, exist_ok=True)
        if d in (POSTS, PAGES):
            for f in d.glob("*.md"):
                f.unlink()

    stats = {"posts": 0, "pages": 0, "skipped_protected": [], "comments": 0}
    for it in items:
        ptype = it.find("wp:post_type", NS).text
        status = it.find("wp:status", NS).text
        if ptype not in ("post", "page") or status != "publish":
            continue
        title = html.unescape(it.find("title").text or "Sans titre").strip()
        if (it.find("wp:post_password", NS).text or "").strip():
            stats["skipped_protected"].append(title)
            continue
        link = it.find("link").text
        path = urllib.parse.urlparse(link).path
        if not path.endswith("/"):
            path += "/"
        body = to_markdown(it.find("content:encoded", NS).text)
        if ptype == "page":
            if len(plain(body)) < 5:
                continue  # pages vides (Masterclasse, Podcast) : remplacées par des listes de rubrique
            slug = path.strip("/").replace("/", "-")
            (PAGES / f"{slug}.md").write_text(fm({"title": title, "path": path}) + body, encoding="utf-8")
            stats["pages"] += 1
            continue

        date = it.find("wp:post_date", NS).text
        modified = (it.find("wp:post_modified", NS).text or date)
        post_cats, post_tags = [], []
        for c in it.findall("category"):
            if c.get("domain") == "category":
                post_cats.append(c.get("nicename"))
            elif c.get("domain") == "post_tag":
                post_tags.append(c.get("nicename"))
        image = None
        for pm in it.findall("wp:postmeta", NS):
            if pm.find("wp:meta_key", NS).text == "_thumbnail_id":
                url = attach.get(pm.find("wp:meta_value", NS).text)
                if url:
                    image = media_local(url) or url
        if not image:
            m = re.search(r"!\[[^\]]*\]\((/(?:wp-content/uploads|images)/[^)]+\.(?:jpe?g|png|webp|gif))\)", body, re.I)
            if m:
                image = m.group(1)
        if image:
            body = re.sub(r"(?m)^!\[[^\]]*\]\(" + re.escape(image) + r"\)\s*", "", body, count=1)
        comments = []
        for c in it.findall("wp:comment", NS):
            if c.find("wp:comment_approved", NS).text != "1" or c.find("wp:comment_type", NS).text == "pingback":
                continue
            txt = comment_text(c.find("wp:comment_content", NS).text)
            if not txt:
                continue
            comments.append({
                "id": c.find("wp:comment_id", NS).text,
                "parent": (c.find("wp:comment_parent", NS).text or "0"),
                "author": html.unescape(c.find("wp:comment_author", NS).text or "Anonyme"),
                "date": c.find("wp:comment_date", NS).text.replace(" ", "T"),
                "text": txt,
            })
        comments.sort(key=lambda c: c["date"])
        stats["comments"] += len(comments)
        words = len(plain(body).split())
        exc = html.unescape(re.sub(r"<[^>]+>", "", it.find("excerpt:encoded", NS).text or "")).strip() or make_excerpt(body)
        data = {
            "title": title,
            "path": path,
            "date": date.replace(" ", "T"),
            "updated": modified.replace(" ", "T"),
            "categories": post_cats,
            "tags": post_tags,
            "image": image,
            "excerpt": exc,
            "accroche": ACCROCHES.get(path),
            "readingTime": max(1, round(words / 230)),
            "comments": comments,
        }
        data = {k: v for k, v in data.items() if v is not None}
        name = f"{date[:10]}-{path.strip('/').split('/')[-1]}"[:120]
        (POSTS / f"{name}.md").write_text(fm(data) + body, encoding="utf-8")
        stats["posts"] += 1

    used_tags = {}
    for f in POSTS.glob("*.md"):
        head = f.read_text(encoding="utf-8").split("---")[1]
        m = re.search(r'^tags: (.*)$', head, re.M)
        for t in json.loads(m.group(1)) if m else []:
            used_tags[t] = tags.get(t, t)
    (DATA / "categories.json").write_text(json.dumps(cats, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "tags.json").write_text(json.dumps(used_tags, ensure_ascii=False, indent=2), encoding="utf-8")
    lst = ROOT / "tools/media-list.txt"
    lst.write_text("\n".join(f"{k.lstrip('/')}\t{v}" for k, v in sorted(MEDIA.items())) + "\n", encoding="utf-8")
    stats["media"] = len(MEDIA)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
