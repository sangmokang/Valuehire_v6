"""Conservative visible-structure checks, not semantic JD or person-fit verification.

The character floors only reject trivial citations. Reviewers remain responsible
for the factual company briefing, complete role and substantive candidate fit.
This static parser does not substitute for a browser's computed CSS/layout.
Its supported dialect excludes foreign/custom elements, media fallbacks, ruby,
and table captions/header/footer groups. Tables require explicit rows/cells
(optionally a tbody); unsupported source context rejects HTML evidence.
"""
import re
from html import unescape
from html.parser import HTMLParser


CONTENT_FLOORS = {"company": 40, "role": 40, "personalization": 24}
BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "blockquote",
              "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
             "meta", "param", "source", "track", "wbr"}
INVISIBLE_TAGS = {"script", "style", "template", "head", "title", "noscript",
                  "datalist", "rp", "noembed", "noframes", "iframe"}
# Support and visibility are separate decisions: known hidden elements remain
# supported so their bodies are suppressed, while unknown syntax fails closed.
SUPPORTED_TAGS = {
    "html", "head", "title", "body", "base", "link", "meta", "style", "script",
    "noscript", "template", "datalist", "rp", "noembed", "noframes", "iframe",
    "article", "section", "main", "aside", "nav", "header", "footer", "address",
    "blockquote", "div", "p", "pre", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "abbr", "b", "bdi", "bdo", "br", "cite", "code", "data", "del", "dfn",
    "em", "i", "ins", "kbd", "mark", "q", "s", "samp", "small", "span", "strong",
    "sub", "sup", "time", "u", "var", "wbr", "font", "center", "img", "hr",
    "ul", "ol", "li", "dl", "dt", "dd", "menu", "details", "summary", "dialog",
    "table", "tbody", "tr", "td", "th",
}
TABLE_CHILDREN = {"table": {"tbody", "tr"}, "tbody": {"tr"}, "tr": {"td", "th"}}
TABLE_PARENTS = {"tbody": {"table"}, "tr": {"table", "tbody"}, "td": {"tr"}, "th": {"tr"}}
DOCUMENT_PARENTS = {"html": {None}, "head": {None, "html"}, "body": {None, "html"}}
LEADING_METADATA_TAGS = {"base", "link", "meta", "title", "style", "script", "noscript", "template"}
# Only these ordinary omitted paragraph/list endings are accepted across a
# closing ancestor. Other crossing closes need browser tree repair we do not
# implement, so they cannot establish visible Golden evidence.
PARAGRAPH_CONTAINERS = {"address", "article", "aside", "blockquote", "div", "footer",
                        "header", "li", "main", "nav", "section", "td", "th"}


def compact(text):
    return re.sub(r"\s+", " ", text).strip()


def character_count(text):
    return sum(character.isalnum() for character in text)


def hidden_node(tag, attrs):
    attrs = dict(attrs)
    style = re.sub(r"/\*.*?\*/", "", attrs.get("style") or "", flags=re.S)
    style = re.sub(r"\s+", "", style).casefold()
    zero = r"[+-]?(?:0+(?:\.0+)?|\.0+)(?:e[+-]?[0-9]+)?"
    invisible_style = re.search(r"(?:^|;)(?:display:none|visibility:(?:hidden|collapse)|opacity:" + zero
                               + r"%?|font-size:" + zero + r"(?:px|cm|mm|q|in|pt|pc|r?(?:em|ex|cap|ch|ic|lh)|[sld]?v(?:w|h|i|b|min|max)|%)?)(?:!important)?(?:;|$)", style)
    # Closed disclosures/dialogs cannot establish visible body evidence without interaction.
    return (tag in INVISIBLE_TAGS or "hidden" in attrs or "inert" in attrs
            or (tag == "details" and "open" not in attrs)
            or (tag == "dialog" and "open" not in attrs)
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
        self.ambiguous_structure = False
        self.document_tags = set()
        self.body_started = False
        self.script_tail = ""

    def blocked(self):
        return bool(self.stack and self.stack[-1][1])

    def flush(self):
        text = compact("".join(self.current))
        if text:
            self.blocks.append(text)
        self.current = []

    def handle_starttag(self, tag, attrs):
        if tag not in SUPPORTED_TAGS:
            self.ambiguous_structure = True
        if tag == "script":
            self.script_tail = ""
        parent = self.stack[-1][0] if self.stack else None
        if tag in DOCUMENT_PARENTS:
            # Browsers merge late html/body attributes into earlier ancestors.
            # Support each wrapper once, before body content, in its normal scope.
            if tag in self.document_tags or self.body_started or parent not in DOCUMENT_PARENTS[tag]:
                self.ambiguous_structure = True
            self.document_tags.add(tag)
            self.body_started = self.body_started or tag == "body"
        elif tag not in LEADING_METADATA_TAGS:
            self.body_started = True
        if parent in TABLE_CHILDREN and tag not in TABLE_CHILDREN[parent]:
            self.ambiguous_structure = True
        if tag in TABLE_PARENTS and parent not in TABLE_PARENTS[tag]:
            self.ambiguous_structure = True
        if len({name for name, _ in attrs}) != len(attrs):
            self.ambiguous_structure = True
        suppressed = self.blocked() or hidden_node(tag, attrs)
        if not suppressed and (tag in BLOCK_TAGS or tag in {"br", "hr"}):
            self.flush()
        if tag not in VOID_TAGS:
            self.stack.append((tag, suppressed))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            # HTML ignores the self-closing flag on ordinary nonvoid elements.
            # Foreign-content handling is outside this conservative parser.
            self.ambiguous_structure = True
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag not in SUPPORTED_TAGS:
            self.ambiguous_structure = True
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                allowed = {"p"} if tag in PARAGRAPH_CONTAINERS else set()
                if tag in {"ul", "ol", "menu"}:
                    allowed = {"li", "p"}
                elif tag == "dl":
                    allowed = {"dt", "dd", "p"}
                if any(open_tag not in allowed for open_tag, _ in self.stack[index + 1:]):
                    self.ambiguous_structure = True
                if tag in BLOCK_TAGS and not self.blocked():
                    self.flush()
                del self.stack[index:]
                return

    def handle_data(self, data):
        if self.stack and self.stack[-1][0] == "script":
            # Script escaping changes browser end-tag handling; it is outside
            # this dialect. Keep the delimiter prefix across raw-data callbacks.
            raw = self.script_tail + data
            if "<!--" in raw:
                self.ambiguous_structure = True
            self.script_tail = raw[-3:]
        self.check_table_text(data)
        if not self.blocked():
            if data.strip(" \t\n\r\f"):
                self.body_started = True
            offset = self.absolute_offset()
            start, end = max(offset, self.start), min(offset + len(data), self.end)
            if start < end:
                self.current.append(data[start - offset:end - offset])

    def check_table_text(self, data):
        # HTML's table whitespace excludes NBSP and other Unicode spaces.
        if self.stack and self.stack[-1][0] in TABLE_CHILDREN and data.strip(" \t\n\r\f"):
            self.ambiguous_structure = True

    def absolute_offset(self):
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def reference(self, prefix, name):
        offset = self.absolute_offset()
        end = offset + len(prefix) + len(name)
        if self.source[end:end + 1] == ";":
            end += 1
        text = unescape(self.source[offset:end])
        self.check_table_text(text)
        if not self.blocked() and text.strip(" \t\n\r\f"):
            self.body_started = True
        if not self.blocked() and self.start <= offset and end <= self.end:
            self.current.append(text)

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
        blocks = [] if parser.ambiguous_structure else parser.blocks
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
