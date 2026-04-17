#!/usr/bin/env python3
"""
VIP Medical Group - Location Content Generator
FastAPI backend for generating location page content across VIP brands.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import re
import csv
import io
import openai
import sys

sys.path.insert(0, os.path.dirname(__file__))
from templates.brands import BRANDS, get_brand, list_brands

app = FastAPI(title="VIP Location Content Generator", version="2.0.0")

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
    doctor_name: Optional[str] = None
    clinic_type: Optional[str] = "vein"  # "vein" | "vein_pain"


class BrandContent(BaseModel):
    brand_id: str
    brand_name: str
    domain: str
    content: str
    meta_title: str
    meta_description: str


class GenerateResponse(BaseModel):
    address: str
    page_type: str
    results: List[BrandContent]


class ExportRequest(BaseModel):
    results: List[BrandContent]
    format: str  # "txt" | "doc" | "html" | "json" | "csv"
    brand_id: Optional[str] = "all"


# ── AI helper ─────────────────────────────────────────────────────────────────

def get_location_context(address: str, brand: dict, page_type: str, language: str = "en") -> dict:
    """
    Call GPT-4o-mini to get location-specific content.
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
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)
    except Exception as e:
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


# ── Doctor section helper ─────────────────────────────────────────────────────

def _doctor_section(doctor_name: Optional[str], hood: str, brand_name: str) -> str:
    """Return a doctor section if doctor_name is provided, else empty string."""
    if not doctor_name:
        return ""
    return f"""
---

## Meet Your Doctor

Dr. {doctor_name} leads our {hood} clinic at {brand_name}, providing expert care with a patient-first approach. With advanced training in minimally invasive techniques, Dr. {doctor_name} is committed to delivering the highest standard of vein and vascular care to every patient.
"""


# ── Content generators ────────────────────────────────────────────────────────

def build_content_vtc(brand: dict, address: str, page_type: str, ctx: dict, doctor_name: Optional[str] = None) -> tuple[str, str, str]:
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
    doctor_sec = _doctor_section(doctor_name, hood, brand_name)

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
{doctor_sec}
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
{doctor_sec}
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


def _generate_vip_content(address: str, hood: str, city: str, state: str, city_state: str, page_type: str, clinic_type: str = "vein", doctor_name: Optional[str] = None) -> dict:
    """
    AI-generate VIP Medical Group location content:
    - intro_paragraph: short intro with keywords
    - directions_paragraph: transit for NYC, landmarks for others
    - subway_lines: list of subway line numbers (NYC only, empty for others)
    - landmarks: list of 3 nearby landmarks
    - meta_title: 50-60 chars, optimized
    - meta_description: 150-160 chars, optimized
    """
    is_nyc = state == "NY" and city.lower() in ("new york", "new york city", "nyc", "manhattan", "brooklyn", "queens", "bronx", "staten island")

    specialty_desc = "specialized vein and pain care" if clinic_type == "vein_pain" else "specialized vein treatment"
    kw_vein = "varicose veins, spider veins, vein treatment, sclerotherapy"
    kw_pain = "back pain, neck pain, sciatica, pain management" if clinic_type == "vein_pain" else ""
    keywords = f"{kw_vein}, {kw_pain}" if kw_pain else kw_vein

    coming_soon_note = "\nThe clinic is NOT yet open (Coming Soon). Mention it opens soon and invite patients to call ahead." if page_type == "coming_soon" else ""
    doctor_note = f"\nThe doctor at this location is {doctor_name}. Mention them naturally." if doctor_name else ""

    subway_instruction = """
- "subway_lines": Array of subway line numbers/letters serving this area (e.g. ["4", "5", "6", "7", "S"]). Be accurate for the actual location.
""" if is_nyc else """
- "subway_lines": Empty array [] (not in NYC)
"""

    prompt = f"""You are a medical marketing copywriter for VIP Medical Group.

Generate content for this location:
- Address: {address}
- Neighborhood: {hood}
- City: {city}, {state}
- Clinic type: {specialty_desc}
{coming_soon_note}{doctor_note}

Return a JSON object with:

1. "intro_paragraph": One short paragraph (2-3 sentences) introducing the clinic. Mention the location naturally and include relevant keywords ({keywords}). Professional, welcoming tone. Style: "Our {hood} clinic is centrally located on [street], offering convenient access for patients seeking {specialty_desc} in the heart of {city}."

2. "directions_paragraph": A detailed paragraph (4-6 sentences) about how to get to the clinic. Include the full address. {'For NYC locations: mention specific subway lines, train stations, bus routes, and walking directions from major transit hubs. Be very specific about which trains stop nearby.' if is_nyc else 'Mention major roads, highways, nearby landmarks, and parking availability. Be specific to the actual area.'} End with a sentence about the facility being modern and comfortable.

3. "landmarks": Array of exactly 3 nearby landmarks (real places near the address). Just the names, e.g. ["Grand Central", "Bryant Park", "Cava Restaurant"]
{subway_instruction}
4. "meta_title": SEO title tag, 50-60 chars max. Include primary keyword + city. Format: "Vein Treatment in [Location] | VIP Medical Group" or "Vein & Pain Clinic in [Location] | VIP Medical Group"

5. "meta_description": SEO description, 150-160 chars max. Include keywords, city, and CTA ("Book today", "Schedule now", etc.)

Return ONLY valid JSON. No markdown."""

    try:
        resp = oai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=700,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)
    except Exception:
        return {
            "intro_paragraph": f"Our {hood} clinic offers convenient access for patients seeking {specialty_desc} in {city_state}.",
            "directions_paragraph": f"Located at {address}, our clinic is easily accessible for patients throughout {city} and the surrounding area.",
            "subway_lines": [],
            "landmarks": ["Nearby landmark 1", "Nearby landmark 2", "Nearby landmark 3"],
            "meta_title": f"Vein Treatment in {hood} | VIP Medical Group",
            "meta_description": f"Expert vein treatment in {hood}, {city_state}. Minimally invasive care by board-certified specialists. Book today.",
        }


