#!/usr/bin/env python3
"""
VIP Medical Group - Location Content Generator
FastAPI backend for generating location page content across VIP brands.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import re
import openai
import sys

sys.path.insert(0, os.path.dirname(__file__))
from templates.brands import BRANDS, get_brand, list_brands

app = FastAPI(title="VIP Location Content Generator", version="1.0.0")

# OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set")
oai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


# ── Request/Response models ────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    address: str
    brand_ids: List[str]
    page_type: str  # "open" | "coming_soon"


class BrandContent(BaseModel):
    brand_id: str
    brand_name: str
    content: str
    meta_title: str
    meta_description: str


class GenerateResponse(BaseModel):
    address: str
    page_type: str
    results: List[BrandContent]


# ── AI helper ─────────────────────────────────────────────────────────────────

def get_location_context(address: str, brand: dict, page_type: str, language: str = "en") -> dict:
    """
    Call GPT-4o-mini to get location-specific content:
    - neighborhood_name: short neighborhood/area name
    - neighborhoods_list: 4-6 nearby neighborhoods/areas (comma-separated)
    - directions_paragraph: 2-3 sentence directions description
    - city: city name
    - state: state abbreviation
    - city_state: "City, ST" formatted
    - local_phrase: natural local context phrase (e.g. "in the heart of downtown")
    """
    specialty_desc = {
        "vein": "vein treatments (varicose veins, spider veins)",
        "pain": "pain management treatments (back pain, spine conditions)",
        "vein_pain": "vein and pain treatments (varicose veins, spider veins, back pain)",
    }.get(brand.get("specialty", "vein"), "medical treatments")

    lang_instruction = "Respond in Spanish." if language == "es" else "Respond in English."

    prompt = f"""
You are a medical marketing copywriter helping generate location-specific content for a healthcare website.

Given this address: {address}
Brand: {brand['name']} - specializing in {specialty_desc}
Page type: {"Opening soon (not yet open)" if page_type == "coming_soon" else "Open location"}

{lang_instruction}

Return a JSON object with these fields:
- "neighborhood_name": The specific neighborhood or area name (e.g. "Spring Branch" not "Houston")
- "city": City name only (e.g. "Houston")
- "state": State abbreviation (e.g. "TX")
- "city_state": "City, ST" format (e.g. "Houston, TX")
- "neighborhoods_list": Array of 4-6 nearby neighborhoods or areas patients might come from
- "directions_paragraph": 2-3 sentences describing how to reach this location (major roads, landmarks, transit if urban). Be specific and accurate.
- "local_phrase": A short phrase describing the location context (e.g. "in the heart of Midtown" or "along the Dallas North Tollway")
- "page_title_location": Location descriptor for page title (e.g. "Spring Branch, Houston, TX" or "Midtown Manhattan, New York, NY")

Only return valid JSON, no markdown, no extra text.
"""

    try:
        resp = oai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=600,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown if present
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)
    except Exception as e:
        # Fallback: parse address simply
        parts = address.split(",")
        city = parts[1].strip() if len(parts) > 1 else "your city"
        state = parts[2].strip().split()[0] if len(parts) > 2 else ""
        return {
            "neighborhood_name": parts[0].strip(),
            "city": city,
            "state": state,
            "city_state": f"{city}, {state}",
            "neighborhoods_list": ["the surrounding area", "nearby neighborhoods"],
            "directions_paragraph": f"Located at {address}, our clinic is conveniently accessible for patients throughout the area.",
            "local_phrase": f"in {city}",
            "page_title_location": f"{city}, {state}",
        }


# ── Content generators ────────────────────────────────────────────────────────

def build_content_vtc(brand: dict, address: str, page_type: str, ctx: dict) -> tuple[str, str, str]:
    """Build VTC-style content (main vein brand)."""
    brand_name = brand["name"]
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    city_state = ctx["city_state"]
    neighborhoods = "\n".join(f"- {n}" for n in ctx["neighborhoods_list"])
    directions = ctx["directions_paragraph"]
    local_phrase = ctx["local_phrase"]
    page_title_loc = ctx["page_title_location"]
    phone = brand["phone"]
    treatments_list = "\n".join(f"- {t}" for t in brand["treatments"])
    conditions_list = "\n".join(f"- {c}" for c in brand["conditions"])
    trust_list = "\n".join(f"- {t}" for t in brand["trust_points"])

    if page_type == "coming_soon":
        content = f"""# Spider & Varicose Vein Treatment in {page_title_loc}

**Address:** {address}

{brand_name} is expanding its network with a new clinic coming soon to {hood}, {city_state}. This location will provide specialized care for patients experiencing varicose veins, spider veins, and venous insufficiency, with appointments opening soon.

