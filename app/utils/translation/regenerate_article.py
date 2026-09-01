"""
Ollama service for handling communication with Ollama container
Manages all interactions with the Ollama translation service with HTML preservation
"""
import re
from typing import List
from utils.translation.tokenizer import AyaTokenizer
from bs4 import BeautifulSoup, Tag
import logging
# 1. Configure the logger to accept INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BLOCK_TAGS = {
    "p", "div", "section", "article", "blockquote", "span",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "pre", "code", "table", "thead", "tbody", "tr", "th", "td",
    "ul", "ol", "li", "hr", "figure", "figcaption"
}

INLINE_TAGS = {
    "strong", "b", "em", "i", "u", "s"
}

STRUCTURAL_TAGS = {"hr", "figure"}

IMAGE_TAGS = {"img"}
ANCHOR_TAGS = {"a"}

ALLOWED_HTML_TAGS = {
    "p", "div", "section", "article", "blockquote", "span",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "pre", "code", "table", "thead", "tbody", "tr", "th", "td",
    "ul", "ol", "li", "hr", "figure", "figcaption", "strong", "b", "em", "i", "u", "s", "hr", "figure", "img", "a"}

class RegenerateArticle:
    """Service class for translating HTML content while preserving structure using Ollama LLM"""

    def __init__(self):
        self.index = 0
    def reconstruct_html_from_structure(self, translated_segments: list[dict[str, str]] ) -> str:
        """
        Reconstruct HTML from structure map with translated text
        
        Args:
            translated_segments: List of translated text segments
            
        Returns:
            HTML with translated content and preserved structure
        """
        html_parts: dict[int, str] = {}
        self.index = 0
        try:
            for segment in translated_segments:
                if segment["tag"] in BLOCK_TAGS or segment["tag"] in INLINE_TAGS:
                    tag = segment["tag"]
                    text = segment["text"]
                    html_part = f"<{tag}>{text}</{tag}>"
                    html_parts[self.index] = html_part
                    self.index += 1
                if segment["tag"] not in BLOCK_TAGS and segment["tag"] not in INLINE_TAGS and segment["tag"] not in ANCHOR_TAGS :
                    tag = segment["tag"]
                    src = segment.get("src", "")
                    alt = segment.get("alt", "")
                    html_part = f'<{tag} src="{src}" alt="{alt}" />'
                    html_parts[self.index] = html_part
                    self.index += 1
                if segment["tag"] not in BLOCK_TAGS and segment["tag"] not in INLINE_TAGS and segment["tag"] not in IMAGE_TAGS :
                    tag = segment["tag"]
                    text = segment["text"]
                    href = segment.get("href", "")
                    html_part = f'<{tag} href="{href}">{text}</{tag}>'
                    html_parts[self.index] = html_part
                    self.index += 1

            print(f"DEBUG: Reconstructed HTML: {html_parts}")
            return ''.join(html_parts.values())
            
        except Exception as e:
            print(f"DEBUG: Error in reconstruct_html_from_structure: {e}")
            return ''.join(html_parts.values())  # Return what we have so far
    def split_html_into_chunks(self, html: str, max_tokens: int = 2000) -> List[str]:
        """
        Split HTML content into smaller chunks for translation.
        
        Strategy:
        1. By tokens using AyaTokenizer, accumulating complete blocks of allowed tags to preserve structure as much as possible.
        2. Split by <div> tags. And later will be by `max_tokens`.
        3. If still too large, fall back to character-based splitting at tag boundaries.

        Args:
            html: Full HTML content to split
            max_tokens: Maximum tokens per chunk

        Returns:
            List of HTML chunks ready for translation
        """
        logger.info("DEBUG: Preparing to split HTML into chunks...")
        self.tokenizer = AyaTokenizer()
        logger.info("==Splitting HTML into chunks with self.tokenizer=%s", self.tokenizer)
        self.max_tokens = max_tokens
        logger.info("==Parsing HTML content with BeautifulSoup (max_tokens=%s)", self.max_tokens)
        soup = BeautifulSoup(html, 'html.parser')  # type: ignore

        # Get top-level children to preserve document flow (use getattr to satisfy type-checkers)
        # body = getattr(soup, 'body', None)
        # if body is not None:
        #     top_level = list(getattr(body, 'children', []))
        #     logger.info("=====Found <body> tag, using its children for chunking")
        # else:
        #     top_level = list(getattr(soup, 'children', []))
        #     logger.info("===No <body> tag found, using top-level children for chunking")

        # Walk only top-level block elements so nested tags (e.g. <strong> inside <p>)
        # are not collected as separate blocks — avoids duplicate content in chunks.
        root = soup.body if soup.body else soup
        blocks: List[str] = []
        for el in root.children:  # type: ignore
            if isinstance(el, Tag) and el.name in ALLOWED_HTML_TAGS:
                logger.info("Adding top-level tag <%s> to blocks for chunking", el.name)
                blocks.append(str(el))

        chunks: List[str] = []
        current_blocks: List[str] = []
        current_tokens = 0
        for block in blocks:
            tokens = self.tokenizer.count(block)
            if current_tokens + tokens > self.max_tokens:
                # chunks.append(self._wrap(current_blocks))
                current_blocks = [block]
                current_tokens = tokens
            else:
                current_blocks.append(block) # type: ignore
                current_tokens += tokens

        if current_blocks:
            chunks.append(self._wrap(current_blocks)) # type: ignore

        return chunks


        # flush_buffer()

        # # Final cleanup: strip and return
        # return [c.strip() for c in final_chunks if c.strip()]

    def _parse_numbered_translation(self, translation_response: str, expected_count: int) -> List[str]:
        """
        Parse numbered translation response back to list of segments
        """
        segments: List[str] = []
        lines = translation_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Match patterns like "1. text" or "1) text" or "1- text"
            match = re.match(r'^\d+[\.\)\-]\s*(.+)', line)
            if match:
                segments.append(match.group(1).strip())
            elif line and not re.match(r'^\d+[\.\)\-]', line):
                # If line doesn't start with number but has content, might be continuation
                if segments:  # Add to last segment if exists
                    segments[-1] += " " + line
        
        # Ensure we have expected number of segments
        while len(segments) < expected_count:
            segments.append("")  # Add empty segments if missing
        
        return segments[:expected_count]  # Trim if too many

# Global service instance
regenerate_article_service = RegenerateArticle()