def build_content_vip(brand: dict, address: str, page_type: str, ctx: dict, doctor_name: Optional[str] = None, clinic_type: Optional[str] = "vein") -> tuple[str, str, str]:
    """Build VIP Medical Group content — H1 + address + intro + directions + subway/landmarks."""
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    state = ctx["state"]
    city_state = ctx["city_state"]

    ai = _generate_vip_content(address, hood, city, state, city_state, page_type, clinic_type, doctor_name)

    intro = ai.get("intro_paragraph", "")
    directions = ai.get("directions_paragraph", "")
    subway_lines = ai.get("subway_lines", [])
    landmarks = ai.get("landmarks", [])
    meta_title = ai.get("meta_title", f"Vein Treatment in {hood} | VIP Medical Group")
    meta_description = ai.get("meta_description", f"Expert vein treatment in {hood}, {city_state}. Book today.")

    coming_soon_label = " — Coming Soon" if page_type == "coming_soon" else ""

    # Build subway section (NYC only)
    subway_sec = ""
    if subway_lines:
        lines_str = ", ".join(subway_lines)
        subway_sec = f"\n## Subway Services\n\n{lines_str}\n"

    # Build landmarks section
    landmarks_sec = ""
    if landmarks:
        landmarks_list = "\n".join(f"- {lm}" for lm in landmarks)
        landmarks_sec = f"\n## Landmarks Nearby\n\n{landmarks_list}\n"

    content = f"""# {hood}{coming_soon_label}

{address}

{intro}

{directions}
{subway_sec}{landmarks_sec}"""

    return content, meta_title, meta_description


def build_content_pts(brand: dict, address: str, page_type: str, ctx: dict, doctor_name: Optional[str] = None) -> tuple[str, str, str]:
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
    doctor_sec = _doctor_section(doctor_name, hood, "Pain Treatment Specialists")

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
{doctor_sec}
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
{doctor_sec}
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


