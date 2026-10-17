#!/usr/bin/env python3
"""Apply the unchanged legacy publication transform to reconstructed sources."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'deploy'))
from reader_views import transform_reading_page

stage=ROOT/'tmp/reading-notes-migration'
metadata=json.loads((stage/'legacy-files.json').read_text())
for record in json.loads((stage/'source-pages.json').read_text()):
    route=record['route']
    raw=(stage/'canonical'/route).read_bytes()
    output=transform_reading_page(raw,route,metadata['document_views'],csapp_pdf_included=(stage/'legacy/csapp/csapp.pdf').is_file())
    path=stage/'prepared'/route
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(output)
