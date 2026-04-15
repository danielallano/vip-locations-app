"""
Brand templates for VIP Medical Group location content generator.
Each brand has its own template for Open and Coming Soon page types.
AI fills in: neighborhoods, directions description, local context.
"""

BRANDS = {
    "vtc": {
        "name": "VTC - Vein Treatment Clinic",
        "domain": "veintreatmentclinic.com",
        "phone": "(844) 690-1788",
        "specialty": "vein",
        "language": "en",
        "type": "main",
        "treatments": [
            "Ultrasound-guided sclerotherapy",
            "Radiofrequency Ablation (RFA)",
            "Endovenous Laser Treatment (EVLT)",
            "Ambulatory phlebectomy",
            "Spider vein sclerotherapy",
        ],
        "conditions": [
            "Varicose veins",
            "Spider veins",
            "Chronic venous insufficiency",
            "Leg swelling and heaviness",
            "Leg pain and cramping",
        ],
        "trust_points": [
            "Ivy League-trained, board-certified vein specialists",
            "Minimally invasive, outpatient procedures",
            "Most insurances accepted — we verify coverage for you",
            "State-of-the-art facilities and diagnostic technology",
            "Compassionate, patient-centered care",
        ],
    },
    "vip": {
        "name": "VIP Medical Group",
        "domain": "vipmedicalgroup.com",
        "phone": "844-297-2300",
        "specialty": "vein_pain",
        "language": "en",
        "type": "main",
        "treatments": [
            "Sclerotherapy for spider veins",
            "Radiofrequency Ablation (RFA)",
            "Endovenous Laser Treatment (EVLT)",
            "Pain management consultations",
            "Minimally invasive spine treatments",
        ],
        "conditions": [
            "Varicose veins",
            "Spider veins",
            "Chronic venous insufficiency",
            "Back pain",
            "Spine conditions",
        ],
        "trust_points": [
            "Ivy League-trained, board-certified specialists",
            "Comprehensive vein and pain care under one roof",
            "Most insurances accepted",
            "Minimally invasive, outpatient procedures",
            "Convenient locations across the Northeast and beyond",
        ],
    },
    "pts": {
        "name": "Pain Treatment Specialists",
        "domain": "paintreatmentspecialists.com",
        "phone": "844-597-0492",
        "specialty": "pain",
        "language": "en",
        "type": "main",
        "treatments": [
            "Epidural steroid injections",
            "Nerve block procedures",
            "Minimally invasive spine treatments",
            "Radiofrequency ablation for pain",
            "Facet joint injections",
        ],
        "conditions": [
            "Chronic back pain",
            "Sciatica",
            "Spine conditions",
            "Joint pain",
            "Nerve pain",
        ],
        "trust_points": [
            "Harvard-trained, fellowship-certified pain specialists",
            "Non-surgical, minimally invasive approach",
            "Most insurances accepted",
            "State-of-the-art pain management techniques",
            "Personalized treatment plans",
        ],
    },
    "veintreatment": {
        "name": "Vein Treatment",
        "domain": "veintreatment.com",
        "phone": "(855) 699-2004",
        "specialty": "vein",
        "language": "en",
        "type": "microsite",
        "treatments": [
            "Sclerotherapy",
            "Radiofrequency Ablation (RFA)",
            "Endovenous Laser Treatment (EVLT)",
            "Ambulatory phlebectomy",
            "Ultrasound-guided vein mapping",
        ],
        "conditions": [
            "Varicose veins",
            "Spider veins",
            "Chronic venous insufficiency",
            "Leg heaviness",
            "Vein disease",
        ],
        "trust_points": [
            "Board-certified vein specialists",
            "Minimally invasive, same-day treatments",
            "Insurance coverage verified",
            "Modern facilities and equipment",
            "Expert diagnosis and personalized care",
        ],
    },
    "venasvarices": {
        "name": "Venas Varices",
        "domain": "venasvarices.com",
        "phone": "(844) 690-1788",
        "specialty": "vein",
        "language": "es",
        "type": "microsite",
        "treatments": [
            "Escleroterapia guiada por ultrasonido",
            "Ablación por radiofrecuencia (RFA)",
            "Tratamiento láser endovenoso (EVLT)",
            "Flebectomía ambulatoria",
            "Escleroterapia para arañas vasculares",
        ],
        "conditions": [
            "Várices",
            "Arañas vasculares (telangiectasias)",
            "Insuficiencia venosa crónica",
            "Hinchazón y pesadez en las piernas",
            "Dolor y calambres en las piernas",
        ],
        "trust_points": [
            "Especialistas certificados formados en universidades de élite",
            "Procedimientos mínimamente invasivos y ambulatorios",
            "Aceptamos la mayoría de los seguros médicos",
            "Tecnología de diagnóstico de vanguardia",
            "Atención personalizada y compasiva",
        ],
    },
    "veintreatmenttx": {
        "name": "Vein Treatment TX",
        "domain": "veintreatmenttx.com",
        "phone": "(844) 690-1788",
        "specialty": "vein",
        "language": "en",
        "type": "regional",
        "region": "Texas",
        "treatments": [
            "Sclerotherapy",
            "Radiofrequency Ablation (RFA)",
            "Laser vein treatment",
            "Spider vein removal",
        ],
        "conditions": [
            "Varicose veins",
            "Spider veins",
            "Venous insufficiency",
            "Leg pain",
        ],
        "trust_points": [
            "Board-certified Texas vein specialists",
            "Minimally invasive treatments",
            "Insurance accepted",
            "Convenient Texas locations",
        ],
    },
    "veincliniclongisland": {
        "name": "Vein Clinic Long Island",
        "domain": "veincliniclongisland.com",
        "phone": "(844) 690-1788",
        "specialty": "vein",
        "language": "en",
        "type": "regional",
        "region": "Long Island, New York",
        "treatments": [
            "Sclerotherapy",
            "Radiofrequency Ablation (RFA)",
            "Laser vein treatment",
            "Spider vein removal",
        ],
        "conditions": [
            "Varicose veins",
            "Spider veins",
            "Venous insufficiency",
            "Leg heaviness",
        ],
        "trust_points": [
            "Long Island's leading vein specialists",
            "Minimally invasive treatments",
            "Insurance accepted",
            "Convenient Long Island locations",
        ],
    },
    "veincentersca": {
        "name": "Vein Centers CA",
        "domain": "veincentersca.com",
        "phone": "(844) 690-1788",
        "specialty": "vein",
        "language": "en",
        "type": "regional",
        "region": "California",
        "treatments": [
            "Sclerotherapy",
            "Radiofrequency Ablation (RFA)",
            "Laser vein treatment",
            "Spider vein removal",
        ],
        "conditions": [
            "Varicose veins",
            "Spider veins",
            "Venous insufficiency",
            "Leg swelling",
        ],
        "trust_points": [
            "California's trusted vein specialists",
            "Minimally invasive treatments",
            "Insurance accepted",
            "Convenient California locations",
        ],
    },
}


def get_brand(brand_id: str) -> dict:
    """Get brand config by ID."""
    return BRANDS.get(brand_id)


def list_brands() -> list:
    """List all brands with basic info."""
    return [
        {"id": k, "name": v["name"], "domain": v["domain"], "type": v["type"], "language": v.get("language", "en")}
        for k, v in BRANDS.items()
    ]