def _generate_venasvarices_content(address: str, hood: str, city: str, city_state: str, page_type: str, doctor_name: Optional[str] = None) -> dict:
    """
    AI-generate the paragraph + optimized meta tags for Venas Varices.
    Returns dict with: paragraph, meta_title, meta_description
    """
    coming_soon_note = """\nThe clinic is NOT yet open (Coming Soon). The paragraph should mention it will open soon ("próximamente") and invite patients to call ahead.
""" if page_type == "coming_soon" else ""

    doctor_note = f"\nThe doctor at this location is {doctor_name}. Mention them naturally in the paragraph." if doctor_name else ""

    prompt = f"""You are a Spanish-language medical marketing copywriter for Venas Varices (a vein treatment clinic brand).

Generate content for this location:
- Address: {address}
- Neighborhood: {hood}
- City: {city}
- City, State: {city_state}
{coming_soon_note}{doctor_note}

Generate a JSON object with:

1. "paragraph": A single compelling paragraph in Spanish (3-5 sentences). Must naturally include:
   - Keywords: "arañitas", "venas varicosas", "especialistas en varices", "tratamiento de varices"
   - The full address
   - The city/neighborhood name
   - A welcoming tone ("Le damos la bienvenida" or similar)
   - Mention of advanced technology and minimally invasive treatments
   Style reference: "Somos especialistas dedicados a ofrecer los tratamientos más avanzados para la eliminación de arañitas y venas varicosas, utilizando tecnología de punta para evitar cirugías complicadas y tiempos de recuperación innecesarios."

2. "meta_title": SEO-optimized title tag in Spanish.
   - MUST be 50-60 characters max
   - Include primary keyword ("varices" or "venas varicosas") + city/neighborhood
   - Brand name "Venas Varices" at end if space allows
   - Example format: "Tratamiento de Varices en [City] | Venas Varices"

3. "meta_description": SEO-optimized meta description in Spanish.
   - MUST be 150-160 characters max
   - Include keywords, city, and a CTA ("Agende su cita", "Llame hoy", etc.)
   - Mention "mínimamente invasivo" or "sin cirugía"

Return ONLY valid JSON. No markdown, no extra text."""

    try:
        resp = oai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=500,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)
    except Exception:
        # Fallback
        if page_type == "coming_soon":
            return {
                "paragraph": f"Próximamente en {hood}, {city_state}. Venas Varices abrirá una nueva clínica dedicada al tratamiento de arañitas y venas varicosas, ubicada en {address}. Nuestros especialistas en varices utilizan tecnología de punta y procedimientos mínimamente invasivos para evitar cirugías complicadas. ¡Llame para reservar su cita con anticipación!",
                "meta_title": f"Clínica de Varices en {hood} | Próximamente",
                "meta_description": f"Próximamente en {hood}, {city_state}. Especialistas en varices y arañitas con tratamientos mínimamente invasivos. Agende su cita hoy.",
            }
        return {
            "paragraph": f"Somos especialistas dedicados a ofrecer los tratamientos más avanzados para la eliminación de arañitas y venas varicosas, utilizando tecnología de punta para evitar cirugías complicadas y tiempos de recuperación innecesarios. Si está buscando médicos especialistas en varices en {hood}, {city}, ha llegado al lugar correcto. ¡Le damos la bienvenida a nuestra clínica Venas Varices, ubicada en {address}!",
            "meta_title": f"Tratamiento de Varices en {hood} | Venas Varices",
            "meta_description": f"Especialistas en varices y arañitas en {hood}, {city_state}. Tratamientos mínimamente invasivos sin cirugía. Agende su cita hoy.",
        }


def build_content_venasvarices(brand: dict, address: str, page_type: str, ctx: dict, doctor_name: Optional[str] = None) -> tuple[str, str, str]:
    """Build Spanish content for Venas Varices — simple template: H1 + address + AI paragraph."""
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    city_state = ctx["city_state"]

    # AI generates the paragraph + optimized meta tags
    ai = _generate_venasvarices_content(address, hood, city, city_state, page_type, doctor_name)

    paragraph = ai.get("paragraph", "")
    meta_title = ai.get("meta_title", f"Tratamiento de Varices en {hood} | Venas Varices")
    meta_description = ai.get("meta_description", f"Especialistas en varices en {hood}, {city_state}. Tratamientos mínimamente invasivos. Agende su cita.")

    coming_soon_label = " — Próximamente" if page_type == "coming_soon" else ""

    content = f"""# {hood}{coming_soon_label}

{address}

{paragraph}"""

    return content, meta_title, meta_description


