"""Turn a package's plain-text description into structured HTML.

Admin types descriptions as plain text in a textarea - a headline, some
paragraphs, labels ending in a colon, and emoji-led bullet lines. This
reads that existing structure and styles each part differently, so the
way admin writes descriptions doesn't have to change at all.

Anything that doesn't match a pattern falls back to a plain paragraph,
so an unusually formatted description never breaks - it just looks
plainer. All text is HTML-escaped before any markup is added.
"""
import re
import unicodedata

from markupsafe import Markup, escape

_PRICE_RE = re.compile(r"(?:₱|PHP\s?|\$|USD\s?|€|EUR\s?)\s?[\d,]+(?:\.\d+)?", re.IGNORECASE)
_DASH_RE = re.compile(r"\s+[—–-]\s+")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

# Characters that can follow an emoji and belong to it: variation
# selector, zero-width joiner, skin tones, keycap.
_EMOJI_JOINERS = {"\ufe0f", "\u200d", "\u20e3"}


def _is_emoji_char(ch):
    cp = ord(ch)
    if ch in _EMOJI_JOINERS or 0x1F3FB <= cp <= 0x1F3FF:
        return True
    if cp >= 0x1F000 or 0x2600 <= cp <= 0x27BF or 0x2B00 <= cp <= 0x2BFF:
        return True
    return unicodedata.category(ch) == "So"


def _split_emoji(line):
    """Return (leading_emoji, rest). leading_emoji is '' when there is none."""
    i = 0
    while i < len(line) and _is_emoji_char(line[i]):
        i += 1
    if i == 0:
        return "", line
    return line[:i], line[i:].strip()


def _inline(text):
    """Escape text, then allow **bold** (same syntax as the itinerary)."""
    escaped = str(escape(text))
    return _BOLD_RE.sub(r"<strong>\1</strong>", escaped)


def _is_price_line(line):
    return bool(_PRICE_RE.search(line))


def _looks_like_heading(line):
    """A short standalone line that labels what follows.

    Needs an emoji or a trailing colon - a short plain line such as
    "3 Days / 2 Nights" is a detail, not a section label.
    """
    emoji, text = _split_emoji(line)
    if not text:
        return False
    if text.endswith(":"):
        return True
    if not emoji or _is_price_line(text) or text.endswith((".", ",", ";")):
        return False
    return len(text.split()) <= 7


def _looks_like_detail(line):
    """A short plain fact on its own line, e.g. "3 Days / 2 Nights"."""
    emoji, text = _split_emoji(line)
    # Sentence punctuation anywhere means it's prose ("Relax by the sea.
    # Explore the island."), not a fact like "3 Days / 2 Nights".
    return (not emoji and not _is_price_line(text) and len(text.split()) <= 6
            and not any(ch in text for ch in ".!?:"))


# Section names admin commonly uses. A line matching one is always a
# label, even when there's no blank line separating it from a list above.
_SECTION_WORDS = (
    "package details", "package inclusions", "inclusions", "inclusion",
    "exclusions", "exclusion", "highlights", "itinerary", "what you can see",
    "what to expect", "things to do", "rates", "package rates", "hotel options",
    "tour details", "notes", "reminders", "requirements",
)


def _is_section_name(line):
    _, text = _split_emoji(line)
    key = text.rstrip(":").strip().lower()
    return any(key == w or key.startswith(w + " ") for w in _SECTION_WORDS)


def _parse_price(line):
    _, text = _split_emoji(line)
    match = _PRICE_RE.search(text)
    amount = match.group(0).strip()
    # A "+" right before the price marks an extra fee, e.g. "Oct 26 - Nov 5 (+USD 100)".
    addon = text[:match.start()].rstrip().endswith("+")
    per_person = "per person" in text.lower() or "per pax" in text.lower()
    parts = _DASH_RE.split(text, maxsplit=1)
    # "Hotel - P6,999" splits on the dash only when the price starts the right side.
    if len(parts) == 2 and not _PRICE_RE.search(parts[0]) and _PRICE_RE.match(parts[1].lstrip("(+ ")):
        label = parts[0].strip()
    else:
        label = text[:match.start()].rstrip().rstrip("+") + text[match.end():]
        label = re.sub(r"(?i)per\s+(person|pax)", "", label)
        label = re.sub(r"\(\s*\)", "", label).strip(" :—–-")
    if addon:
        amount = "+" + amount
    return {"label": label, "amount": amount, "per_person": per_person, "addon": addon}


