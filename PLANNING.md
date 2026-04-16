---
title: VTC Location Content App
type: project
status: planning
created: 2026-04-15
updated: 2026-04-15
tags:
  - project
  - vip
  - locations
  - content
---

# VTC Location Content App

**Purpose:** Generate location-specific content pages for all VIP Medical Group brands

## Brands & Templates

### Main Brands
1. **VIP Medical Group** (vipmedicalgroup.com)
   - Open: https://www.vipmedicalgroup.com/locations/texas/addison
   - Coming Soon: https://www.vipmedicalgroup.com/locations/new-york/williamsburg/

2. **VTC - Vein Treatment Clinic** (veintreatmentclinic.com)
   - Open: https://www.veintreatmentclinic.com/locations/new-york/midtown
   - Coming Soon: https://www.veintreatmentclinic.com/locations/texas/spring-branch/

3. **PTS - Pain Treatment Specialists** (paintreatmentspecialists.com)
   - Optional per location (not all locations have PTS)
   - Templates exist, needs examples documented

### Vein Treatment (regional)
4. veintreatment.com
5. veintreatmentca.com (California)
6. veintreatmentli.com (Long Island)
7. veintreatmentsmd.com (Maryland)
8. veintreatmentnj.com (New Jersey)
9. veintreatmentnyc.com (NYC)
10. veintreatmentsd.com (San Diego)
11. veintreatmenttx.com (Texas)
12. veintreatmentsct.com (Connecticut)

### Vein Centers (regional)
13. veincentersca.com (California)
14. veincentersct.com (Connecticut)
15. veincentersli.com (Long Island)
16. veincentersmd.com (Maryland)
17. veincentersnj.com (New Jersey)
18. veincentersny.com (New York)
19. veincenterstx.com (Texas)
20. paveincenters.com (PA)

### Vein Clinics (regional)
21. veinclinicsca.com (California)
22. veinclinicsct.com (Connecticut)
23. veinclinicsmd.com (Maryland)
24. veinclinicsnj.com (New Jersey)
25. veinclinicsny.com (New York)
26. veincliniclongisland.com (Long Island)
27. paveinclinics.com (PA)

### Other
28. veindoctor.com
    - Open: https://www.veindoctor.com/new-jersey/clifton/
    - Coming Soon: Same pattern, add "Coming Soon" to title
    - Note: different URL structure (no /locations/ prefix)
29. venasvarices.com (Spanish language)
    - Open: https://venasvarices.com/ubicaciones/maryland/bethesda/
31. legulcercenter.com
    - Examples TBD (Dani to send — reminder set for Apr 16 11am COT)

### Example URLs Collected
- VIP Open: https://www.vipmedicalgroup.com/locations/texas/addison
- VIP Coming Soon: https://www.vipmedicalgroup.com/locations/new-york/williamsburg/
- VTC Open: https://www.veintreatmentclinic.com/locations/new-york/midtown
- VTC Coming Soon: https://www.veintreatmentclinic.com/locations/texas/spring-branch/
- Vein Treatment (national) Open: https://www.veintreatment.com/locations/new-york/astoria/
- Vein Treatment (national) Open #2: https://www.veintreatment.com/locations/pennsylvania/center-city/
- Vein Treatment TX Open: https://www.veintreatmenttx.com/locations/texas/cedar-park/
- Vein Centers CA Open: https://www.veincentersca.com/locations/california/murrieta/
- Vein Clinic LI Open: https://www.veincliniclongisland.com/locations/long-island/north-shore/
- Vein Doctor Open: https://www.veindoctor.com/new-jersey/clifton/
- Venas Varices Open: https://venasvarices.com/ubicaciones/maryland/bethesda/

## Key Requirements
- Each brand has its own template/style
- Two page types: **Open** and **Coming Soon**
- VTC Editorial v2 was narrowed to blog content only — this app handles locations
- Follow existing templates closely (lots of working examples to match)
- PTS appears as optional toggle (not all locations have PTS)
- **UX Flow:** Step 1 = enter address + select websites (checkboxes) → Step 2 = tabbed output per site
- App should auto-suggest relevant sites based on state/region entered, but allow manual override
- Sites within same group (treatment/centers/clinics) share the same template
- **Doctor input: optional** — sometimes available, sometimes not
- **30 total websites** across all brands
- Coming Soon pages = same as Open but with "Coming Soon" in the title

## Unique Templates Needed (~8-9)
1. VIP Medical Group
2. VTC (Vein Treatment Clinic)
3. PTS (Pain Treatment Specialists)
4. Vein Treatment (regional group — all share same template)
5. Vein Centers (regional group — all share same template)
6. Vein Clinics (regional group — all share same template)
7. Vein Doctor (unique URL structure, no /locations/ prefix)
8. Venas Varices (Spanish)
9. Leg Ulcer Center (TBD)

## UX Design
**Step 1 — Input**
- Address field
- Doctor name field (optional)
- Open / Coming Soon toggle
- Website checkboxes grouped: VIP → VTC → PTS → Treatment → Centers → Clinics → Other
- Auto-suggest sites based on state, manual override allowed

**Step 2 — Output**
- Tabs per selected site
- Each tab: generated content + meta tags (title + description)
- Per-tab actions: Copy to clipboard
- Download per tab: .doc, .txt, .html, .json
- Bulk export: .csv (all sites in one file), .json (all sites), or ZIP of individual files
- "Download All" button for batch export

## Status
- Discussed Apr 10-16
- All examples collected except legulcercenter.com (reminder set Apr 16 11am COT)
- Templates need crawling/extraction
- App not yet built