def build_content_veindoctor(brand: dict, address: str, page_type: str, ctx: dict, doctor_name: Optional[str] = None) -> tuple[str, str, str]:
    """Build Vein Doctor content — similar to VTC but different URL structure (/{state}/{city}/)."""
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    state = ctx["state"]
    city_state = ctx["city_state"]
    neighborhoods = "\n".join(f"- {n}" for n in ctx["neighborhoods_list"])
    directions = ctx["directions_paragraph"]
    local_phrase = ctx["local_phrase"]
    page_title_loc = ctx["page_title_location"]
    phone = brand["phone"]
    treatments_list = "\n".join(f"- {t}" for t in brand["treatments"])
    conditions_list = "\n".join(f"- {c}" for c in brand["conditions"])
    trust_list = "\n".join(f"- {t}" for t in brand["trust_points"])
    doctor_sec = _doctor_section(doctor_name, hood, "Vein Doctor")

    city_slug = city.lower().replace(" ", "-")
    state_slug = state.lower()
    url_path = f"/{state_slug}/{city_slug}/"

    if page_type == "coming_soon":
        content = f"""# Find a Vein Doctor in {page_title_loc}

**Address:** {address}
**Page URL:** veindoctor.com{url_path}

Vein Doctor is bringing expert vein care to {hood}, {city_state}. Our new clinic will connect you with board-certified vein specialists offering minimally invasive treatments for varicose veins, spider veins, and venous insufficiency.

📞 **Call us to learn more or book in advance:** {phone}

---

## Your Vein Doctor in {hood}, {city}

Our new {hood} location will provide convenient access for patients from:

{neighborhoods}

---

## Location

{directions}

---

## Treatments Available

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose Vein Doctor

{trust_list}
{doctor_sec}
---

## Opening Soon

📞 **{phone}**

---

## Meta Tags

**Title:** Vein Doctor in {hood} {city} | Coming Soon
**Meta description:** Find a vein doctor in {hood}, {city_state}. Coming soon — minimally invasive vein treatments by board-certified specialists. Call {phone}.
"""
        meta_title = f"Vein Doctor in {hood} {city} | Coming Soon"
        meta_desc = f"Find a vein doctor in {hood}, {city_state}. Coming soon — minimally invasive vein treatments by board-certified specialists. Call {phone}."
    else:
        content = f"""# Find a Vein Doctor in {page_title_loc}

**Address:** {address}
**Page URL:** veindoctor.com{url_path}

Looking for a vein doctor in {hood}, {city_state}? Our clinic {local_phrase} offers expert, minimally invasive care for varicose veins, spider veins, and venous insufficiency from board-certified vein specialists.

📞 **Call us or book your appointment:** {phone}

---

## Your Vein Doctor in {hood}, {city}

We serve patients from:

{neighborhoods}

---

## Getting Here

{directions}

---

## Treatments Available

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose Vein Doctor

{trust_list}
{doctor_sec}
---

## Book Your Appointment

📞 **{phone}**

---

## Meta Tags

**Title:** Vein Doctor in {hood}, {state} | Expert Vein Treatment
**Meta description:** Find a top vein doctor in {hood}, {city_state}. Minimally invasive treatments for varicose and spider veins. Board-certified specialists. Book today.
"""
        meta_title = f"Vein Doctor in {hood}, {state} | Expert Vein Treatment"
        meta_desc = f"Find a top vein doctor in {hood}, {city_state}. Minimally invasive treatments for varicose and spider veins. Board-certified specialists. Book today."

    return content, meta_title, meta_desc