def _blocks(text):
    """Split into blocks of consecutive non-empty lines."""
    blocks, current = [], []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if line:
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _classify(blocks):
    """Turn blocks into a flat list of typed items."""
    items = []
    for bi, block in enumerate(blocks):
        if bi == 0:
            items.append(("headline", block[0]))
            if len(block) > 1:
                items.append(("para", "\n".join(block[1:])))
            continue
        if len(block) == 1 and (_looks_like_heading(block[0]) or _is_section_name(block[0])):
            items.append(("heading", block[0]))
            continue
        if len(block) == 1 and _looks_like_detail(block[0]):
            items.append(("detail", block[0]))
            continue
        # Lines inside one block are handled individually so a block can
        # mix, say, price lines with an emoji bullet.
        para_buf = []
        def flush():
            if para_buf:
                items.append(("para", "\n".join(para_buf)))
                para_buf.clear()

        for line in block:
            emoji, _ = _split_emoji(line)
            if _is_section_name(line):
                flush()
                items.append(("heading", line))
            elif _looks_like_detail(line) and len(block) > 1:
                flush()
                items.append(("detail", line))
            elif _is_price_line(line):
                if para_buf:
                    items.append(("para", "\n".join(para_buf)))
                    para_buf = []
                items.append(("price", line))
            elif emoji:
                if para_buf:
                    items.append(("para", "\n".join(para_buf)))
                    para_buf = []
                items.append(("bullet", line))
            else:
                para_buf.append(line)
        if para_buf:
            items.append(("para", "\n".join(para_buf)))
    return items


def _render_label(line):
    _, text = _split_emoji(line)
    text = text.rstrip(":").strip()
    return f'<div class="rd-label"><span>{_inline(text)}</span></div>'


def _render_paragraph(text, cls="rd-para"):
    lines = [_inline(line) for line in text.split("\n")]
    return f'<p class="{cls}">{"<br>".join(lines)}</p>'


def _render_bullets(lines, as_chips):
    if as_chips:
        chips = "".join(f'<span class="rd-chip">{_inline(_split_emoji(line)[1])}</span>' for line in lines)
        return f'<div class="rd-chips">{chips}</div>'
    cards = []
    for line in lines:
        emoji, text = _split_emoji(line)
        cards.append(
            f'<div class="rd-card"><span class="rd-icon" aria-hidden="true">{escape(emoji)}</span>'
            f'<span class="rd-card-text">{_inline(text)}</span></div>'
        )
    return f'<div class="rd-cards">{"".join(cards)}</div>'


def _price_unit(p):
    """Small note under a price: "per person", "additional fee", or both."""
    notes = []
    if p["addon"]:
        notes.append("additional fee")
    if p["per_person"]:
        notes.append("per person")
    return f'<span class="rd-unit">{" ".join(notes)}</span>' if notes else ""


def _render_prices(lines):
    prices = [_parse_price(line) for line in lines]
    if len(prices) == 1:
        p = prices[0]
        label = _inline(p["label"]) if p["label"] else "Price"
        return (
            f'<div class="rd-price-row"><span class="rd-price-label">{label}</span>'
            f'<span class="rd-price-amount">{escape(p["amount"])} {_price_unit(p)}</span></div>'
        )
    cards = "".join(
        f'<div class="rd-hotel"><div class="rd-hotel-name">{_inline(p["label"]) if p["label"] else "Option"}</div>'
        f'<div class="rd-hotel-price">{escape(p["amount"])}</div>'
        f'{_price_unit(p)}</div>'
        for p in prices
    )
    return f'<div class="rd-hotels">{cards}</div>'


def format_description(text):
    """Render a plain-text package description as structured HTML."""
    if not text or not text.strip():
        return Markup("")

    items = _classify(_blocks(text))

    # The last heading becomes a closing callout when only paragraphs follow
    # it - e.g. "Your Boracay escape awaits!" plus a sign-off.
    closing_at = None
    for i in range(len(items) - 1, -1, -1):
        if items[i][0] == "heading":
            if all(kind in ("para", "detail") for kind, _ in items[i + 1:]) and i + 1 < len(items):
                closing_at = i
            break

    out = []
    in_inclusions = False
    i = 0
    while i < len(items):
        kind, value = items[i]

        if closing_at is not None and i == closing_at:
            _, heading_text = _split_emoji(value)
            body = "".join(_render_paragraph(v, "rd-closing-text") for _, v in items[i + 1:])
            out.append(
                f'<div class="rd-closing"><p class="rd-closing-title">{_inline(heading_text)}</p>{body}</div>'
            )
            break

        if kind == "headline":
            out.append(f'<h3 class="rd-headline">{_inline(value)}</h3>')
            # The first paragraph after the headline is the intro.
            if i + 1 < len(items) and items[i + 1][0] == "para":
                out.append(_render_paragraph(items[i + 1][1], "rd-intro"))
                i += 2
                continue
        elif kind == "heading":
            in_inclusions = "inclusion" in value.lower()
            out.append(_render_label(value))
        elif kind == "para":
            out.append(_render_paragraph(value))
        elif kind == "detail":
            out.append(f'<span class="rd-detail">{_inline(value)}</span>')
        elif kind in ("bullet", "price"):
            # Gather the whole run of the same kind into one grid or list.
            run = [value]
            while i + 1 < len(items) and items[i + 1][0] == kind:
                i += 1
                run.append(items[i][1])
            if kind == "price":
                out.append(_render_prices(run))
            else:
                out.append(_render_bullets(run, as_chips=in_inclusions))
        i += 1

    return Markup(f'<div class="rich-desc">{"".join(out)}</div>')
