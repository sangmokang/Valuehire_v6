"""Evidence offsets must retain the visibility context of their source HTML."""
import unittest

from tools.mail_governance.core import classify, content_hash
from tools.mail_governance.test_input_regressions import citation, rich_fixture


def html_review(prefix="", suffix="", *, entity_intro=False):
    message, review = rich_fixture()
    texts = {axis: review["golden_axes"][axis]["evidence"]["quote"]
             for axis in ("personalization", "company", "role")}
    if entity_intro:
        texts["personalization"] = texts["personalization"].replace("API", "API &amp; 데이터")
    fragment = "".join("<p>" + text + "</p>" for text in texts.values())
    html = prefix + fragment + suffix
    message["html"] = html
    message["source_hash"] = review["content_hash"] = content_hash(message["authored_text"], html)
    for axis, text in texts.items():
        review["golden_axes"][axis]["evidence"] = citation(html, text, "html")
    review["golden_axes"]["layout"]["evidence"] = citation(html, fragment, "html")
    return message, review, fragment


class VisibilityContextRegressions(unittest.TestCase):
    def test_numeric_zero_inline_styles_cannot_make_hidden_evidence_golden(self):
        for property_name, values in (
            ("font-size", ("0", "0.0px", "0%", ".0em", "00.000rem", "+0pt", "-0.0px",
                           "0cm", "0in", "0pc", "0vw", "0vh", "0ch", "0ex", "0rlh", "0dvb")),
            ("opacity", ("0", "0.0", ".0", "0%", "00.00%", "+0.0", "-0%")),
        ):
            for value in values:
                with self.subTest(property=property_name, value=value):
                    message, review, _ = html_review(
                        f"<div style='{property_name}:{value}!important'>", "</div><p>hello</p>")
                    self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_nonzero_inline_styles_keep_visible_evidence_golden(self):
        for style in ("font-size:0.1px", "font-size:10px", "font-size:0.1cm", "opacity:.01", "opacity:1", "opacity:10%"):
            with self.subTest(style=style):
                message, review, _ = html_review(f"<div style='{style}'>", "</div><p>hello</p>")
                self.assertTrue(classify(message, review)["is_golden_sample"])

    def test_hidden_ancestor_cannot_be_omitted_from_all_html_citations(self):
        wrappers = (("<div hidden>", "</div>"),
                    ("<div style='display:none'>", "</div>"),
                    ("<section><div aria-hidden='true'>", "</div></section>"),
                    ("<div style='visibility:hidden'>", "</div>"))
        for opening, closing in wrappers:
            with self.subTest(wrapper=opening):
                message, review, _ = html_review(opening, closing + "<p>hello</p>")
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_comment_script_style_context_cannot_be_omitted_from_citations(self):
        for opening, closing in (("<!-- ", " -->"), ("<script>", "</script>"),
                                 ("<style>", "</style>"), ("<template>", "</template>")):
            with self.subTest(wrapper=opening):
                message, review, _ = html_review(opening, closing + "<p>hello</p>")
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_attribute_content_is_not_visible_html_evidence(self):
        message, review, _ = html_review('<div data-evidence="', '"></div><p>hello</p>')
        self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_each_hidden_content_axis_rejects_even_when_layout_has_visible_duplicate(self):
        for axis in ("personalization", "company", "role"):
            with self.subTest(axis=axis):
                message, review, _ = html_review()
                quote = review["golden_axes"][axis]["evidence"]["quote"]
                prefix = "<div hidden><p>" + quote + "</p></div>"
                message, review, _ = html_review(prefix)
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_visible_partial_html_citations_preserve_parent_context_and_entities(self):
        for entity_intro in (False, True):
            with self.subTest(entity_intro=entity_intro):
                message, review, _ = html_review(
                    "<section><p>소개</p><div>", "</div><p>마무리</p></section>",
                    entity_intro=entity_intro)
                self.assertTrue(classify(message, review)["is_golden_sample"])


if __name__ == "__main__":
    unittest.main()
