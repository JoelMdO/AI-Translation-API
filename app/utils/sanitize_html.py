import re
from utils.translation.translate_html_utils import ALLOWED_HTML_TAGS

# Pre-build the negative-lookahead pattern once at import time for efficiency.
# Sort longest-first so the alternation engine matches greedily (avoids 's' matching
# the start of 'script', 'strong', etc. before the \b word-boundary check fires).
_ALLOWED_TAGS_PATTERN = '(?:' + '|'.join(sorted(ALLOWED_HTML_TAGS, key=len, reverse=True)) + ')'

def sanitize_html(html: str) -> str:
                # Remove <script> tags and their content
                html = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', html, flags=re.DOTALL|re.IGNORECASE)
                # Remove <iframe> tags and their content (including self-closing)
                html = re.sub(r'<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>', '', html, flags=re.DOTALL|re.IGNORECASE)
                html = re.sub(r'<\s*iframe[^>]*/?\s*>', '', html, flags=re.IGNORECASE)
                # Remove on* event handlers (e.g., onclick, onerror)
                html = re.sub(r'on\w+\s*=\s*"[^"]*"', '', html, flags=re.IGNORECASE)
                html = re.sub(r'on\w+\s*=\s*\'[^\']*\'', '', html, flags=re.IGNORECASE)
                html = re.sub(r'on\w+\s*=\s*[^ >]+', '', html, flags=re.IGNORECASE)
                # Remove javascript: in href/src attributes
                html = re.sub(r'(href|src)\s*=\s*"javascript:[^"]*"', '', html, flags=re.IGNORECASE)
                html = re.sub(r'(href|src)\s*=\s*\'javascript:[^\']*\'', '', html, flags=re.IGNORECASE)
                # Remove data: URIs in src attributes (potential XSS vector)
                html = re.sub(r'src\s*=\s*"data:[^"]*"', '', html, flags=re.IGNORECASE)
                html = re.sub(r"src\s*=\s*'data:[^']*'", '', html, flags=re.IGNORECASE)
                # Remove javascript: occurrences embedded in style attributes (CSS injection)
                html = re.sub(r'(style\s*=\s*"[^"]*?)javascript:[^"]*', r'\1', html, flags=re.IGNORECASE)
                html = re.sub(r"(style\s*=\s*'[^']*?)javascript:[^']*", r'\1', html, flags=re.IGNORECASE)
                # Strip any tag NOT in the allowlist while preserving its inner content.
                # The negative lookahead combined with a word boundary ensures 'strong', 'span',
                # etc. are kept while 'style', 'object', 'embed', 'form', etc. are removed.
                html = re.sub(
                    r'</?(?!' + _ALLOWED_TAGS_PATTERN + r'\b)[a-zA-Z][a-zA-Z0-9]*(?:\s[^>]*)?>',
                    '',
                    html,
                    flags=re.IGNORECASE,
                )
                return html