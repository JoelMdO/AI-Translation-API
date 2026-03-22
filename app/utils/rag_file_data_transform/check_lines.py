import pymupdf, re

doc = pymupdf.open('vocabularioAeroEI.pdf')
lines = []
for page in doc:
    for line in page.get_text().splitlines():
        s = line.strip()
        if not s: continue
        if re.match(r'^[A-Z]$', s): continue
        if re.match(r'^\d+$', s): continue
        if 'VOCABULARIO' in s.upper() or 'INGLÉS' in s.upper(): continue
        lines.append(s)

print(f'Total lines: {len(lines)}, remainder: {len(lines) % 3}')
print('Last 10 lines:')
for l in lines[-10:]:
    print(repr(l))