def build_content_legulcercenter(brand: dict, address: str, page_type: str, ctx: dict, doctor_name: Optional[str] = None) -> tuple[str, str, str]:
    """Build Leg Ulcer Center content — emphasis on quality care, insurance, and patient reviews."""
    hood = ctx["neighborhood_name"]
    city = ctx["city"]
    state = ctx["state"]
    city_state = ctx["city_state"]
    neighborhoods = "\n".join(f"- {n}" for n in ctx["neighborhoods_list"])
    directions = ctx["directions_paragraph"]
    local_phrase = ctx["local_phrase"]
    page_title_loc = ctx["page_title_location"]
    phone = brand["phone"]
    treatments_list = "\n".join(f"- {t}" for t in brand["treatments"])
    conditions_list = "\n".join(f"- {c}" for c in brand["conditions"])
    trust_list = "\n".join(f"- {t}" for t in brand["trust_points"])
    doctor_sec = _doctor_section(doctor_name, hood, "Leg Ulcer Center")

    if page_type == "coming_soon":
        content = f"""# Vein Treatment Clinic in {page_title_loc}

**Address:** {address}

Welcome to our state-of-the-art Vein Treatment Clinic coming soon to {hood}, {city_state}! Our clinic will specialize in compassionate, effective care for individuals seeking relief from varicose veins, spider veins, venous leg ulcers, and other vascular concerns.

📞 **Call us to learn more or book in advance:** {phone}

Monday - Friday: 9:00 am - 7:00 pm

---

## Top rated vein experts

We employ a collaborative approach to every case: our doctors and staff spend time discussing each patient, and use resources across our broad network of facilities. Our medical directors review each case and perform rigorous quality assurance. When you meet one of us, you meet all of us, including our Harvard-trained leadership team.

Regardless of where you go, you can expect the same high-quality standards. We are conveniently located across the nation.

We will help explain your vein treatment insurance coverage and benefits. Provide us with your insurance information and we will answer any questions you may have. We work closely with insurance companies and you to ensure that there are no surprise bills or hidden costs.

---

## Highest quality treatments

Experience gentle and comfortable treatments at our vein clinic. Our techniques prioritize your comfort while effectively addressing vein conditions, ensuring a smoother recovery and minimal disruption to your daily routine.

Get back to your daily activities immediately after your vein treatment at our clinic. Our procedures are designed to offer zero downtime.

---

## We make sure your treatment is affordable

We understand that quality health care still needs to be affordable. Before we treat you, we let you know exactly what treatment will cost. Wondering "will insurance cover my vein treatment?" Call {phone}. Our insurance experts will verify your coverage.

---

## Serving patients from:

{neighborhoods}

---

## Location

{directions}
{doctor_sec}
---

## Treatments

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose Us

{trust_list}

---

## FAQ

### What is the best vein treatment?
Your vein doctor will decide on the optimal vein treatment following your initial appointment and a discussion of your unique treatment objectives. Sclerotherapy, radiofrequency ablation, and VenaSeal are some of the best remedies for varicose and spider veins.

### How much does it cost to treat veins?
Most major insurances, including Medicare, frequently pay for vein treatments. However, the price might range from $800 to $3000 if you choose to pay cash.

### Do I need a physician referral?
No. Most of the healthcare professionals we work with don't need a referral from a doctor. However, some insurances do; if this is the case, give us a call and our verifications team will assist you.

---

## Meta Tags

**Title:** Vein Treatment Clinic in {hood}, {state} | Coming Soon
**Meta description:** Coming soon to {hood}, {city_state}. State-of-the-art vein treatment clinic with Harvard-trained specialists. Zero downtime procedures. Insurance accepted. Call {phone}.
"""
        meta_title = f"Vein Treatment Clinic in {hood}, {state} | Coming Soon"
        meta_desc = f"Coming soon to {hood}, {city_state}. State-of-the-art vein treatment clinic with Harvard-trained specialists. Zero downtime procedures. Insurance accepted. Call {phone}."
    else:
        content = f"""# Vein Treatment Clinic in {page_title_loc}

**Address:** {address}

Welcome to our state-of-the-art Vein Treatment Clinic in {hood}, {city_state}! Conveniently located {local_phrase}, our clinic specializes in compassionate, effective care for individuals seeking relief from varicose veins, spider veins, venous leg ulcers, and other vascular concerns.

Our experienced team of medical professionals is committed to improving your vascular health and enhancing your overall well-being. Using the latest minimally invasive techniques and advanced technology, we create personalized treatment plans tailored to your unique needs and lifestyle.

Visit our {hood} clinic today for a consultation and take the first step toward better vein health.

📞 **{phone}**

Monday - Friday: 9:00 am - 7:00 pm

---

## Top rated vein experts

We employ a collaborative approach to every case: our doctors and staff spend time discussing each patient, and use resources across our broad network of facilities. Our medical directors review each case and perform rigorous quality assurance. When you meet one of us, you meet all of us, including our Harvard-trained leadership team.

Regardless of where you go, you can expect the same high-quality standards. We are conveniently located across the nation.

We will help explain to you your vein treatment insurance coverage and benefits. Provide us with your insurance information and we will answer any questions you may have. We work closely with insurance companies and you to ensure that there are no surprise bills or hidden costs.

---

## Highest quality treatments

Experience gentle and comfortable treatments at our vein clinic. Our techniques prioritize your comfort while effectively addressing vein conditions, ensuring a smoother recovery and minimal disruption to your daily routine.

Our commitment to staying at the forefront of medical innovation means you'll receive cutting-edge treatments that deliver exceptional results, helping you achieve vein-free legs with the utmost precision and effectiveness.

Get back to your daily activities immediately after your vein treatment at our clinic. Our procedures are designed to offer zero downtime, allowing you to resume your regular routine without any delays.

---

## We make sure your treatment is affordable

We understand that quality health care still needs to be affordable. Before we treat you, we let you know exactly what treatment will cost. Wondering "will insurance cover my vein treatment?" Call {phone}. Our insurance experts will verify your coverage.

---

## Serving patients from:

{neighborhoods}

---

## Getting Here

{directions}
{doctor_sec}
---

## Treatments

{treatments_list}

---

## Conditions We Treat

{conditions_list}

---

## Why Choose Us

{trust_list}

---

## FAQ

### What is the best vein treatment?
Your vein doctor will decide on the optimal vein treatment following your initial appointment and a discussion of your unique treatment objectives. Sclerotherapy, radiofrequency ablation, and VenaSeal are some of the best remedies for varicose and spider veins.

### How much does it cost to treat veins?
Most major insurances, including Medicare, frequently pay for vein treatments. However, the price might range from $800 to $3000 if you choose to pay cash.

### Do I need a physician referral?
No. Most of the healthcare professionals we work with don't need a referral from a doctor. However, some insurances do; if this is the case, give us a call and our verifications team will assist you.

### What should I bring to my initial consultation?
1. Insurance card or cards
2. Photo ID
3. Complete medical history and list of all prescriptions
4. List of all known allergies

---

## Meta Tags

**Title:** Vein Treatment Clinic in {hood}, {state} | Leg Ulcer Center
**Meta description:** State-of-the-art vein treatment in {hood}, {city_state}. Harvard-trained specialists, zero downtime procedures, insurance accepted. Visit our {hood} clinic today. Call {phone}.
"""
        meta_title = f"Vein Treatment Clinic in {hood}, {state} | Leg Ulcer Center"
        meta_desc = f"State-of-the-art vein treatment in {hood}, {city_state}. Harvard-trained specialists, zero downtime procedures, insurance accepted. Visit our {hood} clinic today. Call {phone}."

    return content, meta_title, meta_desc


