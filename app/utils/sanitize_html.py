import re
def sanitize_html(html: str) -> str:
                # Remove <script> and other dangerous tags, but keep safe HTML structure
                # Simple regex-based removal for <script> and event handlers
                html = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', html, flags=re.DOTALL|re.IGNORECASE)
                # Remove on* event handlers (e.g., onclick, onerror)
                html = re.sub(r'on\w+\s*=\s*"[^"]*"', '', html, flags=re.IGNORECASE)
                html = re.sub(r'on\w+\s*=\s*\'[^\']*\'', '', html, flags=re.IGNORECASE)
                html = re.sub(r'on\w+\s*=\s*[^ >]+', '', html, flags=re.IGNORECASE)
                # Remove javascript: in href/src
                html = re.sub(r'(href|src)\s*=\s*"javascript:[^"]*"', '', html, flags=re.IGNORECASE)
                html = re.sub(r'(href|src)\s*=\s*\'javascript:[^\']*\'', '', html, flags=re.IGNORECASE)
                return html