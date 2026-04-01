import re
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
                return html