#!/usr/bin/env python3
import json
import re
from pathlib import Path

IN = Path('API/app/data/abbreviation.json')
OUT = Path('API/app/data/abbreviation_fixed.json')
SUG = Path('API/app/data/abbreviation_suggested_fixes.json')
AMB = Path('API/app/data/abbreviation_ambiguous.json')

ACRO_RE = re.compile(r'^[A-Z0-9-]{1,6}$')

# small Spanish corrections map
SPANISH_FIXES = {
    'Pasjero': 'Pasajero'
}

with IN.open('r', encoding='utf-8') as f:
    data = json.load(f)

suggested = []
ambiguous = []
fixed = []

for i, item in enumerate(data):
    a = (item.get('abbreviation') or '').strip()
    e = (item.get('english') or '').strip()
    s = (item.get('spanish') or '').strip()

    # quick clean of leading non-ascii glyphs
    a_clean = re.sub(r'^\W+','', a).strip()
    a_clean = re.sub(r'\s*\(IATA\)|\s*\(ICAO\)', '', a_clean)

    # apply Spanish typo fixes
    for k,v in SPANISH_FIXES.items():
        if k in s:
            s = s.replace(k, v)

    # If abbreviation looks valid, keep but ensure english/spanish not swapped
    if ACRO_RE.match(a_clean):
        fixed.append({'abbreviation': a_clean, 'english': e, 'spanish': s})
        continue

    # If abbreviation is phrase (likely swapped), search for acronym in english/spanish
    e_is_acro = ACRO_RE.match(e)
    s_is_acro = ACRO_RE.match(s)

    # Decide candidate acronym
    candidate = None
    source = None
    if s_is_acro and not e_is_acro:
        candidate = s
        source = 'spanish'
    elif e_is_acro and not s_is_acro:
        candidate = e
        source = 'english'
    elif s_is_acro and e_is_acro:
        # both acronyms — ambiguous
        ambiguous.append({'index': i, 'original': item, 'note': 'Both english and spanish look like acronyms'})
        fixed.append(item)
        continue
    else:
        # neither looks like acronym — attempt to extract uppercase acronym from any field
        for fld in (a, e, s):
            m = re.search(r'([A-Z]{2,6})', fld)
            if m:
                candidate = m.group(1)
                break

    if candidate:
        # Determine probable english/spanish phrases
        # If original abbreviation (a) contains accented chars or common Spanish words, treat as spanish phrase
        if re.search(r'[áéíóúÁÉÍÓÚñÑ]', a) or any(w in a.lower() for w in ['plano','ruta','sistema','equipo','servicio','zona','grupo','autónomo','autónoma','procesamiento','notificación']):
            new_english = e if not ACRO_RE.match(e) else a.title()
            new_spanish = a
        else:
            # assume a is English phrase
            new_english = a
            # if english field contains Spanish (accents) then use it as spanish
            if re.search(r'[áéíóúÁÉÍÓÚñÑ]', e) or any(w in e.lower() for w in ['plano','ruta','sistema','equipo','servicio','zona','grupo']):
                new_spanish = e
            else:
                new_spanish = s
        corrected = {'abbreviation': candidate, 'english': new_english, 'spanish': new_spanish}
        suggested.append({'index': i, 'original': item, 'corrected': corrected, 'reason': f'Promoted {candidate} to abbreviation from {source or "detected"}'})
        fixed.append(corrected)
    else:
        ambiguous.append({'index': i, 'original': item, 'note': 'No clear acronym candidate found'})
        fixed.append(item)

# Write outputs
OUT.write_text(json.dumps(fixed, ensure_ascii=False, indent=2))
SUG.write_text(json.dumps(suggested, ensure_ascii=False, indent=2))
AMB.write_text(json.dumps(ambiguous, ensure_ascii=False, indent=2))

print(f'Processed {len(data)} entries. Suggested fixes: {len(suggested)}. Ambiguous: {len(ambiguous)}. Output: {OUT}')