📞 **Call us to learn more or book your appointment in advance:** {phone}

---

## Your {brand_name} in {hood}, {city}

Our new clinic in {hood} is designed to provide convenient access to minimally invasive vein treatment for patients in:

{neighborhoods}

If you are searching for a vein doctor or vein clinic near you, this location will offer a nearby option for expert evaluation and treatment.

---

## Convenient Location {local_phrase}

{directions}

Additional directions and transportation details will be available once we open.

---

## Our Services — Personalized vein care, tailored to you

At our {hood} clinic, we provide a full range of services focused on diagnosing and treating vein disease:

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose {brand_name}

{trust_list}

---

## Opening Soon — Book Your Appointment

We're preparing to open in {hood}. In the meantime, call us to learn more or book your appointment in advance. Our other clinics are ready to welcome you now.

📞 **{phone}**

---

## Meta Tags

**Title:** {brand_name} in {hood} {city} | Opening Soon
**Meta description:** Opening soon in {hood}, {city_state}. {brand_name} treats varicose and spider veins with minimally invasive options. Schedule today.
"""
        meta_title = f"{brand_name} in {hood} {city} | Opening Soon"
        meta_desc = f"Opening soon in {hood}, {city_state}. {brand_name} treats varicose and spider veins with minimally invasive options like sclerotherapy and RFA. Schedule today."

    else:  # open
        content = f"""# Spider & Varicose Vein Treatment in {page_title_loc}

**Address:** {address}

Welcome to {brand_name} in {hood}, {city_state}. Our clinic provides expert, minimally invasive care for varicose veins, spider veins, and venous insufficiency — right {local_phrase}.

📞 **Call us or book your appointment:** {phone}

---

## Your Premier Vein Treatment Clinic in {hood}, {city}

Our {hood} clinic is designed to provide convenient access to the best vein care for patients throughout {city_state}:

{neighborhoods}

Whether you're searching for a vein doctor or looking to treat uncomfortable varicose or spider veins, our specialists are ready to help.

---

## Convenient Location {local_phrase}

{directions}

---

## Our Services — Personalized vein care, tailored to you

At our {hood} clinic, we provide a comprehensive range of vein treatment services:

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose {brand_name}

{trust_list}

---

## Book Your Appointment Today

Ready to get started? Our {hood} clinic is accepting new patients.

📞 **Call us:** {phone}

---

## Meta Tags

**Title:** {brand_name} in {hood} {city} | Expert Vein Treatment
**Meta description:** Expert vein treatment in {hood}, {city_state}. {brand_name} offers minimally invasive care for varicose and spider veins. Ivy League-trained specialists. Book today.
"""
        meta_title = f"{brand_name} in {hood} {city} | Expert Vein Treatment"
        meta_desc = f"Expert vein treatment in {hood}, {city_state}. {brand_name} offers minimally invasive care for varicose and spider veins. Board-certified specialists. Book today."

    return content, meta_title, meta_desc


def build_content_vip(brand: dict, address: str, page_type: str, ctx: dict) -> tuple[str, str, str]:
    """Build VIP Medical Group content (vein + pain)."""
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    city_state = ctx["city_state"]
    neighborhoods = "\n".join(f"- {n}" for n in ctx["neighborhoods_list"])
    directions = ctx["directions_paragraph"]
    local_phrase = ctx["local_phrase"]
    page_title_loc = ctx["page_title_location"]
    phone = brand["phone"]
    treatments_list = "\n".join(f"- {t}" for t in brand["treatments"])
    conditions_list = "\n".join(f"- {c}" for c in brand["conditions"])
    trust_list = "\n".join(f"- {t}" for t in brand["trust_points"])

    if page_type == "coming_soon":
        content = f"""# Vein & Pain Treatment in {page_title_loc}

**Address:** {address}

VIP Medical Group is preparing to open a new clinic in {hood}, {city_state}, bringing comprehensive vein and pain care to patients in the area. This location will offer minimally invasive treatments for varicose veins, spider veins, and chronic pain conditions.

📞 **Call us to learn more or book in advance:** {phone}

---

## VIP Medical Group Coming to {hood}, {city}

We're expanding to serve patients throughout {city_state}:

{neighborhoods}

---

## Convenient Location {local_phrase}

{directions}

Transportation and parking details will be available when we open.

---

## Our Services

At our {hood} clinic, we provide:

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose VIP Medical Group

{trust_list}

---

## Need to Be Seen Sooner?

Call us to learn more or book your appointment in advance at one of our existing locations.

📞 **{phone}**