def build_content_regional(brand: dict, address: str, page_type: str, ctx: dict, doctor_name: Optional[str] = None) -> tuple[str, str, str]:
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
    doctor_sec = _doctor_section(doctor_name, hood, brand_name)

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
{doctor_sec}
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
{doctor_sec}
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


def generate_content_for_brand(brand_id: str, address: str, page_type: str, doctor_name: Optional[str] = None, clinic_type: Optional[str] = "vein") -> BrandContent:
    """Generate content for a single brand."""
    brand = get_brand(brand_id)
    if not brand:
        raise ValueError(f"Unknown brand: {brand_id}")

    # Override brand specialty based on clinic_type selection
    if clinic_type == "vein_pain" and brand.get("specialty") in ("vein", "vein_pain"):
        brand = {**brand, "specialty": "vein_pain"}
    elif clinic_type == "vein" and brand_id != "pts":
        # Keep vein-only unless it's PTS (always pain)
        if brand.get("specialty") == "vein_pain":
            brand = {**brand, "specialty": "vein"}

    language = brand.get("language", "en")
    ctx = get_location_context(address, brand, page_type, language)

    brand_type = brand.get("type", "main")

    if brand_id == "vtc" or brand_id == "veintreatment":
        content, meta_title, meta_desc = build_content_vtc(brand, address, page_type, ctx, doctor_name)
    elif brand_id == "vip":
        content, meta_title, meta_desc = build_content_vip(brand, address, page_type, ctx, doctor_name, clinic_type)
    elif brand_id == "pts":
        content, meta_title, meta_desc = build_content_pts(brand, address, page_type, ctx, doctor_name)
    elif brand_id == "venasvarices":
        content, meta_title, meta_desc = build_content_venasvarices(brand, address, page_type, ctx, doctor_name)
    elif brand_id == "veindoctor":
        content, meta_title, meta_desc = build_content_veindoctor(brand, address, page_type, ctx, doctor_name)
    elif brand_id == "legulcercenter":
        content, meta_title, meta_desc = build_content_legulcercenter(brand, address, page_type, ctx, doctor_name)
    elif brand_type in ("regional", "other"):
        content, meta_title, meta_desc = build_content_regional(brand, address, page_type, ctx, doctor_name)
    else:
        content, meta_title, meta_desc = build_content_vtc(brand, address, page_type, ctx, doctor_name)

    return BrandContent(
        brand_id=brand_id,
        brand_name=brand["name"],
        domain=brand["domain"],
        content=content,
        meta_title=meta_title,
        meta_description=meta_desc,
    )


