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


def replace_review_html(message, review, html):
    message["html"] = html
    message["source_hash"] = review["content_hash"] = content_hash(message["authored_text"], html)
    for axis in ("personalization", "company", "role"):
        quote = review["golden_axes"][axis]["evidence"]["quote"]
        review["golden_axes"][axis]["evidence"] = citation(html, quote, "html")
    review["golden_axes"]["layout"]["evidence"] = citation(html, html, "html")


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

    def test_crossing_inline_close_cannot_release_a_hidden_block_ancestor(self):
        for block in ("div", "section", "article", "ul", "p"):
            with self.subTest(block=block):
                opening = "<span style='display:none'><" + block + "></span>"
                message, review, _ = html_review(opening, "</" + block + ">")
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_nested_crossing_closes_cannot_release_hidden_inline_context(self):
        opening = "<span hidden><section><div></span>"
        message, review, _ = html_review(opening, "</div></section>")
        self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_ordinary_omitted_paragraph_ends_remain_visible_with_partial_entity_citations(self):
        message, review, fragment = html_review("<article>", "</article>", entity_intro=True)
        html = message["html"].replace("</p>", "")
        message["html"] = html
        message["source_hash"] = review["content_hash"] = content_hash(message["authored_text"], html)
        for axis in ("personalization", "company", "role"):
            quote = review["golden_axes"][axis]["evidence"]["quote"]
            review["golden_axes"][axis]["evidence"] = citation(html, quote, "html")
        review["golden_axes"]["layout"]["evidence"] = citation(html, fragment.replace("</p>", ""), "html")
        self.assertTrue(classify(message, review)["is_golden_sample"])

    def test_nonvoid_self_closing_tags_cannot_release_hidden_context(self):
        for tag, attributes in (("span", " hidden"), ("div", " style='display:none'"),
                                ("section", " hidden"), ("script", ""), ("style", "")):
            with self.subTest(tag=tag):
                message, review, _ = html_review("<" + tag + attributes + "/>", "</" + tag + ">")
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_void_self_closing_images_and_breaks_do_not_hide_later_evidence(self):
        message, review, _ = html_review(
            "<article><img hidden src='synthetic.png'/><br/>", "</article>", entity_intro=True)
        self.assertTrue(classify(message, review)["is_golden_sample"])

    def test_duplicate_attributes_make_html_visibility_ambiguous(self):
        for attributes in ("STYLE='display:none' style='display:block'",
                           "style='opacity:0' style='opacity:1'",
                           "aria-hidden='true' aria-hidden='false'",
                           "class='first' class='second'"):
            with self.subTest(attributes=attributes):
                message, review, _ = html_review("<div " + attributes + ">", "</div>")
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_closed_details_body_is_not_visible_including_nested_disclosures(self):
        wrappers = (("<details>", "</details>"),
                    ("<details open><details>", "</details></details>"),
                    ("<details><details open>", "</details></details>"))
        for opening, closing in wrappers:
            with self.subTest(wrapper=opening):
                message, review, _ = html_review(opening + "<summary>채용 안내</summary>", closing)
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_explicitly_open_details_body_remains_visible(self):
        for opening, closing in (("<details open>", "</details>"),
                                 ("<details open=''>", "</details>"),
                                 ("<details open='false'>", "</details>"),
                                 ("<details open><details open>", "</details></details>")):
            with self.subTest(wrapper=opening):
                message, review, _ = html_review(opening + "<summary>채용 안내</summary>", closing,
                                               entity_intro=True)
                self.assertTrue(classify(message, review)["is_golden_sample"])

    def test_default_hidden_html_elements_cannot_establish_visible_evidence(self):
        # Chromium 155 local synthetic rendering: the first three have no text
        # rectangles; fallback/raw-text contents of the others are not rendered.
        for opening, closing in (("<dialog>", "</dialog>"),
                                 ("<datalist>", "</datalist>"),
                                 ("<ruby><rp>", "</rp></ruby>"),
                                 ("<noembed>", "</noembed>"),
                                 ("<noframes>", "</noframes>"),
                                 ("<iframe>", "</iframe>")):
            with self.subTest(wrapper=opening):
                message, review, _ = html_review(opening, closing)
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_explicitly_open_dialog_and_ordinary_content_remain_visible(self):
        for opening, closing in (("<dialog open>", "</dialog>"),
                                 ("<dialog open=''>", "</dialog>"),
                                 ("<dialog open='false'>", "</dialog>"),
                                 ("<section>", "</section>")):
            with self.subTest(wrapper=opening):
                message, review, _ = html_review(opening, closing, entity_intro=True)
                self.assertTrue(classify(message, review)["is_golden_sample"])

    def test_hidden_raw_text_citations_reject_even_with_visible_duplicate_layout(self):
        # The visible duplicate supplies three real blocks; hidden evidence
        # cannot rely on the block-count check to reject fallback text.
        for tag in ("noembed", "noframes", "iframe"):
            with self.subTest(tag=tag):
                _, _, fragment = html_review()
                prefix = "<" + tag + ">" + fragment + "</" + tag + ">"
                message, review, _ = html_review(prefix)
                start = len(prefix)
                review["golden_axes"]["layout"]["evidence"] = {
                    "representation": "html", "start": start,
                    "end": start + len(fragment), "quote": fragment,
                }
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_unsupported_media_foreign_and_custom_elements_are_not_golden_evidence(self):
        for opening, closing in (("<audio>", "</audio>"),
                                 ("<audio controls>", "</audio>"),
                                 ("<video controls>", "</video>"),
                                 ("<canvas>", "</canvas>"), ("<object>", "</object>"),
                                 ("<select>", "</select>"), ("<svg>", "</svg>"),
                                 ("<math>", "</math>"), ("<unknown>", "</unknown>"),
                                 ("<candidate-card>", "</candidate-card>")):
            with self.subTest(wrapper=opening):
                message, review, fragment = html_review()
                html = opening + fragment.replace("<p>", "<section>").replace("</p>", "</section>") + closing
                replace_review_html(message, review, html)
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_unsupported_elements_outside_citations_make_source_ambiguous(self):
        for tag in ("unknown", "candidate-card", "svg", "math", "canvas", "select", "object"):
            with self.subTest(tag=tag):
                message, review, _ = html_review("<" + tag + "></" + tag + ">")
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_table_foster_parenting_cannot_move_intro_below_the_jd(self):
        message, review, _ = html_review()
        intro, company, role = [review["golden_axes"][axis]["evidence"]["quote"]
                                for axis in ("personalization", "company", "role")]
        html = ("<table><tr><td><p>" + intro + "</p></td></tr><p>" + company
                + "</p><p>" + role + "</p></table>")
        replace_review_html(message, review, html)
        self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_nonwhitespace_data_directly_inside_table_cannot_be_fostered(self):
        message, review, _ = html_review()
        intro, company, role = [review["golden_axes"][axis]["evidence"]["quote"]
                                for axis in ("personalization", "company", "role")]
        html = ("<table><tbody><tr><td><p>" + intro + "</p></td></tr>" + company
                + "<tr><td><p>" + role + "</p></td></tr></tbody></table>")
        replace_review_html(message, review, html)
        self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_table_sections_that_reorder_rendering_are_outside_supported_dialect(self):
        for opening, closing in (("<table><caption>표 안내</caption><tr><td>", "</td></tr></table>"),
                                 ("<table><thead><tr><th>", "</th></tr></thead></table>"),
                                 ("<table><tfoot><tr><td>", "</td></tr></tfoot></table>")):
            with self.subTest(wrapper=opening):
                message, review, _ = html_review(opening, closing)
                self.assertFalse(classify(message, review)["is_golden_sample"])

    def test_normal_table_body_preserves_intro_order_and_partial_entity_citations(self):
        for body_start, body_end in (("", ""), ("<tbody>", "</tbody>")):
            with self.subTest(tbody=body_start):
                message, review, fragment = html_review(entity_intro=True)
                html = ("<table>\n" + body_start + fragment.replace("<p>", "<tr><td><p>")
                        .replace("</p>", "</p></td></tr>\n") + body_end + "</table>")
                replace_review_html(message, review, html)
                self.assertTrue(classify(message, review)["is_golden_sample"])


if __name__ == "__main__":
    unittest.main()
