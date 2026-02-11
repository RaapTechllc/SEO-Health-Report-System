"""DFY artifact generators for automated fixes."""

from .meta_tags import generate_meta_tags
from .robots_txt import generate_robots_txt
from .schema_markup import generate_schema_markup
from .sitemap import generate_sitemap_xml

__all__ = [
    "generate_robots_txt",
    "generate_meta_tags",
    "generate_schema_markup",
    "generate_sitemap_xml",
]