# ── Export helpers ─────────────────────────────────────────────────────────────

def _filter_results(results: List[BrandContent], brand_id: str) -> List[BrandContent]:
    if brand_id == "all":
        return results
    return [r for r in results if r.brand_id == brand_id]


def _md_to_html(content: str) -> str:
    """Convert markdown-style content to semantic HTML with proper heading hierarchy."""
    lines = content.strip().split("\n")
    html_lines = []
    in_list = False
    skip_meta = False

    for line in lines:
        stripped = line.strip()

        # Skip the Meta Tags section at the bottom (it's in the SEO fields)
        if stripped.startswith("## Meta Tags") or stripped.startswith("## Meta tags"):
            skip_meta = True
            continue
        if skip_meta:
            continue

        # Skip horizontal rules
        if stripped == "---":
            continue

        # Headings
        if stripped.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("#### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h4>{stripped[5:]}</h4>")
        # List items
        elif stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif re.match(r'^\d+\.\s', stripped):
            if not in_list:
                html_lines.append("<ol>")
                in_list = True
            text = re.sub(r'^\d+\.\s', '', stripped)
            html_lines.append(f"<li>{text}</li>")
        # Bold lines (like **Address:** ...)
        elif stripped.startswith("**") and ":**" in stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            # Convert **Label:** value to <p><strong>Label:</strong> value</p>
            converted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
            html_lines.append(f"<p>{converted}</p>")
        # Empty line
        elif not stripped:
            if in_list:
                # Check if list type was <ol>
                if html_lines and "<ol>" in html_lines[-len([l for l in html_lines if l.startswith("<li>")]):]:
                    html_lines.append("</ol>")
                else:
                    html_lines.append("</ul>")
                in_list = False
        # Regular text
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            # Convert inline bold/emoji
            converted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
            if converted:  # skip truly empty
                html_lines.append(f"<p>{converted}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _strip_meta_section(content: str) -> str:
    """Remove the Meta Tags section from the bottom of content."""
    lines = content.strip().split("\n")
    result = []
    for line in lines:
        if line.strip().startswith("## Meta Tags") or line.strip().startswith("## Meta tags"):
            break
        result.append(line)
    # Remove trailing --- and empty lines
    while result and result[-1].strip() in ("", "---"):
        result.pop()
    return "\n".join(result)


def _export_txt(items: List[BrandContent]) -> str:
    parts = []
    for r in items:
        parts.append(f"{'='*60}")
        parts.append(f"BRAND: {r.brand_name} ({r.brand_id})")
        parts.append(f"DOMAIN: {r.domain}")
        parts.append(f"{'='*60}")
        parts.append("")
        parts.append("[SEO]")
        parts.append(f"Title: {r.meta_title}")
        parts.append(f"Description: {r.meta_description}")
        parts.append("")
        parts.append("[CONTENT]")
        parts.append(_strip_meta_section(r.content))
        parts.append("")
    return "\n".join(parts)


def _export_html(items: List[BrandContent]) -> str:
    html_parts = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>Location Content Export</title>',
                  '<style>',
                  'body{font-family:sans-serif;max-width:900px;margin:40px auto;padding:0 20px;line-height:1.6;}',
                  '.brand{margin-bottom:40px;border-bottom:2px solid #ddd;padding-bottom:20px;}',
                  '.seo-meta{background:#fff3cd;padding:12px 16px;border-radius:8px;margin-bottom:20px;font-size:0.9em;}',
                  '.seo-meta strong{color:#6d4c00;}',
                  'h1{font-size:1.8em;} h2{font-size:1.4em;margin-top:1.5em;} h3{font-size:1.15em;margin-top:1.2em;}',
                  'ul,ol{margin:0.5em 0;padding-left:1.5em;}',
                  '</style></head><body>']
    for r in items:
        content_html = _md_to_html(r.content)
        html_parts.append(f'<div class="brand">')
        html_parts.append(f'<div class="seo-meta">')
        html_parts.append(f'<strong>SEO Title:</strong> {r.meta_title}<br>')
        html_parts.append(f'<strong>SEO Description:</strong> {r.meta_description}')
        html_parts.append(f'</div>')
        html_parts.append(content_html)
        html_parts.append(f'</div>')
    html_parts.append('</body></html>')
    return "\n".join(html_parts)


