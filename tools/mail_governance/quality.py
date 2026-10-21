"""Conservative visible-structure checks, not semantic JD or person-fit verification.

The character floors only reject trivial citations. Reviewers remain responsible
for the factual company briefing, complete role and substantive candidate fit.
This static parser does not substitute for a browser's computed CSS/layout.
"""
import re
from html import unescape
from html.parser import HTMLParser


CONTENT_FLOORS = {"company": 40, "role": 40, "personalization": 24}
BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "blockquote",
              "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
             "meta", "param", "source", "track", "wbr"}
INVISIBLE_TAGS = {"script", "style", "template", "head", "title", "noscript"}


def compact(text):
    return re.sub(r"\s+", " ", text).strip()


def character_count(text):
    return sum(character.isalnum() for character in text)


def hidden_node(tag, attrs):
    attrs = dict(attrs)
    style = re.sub(r"/\*.*?\*/", "", attrs.get("style") or "", flags=re.S)
    style = re.sub(r"\s+", "", style).casefold()
    invisible_style = re.search(r"(?:^|;)(?:display:none|visibility:(?:hidden|collapse)|opacity:0(?:\.0*)?|font-size:0(?:px|em|rem|pt)?)(?:!important)?(?:;|$)", style)
    return (tag in INVISIBLE_TAGS or "hidden" in attrs or "inert" in attrs
            or (attrs.get("aria-hidden") or "").casefold() == "true" or bool(invisible_style))


class VisibleBlocks(HTMLParser):
    def __init__(self, source, start, end):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.start, self.end = start, end
        self.line_starts = [0] + [match.end() for match in re.finditer("\n", source)]
        self.stack = []
        self.current = []
        self.blocks = []

    def blocked(self):
        return bool(self.stack and self.stack[-1][1])

    def flush(self):
        text = compact("".join(self.current))
        if text:
            self.blocks.append(text)
        self.current = []

    def handle_starttag(self, tag, attrs):
        suppressed = self.blocked() or hidden_node(tag, attrs)
        if not suppressed and (tag in BLOCK_TAGS or tag in {"br", "hr"}):
            self.flush()
        if tag not in VOID_TAGS:
            self.stack.append((tag, suppressed))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                if tag in BLOCK_TAGS and not self.blocked():
                    self.flush()
                del self.stack[index:]
                return

    def handle_data(self, data):
        if not self.blocked():
            offset = self.absolute_offset()
            start, end = max(offset, self.start), min(offset + len(data), self.end)
            if start < end:
                self.current.append(data[start - offset:end - offset])

    def absolute_offset(self):
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def reference(self, prefix, name):
        offset = self.absolute_offset()
        end = offset + len(prefix) + len(name)
        if self.source[end:end + 1] == ";":
            end += 1
        if not self.blocked() and self.start <= offset and end <= self.end:
            self.current.append(unescape(self.source[offset:end]))

    def handle_entityref(self, name):
        self.reference("&", name)

    def handle_charref(self, name):
        self.reference("&#", name)


def visible_content(message, evidence):
    source = message[evidence["representation"]]
    if evidence["representation"] == "authored_text":
        blocks = [compact(line) for line in evidence["quote"].splitlines() if line.strip()]
    else:
        # Citation offsets restrict emitted text, never the surrounding DOM.
        parser = VisibleBlocks(source, evidence["start"], evidence["end"])
        parser.feed(parser.source)
        parser.close()
        parser.flush()
        blocks = parser.blocks
    return compact(" ".join(blocks)), blocks


def golden_structure(message, axes):
    """Reject trivial/invisible evidence and introductions below the JD body."""
    layout = axes["layout"]["evidence"]
    if not layout:
        return False
    visible_layout, blocks = visible_content(message, layout)
    if sum(character_count(block) >= 12 for block in blocks) < 3:
        return False
    positions = {}
    for axis, floor in CONTENT_FLOORS.items():
        evidence = axes[axis]["evidence"]
        if not evidence:
            return False
        quote, _ = visible_content(message, evidence)
        if character_count(quote) < floor or quote not in visible_layout:
            return False
        positions[axis] = visible_layout.index(quote)
    return positions["personalization"] < min(positions["company"], positions["role"])
