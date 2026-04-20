import sys
sys.path.insert(0, '.')

from utils.translation.translate_html_utils import TranslateHTMLUtils
from utils.sanitize_html import sanitize_html

# Test 1: split_html_into_chunks keeps all tag types
html = '<div><p>Para one.</p><blockquote>A quote.</blockquote><ol><li>Item A</li></ol><h2>Heading.</h2><hr/><p>Last.</p></div>'
chunks = TranslateHTMLUtils().split_html_into_chunks(html, max_chars=5000)
full = ' '.join(chunks)
print("blockquote present:", 'A quote.' in full)
print("ol/li present:", 'Item A' in full)
print("h2 present:", 'Heading.' in full)
print("last p present:", 'Last.' in full)

# Test 2: sanitize_html enforces allowlist
dirty = '<p>Hello</p><style>.bad{}</style><strong>world</strong>'
clean = sanitize_html(dirty)
print("p kept:", '<p>' in clean)
print("strong kept:", '<strong>' in clean)
print("style stripped:", 'style' not in clean)
print("text preserved:", 'Hello' in clean and 'world' in clean)