def _export_doc(items: List[BrandContent]) -> str:
    """Simple HTML-based .doc format with semantic tags."""
    return _export_html(items)


def _export_csv(items: List[BrandContent]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["brand_id", "brand_name", "domain", "seo_title", "seo_description", "content_html"])
    for r in items:
        content_html = _md_to_html(r.content)
        writer.writerow([r.brand_id, r.brand_name, r.domain, r.meta_title, r.meta_description, content_html])
    return output.getvalue()


def _export_json(items: List[BrandContent]) -> str:
    """JSON export with body as semantic HTML, separated from SEO fields."""
    structured = []
    for r in items:
        structured.append({
            "brand_id": r.brand_id,
            "brand_name": r.brand_name,
            "domain": r.domain,
            "seo": {
                "title": r.meta_title,
                "description": r.meta_description,
            },
            "body": _md_to_html(r.content),
        })
    return json.dumps(structured, indent=2, ensure_ascii=False)


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
            result = generate_content_for_brand(brand_id, req.address, req.page_type, req.doctor_name, req.clinic_type)
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


@app.post("/api/export")
def api_export(req: ExportRequest):
    """Export generated content in various formats."""
    items = _filter_results(req.results, req.brand_id or "all")
    if not items:
        raise HTTPException(status_code=400, detail="No results to export")

    fmt = req.format.lower()
    brand_suffix = req.brand_id if req.brand_id and req.brand_id != "all" else "all-brands"

    if fmt == "txt":
        content = _export_txt(items)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="location-content-{brand_suffix}.txt"'},
        )
    elif fmt == "html":
        content = _export_html(items)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="location-content-{brand_suffix}.html"'},
        )
    elif fmt == "doc":
        content = _export_doc(items)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/msword",
            headers={"Content-Disposition": f'attachment; filename="location-content-{brand_suffix}.doc"'},
        )
    elif fmt == "csv":
        content = _export_csv(items)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="location-content-{brand_suffix}.csv"'},
        )
    elif fmt == "json":
        content = _export_json(items)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="location-content-{brand_suffix}.json"'},
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}. Use txt, html, doc, csv, or json.")


@app.get("/health")
def health():
    return {"status": "ok", "app": "vtc-locations", "brands": len(BRANDS)}


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
