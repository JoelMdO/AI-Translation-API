"""
Extract service for handling communication with the extraction logic
Manages all interactions with the extraction service with HTML preservation
"""

from bs4 import NavigableString, Tag
from bs4 import BeautifulSoup
import logging
# 1. Configure the logger to accept INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BLOCK_TAGS = {
    "p", "div", "section", "article", "blockquote", "span",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "pre", "code", "table", "thead", "tbody", "tr", "th", "td",
    "ul", "ol", "li", "img", "hr", "figure", "figcaption", "a"
}

INLINE_TAGS = {
    "strong", "b", "em", "i", "u", "s"
}

STRUCTURAL_TAGS = {"img", "hr", "figure", "figcaption"}

class ExtractText:
    """Service class for extracting text from HTML content by the LLM"""

    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.timeout = 960.0
        self.model = "llama3.2"
    

    async def extract_article_structure(self, html: str) -> list[dict[str, str]]: # type: ignore
        # Use Python's built-in parser so extraction does not require the
        # optional lxml package at runtime.
        soup = BeautifulSoup(html, "html.parser")
        root = soup.body or soup

        blocks = []
        paragraph_id = 1
          # Initialize paragraph_id for unique identification of text nodes

        def walk_block(el): # type: ignore
            """Convert a block element into a paragraph-like structure."""
            tag = el.name.lower() # type: ignore

            # structural elements
            if tag == "img":
                return { # type: ignore
                    "type": "image", 
                    "tag": tag,
                    "src": el.get("src"), # type: ignore
                    "alt": el.get("alt", "") # type: ignore
                }

            if tag == "hr":
                return {"type": "separator","tag": tag,}

            # list items
            if tag in ["ul", "ol"]:
                return { # type: ignore
                    "type": "list",
                    "tag": tag,
                    "items": [walk_block(li) for li in el.find_all("li", recursive=False)] # type: ignore
                }

            if tag == "li":
                return { # type: ignore
                    "type": "listItem",
                    "tag": tag,
                    "content": walk_inline_children(el, parent_tag=tag) # type: ignore
                }

            # code blocks
            if tag in ["pre", "code"]:
                return { # type: ignore
                    "type": "code",
                    "tag": tag,
                    "text": el.get_text("\n", strip=True) # type: ignore
                }

            # headings, paragraphs, divs, sections
            if tag in BLOCK_TAGS:
                return { # type: ignore
                    "type": "paragraph",
                    "tag": tag,
                    "content": walk_inline_children(el, parent_tag=tag) # type: ignore
                }

            return None


        def walk_inline_children(el, parent_tag=None): # type: ignore
            """Extract inline content inside a block."""
            content = []

            for child in el.children: # type: ignore
                if isinstance(child, NavigableString):
                    text = child.strip()
                    if text:
                        content.append({ # type: ignore
                            "type": "text",
                            "tag": parent_tag,
                            "text": text
                        })
                    continue

                if isinstance(child, Tag):
                    tag = child.name.lower()

                    # inline formatting
                    if tag in INLINE_TAGS:
                        content.append({ # type: ignore
                            "type": "formatted",
                            "tag": tag,
                            "content": walk_inline_children(child, parent_tag=tag)
                        })
                        continue

                    # nested block inside block → treat as paragraph
                    if tag in BLOCK_TAGS:
                        print(" ???? Nested block detected: %s inside %s" % (tag, parent_tag), flush=True)
                        content.append(walk_block(child)) # type: ignore
                        continue

                    # fallback: recurse
                    content.extend(walk_inline_children(child, parent_tag=tag)) # type: ignore

            return content # type: ignore


        def collect_text_nodes(blocks): # type: ignore
            texts = []
           

            def walk(node):  # type: ignore
                # If it's a text node, collect it
                nonlocal paragraph_id
                if node.get("type") == "text":  # type: ignore
                    print("======FOUND TEXT NODE:=====", node.get("text", ""), flush=True) # type: ignore
                    texts.append({"id": paragraph_id, "tag": node.get("tag"), "text": node.get("text", "")}) # type: ignore
                    paragraph_id += 1

                if node.get("tag") in {"img"}: # type: ignore
                    print("======FOUND IMG  NODE:=====", node.get("tag"), flush=True) # type: ignore
                    texts.append({"id": paragraph_id, "tag": node.get("tag"), "src": node.get("src", ""), "alt": node.get("alt", "")}) # type: ignore
                    print(f"//IMG NODE: Added structural node with: {node}", flush=True)
                    paragraph_id += 1
                if node.get("tag") in {"a"}: # type: ignore
                    print("======FOUND A NODE:=====", node.get("tag"), flush=True) # type: ignore
                    texts.append({"id": paragraph_id, "tag": node.get("tag"), "href": node.get("href", "")}) # type: ignore
                    print(f"//Anchor NODE: Added structural node with: {node}", flush=True)
                    paragraph_id += 1
                if node.get("tag") in {"hr"}: # type: ignore
                    print("======FOUND HR NODE:=====", node.get("tag"), flush=True) # type: ignore
                    texts.append({"id": paragraph_id, "tag": node.get("tag")}) # type: ignore
                    print(f"//HR NODE: Added structural node with: {node}", flush=True)
                    paragraph_id += 1               
                # If it has children/content, recurse
                if "content" in node and isinstance(node["content"], list):
                    for child in node["content"]: # type: ignore
                        walk(child) # type: ignore

                # Lists have "items"
                if "items" in node and isinstance(node["items"], list):
                    for child in node["items"]: # type: ignore
                        walk(child) # type: ignore

                # If it's a list of nodes
                elif isinstance(node, list):
                    for child in node: # type: ignore
                        walk(child) # type: ignore

            walk(blocks) # type: ignore
            print("======COLLECTED TEXT NODES:=====", texts, flush=True) # type: ignore
            return texts # type: ignore



        # Walk only top-level blocks. Nested blocks are already traversed by
        # walk_inline_children(), so using root.descendants here would process
        # those same blocks a second time.
        for el in root.children: # type: ignore
            if isinstance(el, Tag) and el.name.lower() in BLOCK_TAGS:
                block = walk_block(el) # type: ignore
                print("======WALKED BLOCK:=====", block, flush=True) # type: ignore
                if block:
                    text_nodes = collect_text_nodes(block) # type: ignore
                    blocks.extend(text_nodes) # type: ignore
        return blocks# type: ignore
