# Knowledge Corpus – TODO

## Purpose
This folder contains the RAG (Retrieval-Augmented Generation) knowledge base that the
CleanBreath AI chat agent searches when answering user questions.  Each document is
chunked into 300–500 token segments, embedded with Gemini `text-embedding-004`, and
stored in Supabase `pgvector`.

## Documents Still Required (obtain from official sources only)

| Priority | Document | Source | Status |
|----------|----------|--------|--------|
| P0 | WHO Global Air Quality Guidelines 2021 (full PDF) | who.int | ⬜ Placeholder |
| P0 | CPCB National Air Quality Index (NAQI) 2014 | cpcb.nic.in | ⬜ Placeholder |
| P0 | India NAQI Health Advisories by Category | CPCB/MoEFCC | ⬜ Placeholder |
| P0 | CDC N95 respirator guidance (2023) | cdc.gov | ⬜ Placeholder |
| P1 | USEPA Particulate Matter Health Effects | epa.gov | ⬜ Placeholder |
| P1 | Corsi-Rosenthal Box study – Bliss et al. 2021 | preprint | ⬜ Placeholder |
| P1 | AHAM air purifier CADR standards (AC-1-2015) | aham.org | ⬜ Placeholder |
| P1 | WHO Household Air Pollution guidelines 2014 | who.int | ⬜ Placeholder |
| P2 | TERI Household energy and air quality study | teriin.org | ⬜ Placeholder |
| P2 | IPCC AR6 WG3 Chapter 10 (transport emissions) | ipcc.ch | ⬜ Placeholder |
| P2 | CEA Grid Emission Factor 2022-23 | cea.nic.in | ⬜ Placeholder |
| P2 | Delhi DTC fleet emission data | dtc.nic.in | ⬜ Placeholder |

## How to Ingest

```bash
cd backend
python scripts/ingest_knowledge.py --input ../knowledge/ --lang en
```

The script chunks each `.md` file at paragraph boundaries (target ~400 tokens),
calls `google.generativeai.embed_content` with model `text-embedding-004`,
and upserts into `knowledge_chunks` with `doc_id`, `source_org`, `source_url`,
`published_year`, and `language` fields parsed from the YAML front-matter.

## Markdown Front-Matter Format

```yaml
---
doc_id: who_aqg_2021
title: "WHO Global Air Quality Guidelines 2021"
source_org: "World Health Organization"
source_url: "https://www.who.int/publications/i/item/9789240034228"
published_year: 2021
language: en
---
```
