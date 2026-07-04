import logging
import re

import markdown as md
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MarkdownService:
    def __init__(self):
        self.md = md.Markdown(
            extensions=[
                "fenced_code",
                "codehilite",
                "tables",
                "toc",
                "attr_list",
                "def_list",
                "footnotes",
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "use_pygments": True,
                },
            },
        )

    def to_html(self, markdown_text: str) -> str:
        html = self.md.convert(markdown_text)
        return self._sanitize_for_beehiiv(html)

    def _sanitize_for_beehiiv(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.find_all(True):
            attrs_to_keep = {}
            if tag.name == "a":
                href = tag.get("href")
                if href:
                    attrs_to_keep["href"] = href
                title = tag.get("title")
                if title:
                    attrs_to_keep["title"] = title
            elif tag.name == "img":
                src = tag.get("src")
                if src:
                    attrs_to_keep["src"] = src
                alt = tag.get("alt")
                if alt:
                    attrs_to_keep["alt"] = alt
                width = tag.get("width")
                if width:
                    attrs_to_keep["width"] = width
                height = tag.get("height")
                if height:
                    attrs_to_keep["height"] = height
            elif tag.name in ("code", "pre"):
                class_attr = tag.get("class")
                if class_attr:
                    attrs_to_keep["class"] = " ".join(class_attr) if isinstance(class_attr, list) else class_attr

            tag.attrs = attrs_to_keep

        for tag in soup.find_all(["script", "style", "iframe", "form", "input", "button"]):
            tag.decompose()

        return str(soup)

    def extract_excerpt(self, markdown_text: str, max_length: int = 200) -> str:
        html = self.to_html(markdown_text)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "..."
        return text

    def generate_slug(self, title: str, max_length: int = 60) -> str:
        slug = title.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s-]+", "-", slug)
        slug = slug.strip("-")
        if len(slug) > max_length:
            slug = slug[:max_length].rsplit("-", 1)[0]
        return slug


markdown_service = MarkdownService()