---

## Meta Tags

**Title:** Vein Clinic Opening in {hood} {city} | VIP Medical Group
**Meta description:** New vein and pain clinic opening in {hood}, {city_state}. Convenient access for patients. Minimally invasive treatments by top specialists. Call {phone}.
"""
        meta_title = f"Vein Clinic Opening in {hood} {city} | VIP Medical Group"
        meta_desc = f"New vein and pain clinic opening in {hood}, {city_state}. Minimally invasive treatments by Ivy League-trained specialists. Call {phone}."

    else:
        content = f"""# Vein & Pain Treatment in {page_title_loc}

**Address:** {address}

VIP Medical Group in {hood}, {city_state} offers comprehensive care for vein and pain conditions. Our clinic is conveniently located {local_phrase}, serving patients across {city} and the surrounding area.

📞 **Call us or book an appointment:** {phone}

---

## Your VIP Medical Group Clinic in {hood}, {city}

We serve patients from:

{neighborhoods}

---

## Getting Here

{directions}

---

## Our Services

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose VIP Medical Group

{trust_list}

---

## Book Your Appointment

Our {hood} clinic is now accepting new patients.

📞 **{phone}**

---

## Meta Tags

**Title:** Vein Treatment in {hood}, {state} | Best Vein & Pain Doctors
**Meta description:** Vein & pain treatment in {hood}, {city_state}. Minimally invasive treatments at {address}. Book an appointment with our board-certified specialists today.
""".replace("{state}", ctx["state"])
        meta_title = f"Vein Treatment in {hood}, {ctx['state']} | Best Vein & Pain Doctors"
        meta_desc = f"Vein & pain treatment in {hood}, {city_state}. Minimally invasive treatments at {address}. Book an appointment today."

    return content, meta_title, meta_desc


def build_content_pts(brand: dict, address: str, page_type: str, ctx: dict) -> tuple[str, str, str]:
    """Build Pain Treatment Specialists content."""
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    city_state = ctx["city_state"]
    neighborhoods = "\n".join(f"- {n}" for n in ctx["neighborhoods_list"])
    directions = ctx["directions_paragraph"]
    local_phrase = ctx["local_phrase"]
    page_title_loc = ctx["page_title_location"]
    phone = brand["phone"]
    treatments_list = "\n".join(f"- {t}" for t in brand["treatments"])
    conditions_list = "\n".join(f"- {c}" for c in brand["conditions"])
    trust_list = "\n".join(f"- {t}" for t in brand["trust_points"])

    if page_type == "coming_soon":
        content = f"""# Pain Management in {page_title_loc}

**Address:** {address}

Pain Treatment Specialists is expanding to {hood}, {city_state}. Our new clinic will offer non-surgical, minimally invasive pain management for patients suffering from back pain, sciatica, and other chronic pain conditions.

📞 **Call us to learn more or book in advance:** {phone}

---

## Pain Treatment Specialists Coming to {hood}, {city}

Serving patients from:

{neighborhoods}

---

## Location Details

{directions}

---

## Our Services

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose Pain Treatment Specialists

{trust_list}

---

## Book in Advance

Our {hood} clinic is opening soon. Call now to get on the schedule.

📞 **{phone}**

---

## Meta Tags

**Title:** Pain Management Clinic Opening in {hood} {city} | Pain Treatment Specialists
**Meta description:** Pain Treatment Specialists coming soon to {hood}, {city_state}. Non-surgical pain management by Harvard-trained specialists. Book in advance.
"""
        meta_title = f"Pain Management Clinic Opening in {hood} {city} | Pain Treatment Specialists"
        meta_desc = f"Pain Treatment Specialists coming soon to {hood}, {city_state}. Non-surgical pain management by Harvard-trained specialists. Book in advance."
    else:
        content = f"""# Pain Management in {page_title_loc}

**Address:** {address}

Pain Treatment Specialists in {hood}, {city_state} provides comprehensive, non-surgical pain management care. Located {local_phrase}, our specialists treat chronic pain with minimally invasive techniques.

📞 **{phone}**

---

## Your Pain Clinic in {hood}, {city}

Serving patients from:

{neighborhoods}

---

## Getting Here

{directions}

---

## Our Services

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose Pain Treatment Specialists

{trust_list}

---

## Book Your Appointment

📞 **{phone}**

---

## Meta Tags

