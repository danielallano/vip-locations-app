# VTC Locations Content Generator

Location page content generator for VIP Medical Group brands.

## What it does

- Generates SEO-optimized text content for location pages
- Supports 8 brands: VTC, VIP Medical Group, PTS, Vein Treatment, Venas Varices, TX/LI/CA regional sites
- Two page types: Open location and Coming Soon
- Uses GPT-4o-mini to fill in location-specific details (neighborhoods, directions, context)
- Clean Bootstrap 5 UI with copy-to-clipboard per brand

## Brands

| ID | Brand | Domain | Type |
|----|-------|--------|------|
| vtc | Vein Treatment Clinic | veintreatmentclinic.com | Main |
| vip | VIP Medical Group | vipmedicalgroup.com | Main |
| pts | Pain Treatment Specialists | paintreatmentspecialists.com | Main |
| veintreatment | Vein Treatment | veintreatment.com | Microsite |
| venasvarices | Venas Varices (ES) | venasvarices.com | Microsite |
| veintreatmenttx | Vein Treatment TX | veintreatmenttx.com | Regional |
| veincliniclongisland | Vein Clinic Long Island | veincliniclongisland.com | Regional |
| veincentersca | Vein Centers CA | veincentersca.com | Regional |

## Run locally

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
uvicorn main:app --host 0.0.0.0 --port 8007 --reload
```

## Deploy

Deployed at: https://sophia.vipmedicalgroup.ai/vtc-locations/
Port: 8007
Systemd service: vtc-locations

## Structure

```
vtc-locations-app/
├── main.py              # FastAPI backend
├── requirements.txt
├── templates/
│   ├── brands.py        # Brand configs & templates
│   └── __init__.py
└── static/
    └── index.html       # Frontend UI
```