**Title:** Pain Management in {hood}, {ctx['state']} | Pain Treatment Specialists
**Meta description:** Non-surgical pain management in {hood}, {city_state}. Pain Treatment Specialists offers minimally invasive treatments for back pain, sciatica & more. Book today.
"""
        meta_title = f"Pain Management in {hood}, {ctx['state']} | Pain Treatment Specialists"
        meta_desc = f"Non-surgical pain management in {hood}, {city_state}. Pain Treatment Specialists offers minimally invasive treatments for back pain, sciatica & more. Book today."

    return content, meta_title, meta_desc


def build_content_venasvarices(brand: dict, address: str, page_type: str, ctx: dict) -> tuple[str, str, str]:
    """Build Spanish content for Venas Varices."""
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    city_state = ctx["city_state"]
    neighborhoods = "\n".join(f"- {n}" for n in ctx["neighborhoods_list"])
    directions = ctx["directions_paragraph"]
    local_phrase = ctx["local_phrase"]
    page_title_loc = ctx["page_title_location"]
    phone = brand["phone"]
    treatments_list = "\n".join(f"- {t}" for t in brand["treatments"])
    conditions_list = "\n".join(f"- {c}" for c in brand["conditions"])
    trust_list = "\n".join(f"- {t}" for t in brand["trust_points"])

    if page_type == "coming_soon":
        content = f"""# Tratamiento de Várices y Arañas Vasculares en {page_title_loc}

**Dirección:** {address}

Venas Varices pronto abrirá una nueva clínica en {hood}, {city_state}. Esta ubicación ofrecerá atención especializada para pacientes con várices, arañas vasculares e insuficiencia venosa.

📞 **Llámenos para más información o para reservar su cita con anticipación:** {phone}

---

## Su Clínica de Venas Varices en {hood}, {city}

Nuestra nueva clínica en {hood} estará diseñada para brindar acceso conveniente a pacientes de:

{neighborhoods}

---

## Ubicación conveniente

{directions}

Los detalles de cómo llegar estarán disponibles próximamente.

---

## Nuestros Servicios

{treatments_list}

---

## Condiciones que Tratamos

{conditions_list}

---

## ¿Por qué elegirnos?

{trust_list}

---

## Abrimos Pronto — Reserve su Cita

📞 **{phone}**

---

## Meta Tags

**Title:** Clínica de Várices en {hood} {city} | Próximamente
**Meta description:** Próximamente en {hood}, {city_state}. Venas Varices trata várices y arañas vasculares con opciones mínimamente invasivas. Reserve su cita hoy.
"""
        meta_title = f"Clínica de Várices en {hood} {city} | Próximamente"
        meta_desc = f"Próximamente en {hood}, {city_state}. Venas Varices trata várices y arañas vasculares con opciones mínimamente invasivas como escleroterapia y RFA. Reserve hoy."
    else:
        content = f"""# Tratamiento de Várices y Arañas Vasculares en {page_title_loc}

**Dirección:** {address}

Bienvenido a Venas Varices en {hood}, {city_state}. Nuestra clínica ofrece tratamientos especializados y mínimamente invasivos para várices y arañas vasculares, {local_phrase}.

📞 **Llámenos o reserve su cita:** {phone}

---

## Su Clínica de Venas en {hood}, {city}

Atendemos pacientes de:

{neighborhoods}

---

## Cómo llegar

{directions}

---

## Nuestros Servicios

{treatments_list}

---

## Condiciones que Tratamos

{conditions_list}

---

## ¿Por qué elegirnos?

{trust_list}

---

## Reserve su Cita

📞 **{phone}**

---

## Meta Tags

**Title:** Tratamiento de Várices en {hood}, {ctx['state']} | Venas Varices
**Meta description:** Tratamiento de várices y arañas vasculares en {hood}, {city_state}. Especialistas certificados, procedimientos mínimamente invasivos. Reserve hoy.
"""
        meta_title = f"Tratamiento de Várices en {hood}, {ctx['state']} | Venas Varices"
        meta_desc = f"Tratamiento de várices y arañas vasculares en {hood}, {city_state}. Especialistas certificados, procedimientos mínimamente invasivos. Reserve hoy."

    return content, meta_title, meta_desc


def build_content_regional(brand: dict, address: str, page_type: str, ctx: dict) -> tuple[str, str, str]:
    """Build regional site content (shorter template)."""
    brand_name = brand["name"]
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    city_state = ctx["city_state"]
    neighborhoods = "\n".join(f"- {n}" for n in ctx["neighborhoods_list"])
    directions = ctx["directions_paragraph"]
    page_title_loc = ctx["page_title_location"]
    phone = brand["phone"]
    treatments_list = "\n".join(f"- {t}" for t in brand["treatments"])
    conditions_list = "\n".join(f"- {c}" for c in brand["conditions"])
    trust_list = "\n".join(f"- {t}" for t in brand["trust_points"])

    if page_type == "coming_soon":
        content = f"""# Vein Treatment in {page_title_loc} | Coming Soon

**Address:** {address}

{brand_name} is coming soon to {hood}, {city_state}. We will offer minimally invasive vein treatments including sclerotherapy, RFA, and more.

📞 **Call ahead to schedule:** {phone}

---

## Serving Patients from:

{neighborhoods}

---

## Location

{directions}

---

## Services

{treatments_list}

---

## Conditions

{conditions_list}

---

## Why Choose Us

{trust_list}

---

## Meta Tags

**Title:** Vein Treatment in {hood} {city} | Coming Soon | {brand_name}
**Meta description:** Coming soon to {hood}, {city_state}. {brand_name} offers minimally invasive vein treatment. Book in advance: {phone}.
"""
        meta_title = f"Vein Treatment in {hood} {city} | Coming Soon | {brand_name}"
        meta_desc = f"Coming soon to {hood}, {city_state}. {brand_name} offers minimally invasive vein treatment. Book in advance: {phone}."
    else:
        content = f"""# Vein Treatment in {page_title_loc}

**Address:** {address}

{brand_name} in {hood}, {city_state} provides expert, minimally invasive vein care for patients throughout the area.

📞 **{phone}**

---

## Serving Patients from:

{neighborhoods}

---

## Location

{directions}

---

## Services

{treatments_list}

---

## Conditions

{conditions_list}

---

## Why Choose Us

{trust_list}

---

## Book Your Appointment

📞 **{phone}**

---

## Meta Tags

**Title:** Vein Treatment in {hood}, {ctx['state']} | {brand_name}
**Meta description:** Expert vein treatment in {hood}, {city_state}. {brand_name} offers sclerotherapy, RFA, and more. Book today: {phone}.
"""
        meta_title = f"Vein Treatment in {hood}, {ctx['state']} | {brand_name}"
        meta_desc = f"Expert vein treatment in {hood}, {city_state}. {brand_name} offers sclerotherapy, RFA, and more. Book today: {phone}."

    return content, meta_title, meta_desc


def generate_content_for_brand(brand_id: str, address: str, page_type: str) -> BrandContent:
    """Generate content for a single brand."""
    brand = get_brand(brand_id)
    if not brand:
        raise ValueError(f"Unknown brand: {brand_id}")

    language = brand.get("language", "en")
    ctx = get_location_context(address, brand, page_type, language)

    brand_type = brand.get("type", "main")

    if brand_id == "vtc" or brand_id == "veintreatment":
        content, meta_title, meta_desc = build_content_vtc(brand, address, page_type, ctx)
    elif brand_id == "vip":
        content, meta_title, meta_desc = build_content_vip(brand, address, page_type, ctx)
    elif brand_id == "pts":
        content, meta_title, meta_desc = build_content_pts(brand, address, page_type, ctx)
    elif brand_id == "venasvarices":
        content, meta_title, meta_desc = build_content_venasvarices(brand, address, page_type, ctx)
    elif brand_type == "regional":
        content, meta_title, meta_desc = build_content_regional(brand, address, page_type, ctx)
    else:
        content, meta_title, meta_desc = build_content_vtc(brand, address, page_type, ctx)

    return BrandContent(
        brand_id=brand_id,
        brand_name=brand["name"],
        content=content,
        meta_title=meta_title,
        meta_description=meta_desc,
    )


# ── API Routes ─────────────────────────────────────────────────────────────────

@app.get("/api/brands")
def api_brands():
    """List all available brands."""
    return list_brands()


@app.post("/api/generate", response_model=GenerateResponse)
def api_generate(req: GenerateRequest):
    """Generate location content for selected brands."""
    if not req.address.strip():
        raise HTTPException(status_code=400, detail="Address is required")
    if not req.brand_ids:
        raise HTTPException(status_code=400, detail="At least one brand must be selected")
    if req.page_type not in ("open", "coming_soon"):
        raise HTTPException(status_code=400, detail="page_type must be 'open' or 'coming_soon'")

    results = []
    errors = []

    for brand_id in req.brand_ids:
        try:
            result = generate_content_for_brand(brand_id, req.address, req.page_type)
            results.append(result)
        except Exception as e:
            errors.append(f"{brand_id}: {str(e)}")

    if not results and errors:
        raise HTTPException(status_code=500, detail="; ".join(errors))

    return GenerateResponse(
        address=req.address,
        page_type=req.page_type,
        results=results,
    )


@app.get("/health")
def health():
    return {"status": "ok", "app": "vtc-locations"}


# ── Static files ───────────────────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(static_dir, "index.html")) as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
