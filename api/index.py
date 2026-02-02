"""
TWU Adaptive Re-Illustration API
================================
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

app = FastAPI(
    title="TWU Re-Illustration API",
    description="API for generating demographic variants of THIS WAY UP therapy illustrations",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample panel data as plain dicts (avoiding dataclass issues)
SAMPLE_PANELS = [
    {
        "panel_id": "insomnia_L1_P1_narrator_intro",
        "source_file": "lesson1_page-01.png",
        "category": "narrator_single",
        "scene_description": "Course narrator Rebecca welcomes user to the sleep program",
        "setting": "neutral background with blue gradient",
        "lighting": "soft, even studio lighting",
        "mood": "warm, welcoming, professional",
        "characters": [
            {"name": "Rebecca", "role": "narrator", "gender": "female", "emotion": "positive",
             "pose": "facing viewer, hand raised in welcoming gesture", "position": "center"}
        ],
        "locked_elements": ["speech bubble content", "welcoming gesture"],
        "adaptable_elements": ["character demographics", "clothing colors"],
        "requires_clinical_review": False
    },
    {
        "panel_id": "insomnia_L1_P2_therapy_intro",
        "source_file": "lesson1_page-02.png",
        "category": "dialogue_therapy",
        "scene_description": "Leo meets his psychologist Ian for the first time",
        "setting": "therapy office with bookshelf, plant, wooden desk",
        "lighting": "warm indoor lighting",
        "mood": "professional, hopeful",
        "characters": [
            {"name": "Ian", "role": "therapist", "gender": "male", "emotion": "positive",
             "pose": "seated at desk, leaning slightly forward", "position": "right"},
            {"name": "Leo", "role": "client", "gender": "male", "emotion": "neutral",
             "pose": "seated across from therapist", "position": "left"}
        ],
        "locked_elements": ["therapy office setting", "therapeutic relationship dynamic"],
        "adaptable_elements": ["client demographics", "client clothing"],
        "requires_clinical_review": False
    },
    {
        "panel_id": "insomnia_L1_P3_bed_distress",
        "source_file": "lesson1_page-03.png",
        "category": "client_single",
        "scene_description": "Leo lying awake in bed at night, unable to sleep",
        "setting": "bedroom at night, dark with bedside lamp glow",
        "lighting": "dim nighttime, warm lamp light",
        "mood": "frustrated, exhausted, anxious",
        "characters": [
            {"name": "Leo", "role": "client", "gender": "male", "emotion": "distressed",
             "pose": "lying in bed, head on pillow", "position": "center"}
        ],
        "locked_elements": ["distressed expression", "bedroom setting", "lying pose"],
        "adaptable_elements": ["character demographics", "bedroom decor"],
        "requires_clinical_review": False
    },
    {
        "panel_id": "insomnia_L1_P5_circadian_diagram",
        "source_file": "lesson1_page-05.png",
        "category": "conceptual_diagram",
        "scene_description": "Ian explaining circadian rhythm with clock diagram",
        "setting": "therapy office",
        "lighting": "indoor lighting",
        "mood": "educational",
        "characters": [
            {"name": "Ian", "role": "therapist", "gender": "male", "emotion": "neutral",
             "pose": "gesturing toward diagram", "position": "right"}
        ],
        "locked_elements": ["circadian rhythm diagram", "educational content"],
        "adaptable_elements": ["therapist demographics"],
        "requires_clinical_review": True
    },
    {
        "panel_id": "insomnia_L1_P2_bedroom_domestic",
        "source_file": "lesson1_page-02.png",
        "category": "dialogue_domestic",
        "scene_description": "Leo and Ali in bedroom discussing sleep problems",
        "setting": "bedroom, morning or evening",
        "lighting": "warm indoor domestic lighting",
        "mood": "concerned, supportive",
        "characters": [
            {"name": "Leo", "role": "client", "gender": "male", "emotion": "struggling",
             "pose": "sitting on edge of bed", "position": "left"},
            {"name": "Ali", "role": "partner", "gender": "female", "emotion": "neutral",
             "pose": "sitting beside partner", "position": "right"}
        ],
        "locked_elements": ["domestic supportive dynamic", "bedroom setting"],
        "adaptable_elements": ["both character demographics", "bedroom decor"],
        "requires_clinical_review": False
    }
]

VARIANTS = [
    {"id": "gender_swap_female", "name": "Female Client", "description": "Transform male client (Leo) to female (Leah)", "type": "gender"},
    {"id": "gender_swap_male", "name": "Male Partner", "description": "Transform female partner (Ali) to male (Alex)", "type": "gender"},
    {"id": "diverse_v1", "name": "South Asian", "description": "South Asian features and skin tone", "type": "ethnicity"},
    {"id": "diverse_v2", "name": "African", "description": "African features and skin tone", "type": "ethnicity"},
    {"id": "diverse_v3", "name": "East Asian", "description": "East Asian features and skin tone", "type": "ethnicity"},
    {"id": "age_younger", "name": "Younger (25-35)", "description": "Young adult presentation", "type": "age"},
    {"id": "age_older", "name": "Older (65-75)", "description": "Senior presentation", "type": "age"}
]

STYLE_PROMPT = """Professional illustration in clean vector style with consistent line weights,
flat color fills with subtle gradients for shading, warm but professional color palette.
Style matches THIS WAY UP CBT course illustrations."""

NEGATIVE_PROMPT = """photorealistic, 3d render, photograph, blurry, low quality,
distorted faces, extra limbs, violence, gore, nsfw, weapons, blood,
medical emergency, self-harm, disturbing imagery, scary, horror"""


def generate_transform_spec(panel: dict, variant_type: str, target_chars: List[str] = None):
    """Generate transformation specification"""
    if target_chars is None:
        target_chars = [c["name"] for c in panel["characters"] if c["role"] == "client"]

    character_transforms = {}

    if variant_type == "gender_swap_female":
        for char in panel["characters"]:
            if char["name"] in target_chars:
                character_transforms[char["name"]] = {
                    "gender": "female",
                    "new_name": "Leah" if char["name"] == "Leo" else char["name"],
                    "preserve_emotion": char["emotion"],
                    "preserve_pose": char["pose"]
                }
    elif variant_type == "gender_swap_male":
        for char in panel["characters"]:
            if char["name"] in target_chars:
                character_transforms[char["name"]] = {
                    "gender": "male",
                    "new_name": "Alex" if char["name"] == "Ali" else char["name"],
                    "preserve_emotion": char["emotion"],
                    "preserve_pose": char["pose"]
                }
    elif variant_type.startswith("diverse"):
        presets = {
            "diverse_v1": {"skin_tone": "medium brown", "features": "South Asian features"},
            "diverse_v2": {"skin_tone": "dark brown", "features": "African features"},
            "diverse_v3": {"skin_tone": "light", "features": "East Asian features"}
        }
        preset = presets.get(variant_type, presets["diverse_v1"])
        for char in panel["characters"]:
            if char["name"] in target_chars:
                character_transforms[char["name"]] = {
                    **preset,
                    "preserve_emotion": char["emotion"],
                    "preserve_pose": char["pose"]
                }
    elif variant_type.startswith("age"):
        presets = {
            "age_younger": {"age": "young_adult", "age_range": "25-35"},
            "age_older": {"age": "senior", "age_range": "65-75"}
        }
        preset = presets.get(variant_type, presets["age_younger"])
        for char in panel["characters"]:
            if char["name"] in target_chars:
                character_transforms[char["name"]] = {
                    **preset,
                    "preserve_emotion": char["emotion"],
                    "preserve_pose": char["pose"]
                }

    # Determine ControlNet settings based on panel category
    category = panel["category"]
    if category in ["conceptual_diagram", "diagram_only"]:
        controlnet_mode, strength, denoise = "canny", 0.9, 0.3
    elif category in ["dialogue_therapy", "dialogue_domestic"]:
        controlnet_mode, strength, denoise = "openpose", 0.75, 0.45
    else:
        controlnet_mode, strength, denoise = "lineart", 0.8, 0.4

    return {
        "source_panel_id": panel["panel_id"],
        "target_variant": variant_type,
        "character_transforms": character_transforms,
        "controlnet_mode": controlnet_mode,
        "controlnet_strength": strength,
        "denoise_strength": denoise,
        "min_structural_similarity": 0.85 if panel.get("requires_clinical_review") else 0.80
    }


def build_prompt(panel: dict, transform_spec: dict):
    """Build generation prompt"""
    scene_parts = [
        f"Clinical therapy illustration depicting: {panel['scene_description']}",
        f"Setting: {panel['setting']}",
        f"Lighting: {panel['lighting']}",
        f"Mood: {panel['mood']}"
    ]

    char_descriptions = []
    for char in panel["characters"]:
        transform = transform_spec["character_transforms"].get(char["name"], {})
        if transform:
            gender = transform.get("gender", char["gender"])
            name = transform.get("new_name", char["name"])
            char_desc = f"{name}: {gender}, expression showing {char['emotion']}"
        else:
            char_desc = f"{char['name']}: {char['gender']}, expression showing {char['emotion']}"
        char_desc += f", {char['pose']}, positioned {char['position']}"
        char_descriptions.append(char_desc)

    prompt_parts = [STYLE_PROMPT, "", "Scene:"] + scene_parts + ["", "Characters:"] + char_descriptions
    positive_prompt = "\n".join(prompt_parts)

    controlnet_prompt = f"""Use {transform_spec['controlnet_mode']} ControlNet at strength {transform_spec['controlnet_strength']}.
Denoise strength: {transform_spec['denoise_strength']}
Preserve exact composition and pose from source image."""

    return {
        "positive_prompt": positive_prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "controlnet_prompt": controlnet_prompt,
        "generation_params": {
            "controlnet_mode": transform_spec["controlnet_mode"],
            "controlnet_strength": transform_spec["controlnet_strength"],
            "denoise_strength": transform_spec["denoise_strength"]
        }
    }


class TransformRequest(BaseModel):
    panel_id: str
    variant_type: str
    target_characters: Optional[List[str]] = None


@app.get("/")
async def root():
    return {
        "service": "TWU Re-Illustration API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "demo": "/api/demo",
            "panels": "/api/panels",
            "transform": "/api/transform",
            "variants": "/api/variants"
        }
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/demo")
async def run_demo():
    results = []
    for panel in SAMPLE_PANELS:
        transform_spec = generate_transform_spec(panel, "gender_swap_female", ["Leo"])
        prompts = build_prompt(panel, transform_spec)
        results.append({
            "panel_id": panel["panel_id"],
            "category": panel["category"],
            "scene_description": panel["scene_description"],
            "characters": [{"name": c["name"], "role": c["role"], "emotion": c["emotion"]} for c in panel["characters"]],
            "transform_spec": {
                "variant": transform_spec["target_variant"],
                "characters_transformed": list(transform_spec["character_transforms"].keys()),
                "controlnet_mode": transform_spec["controlnet_mode"]
            },
            "prompt_excerpt": prompts["positive_prompt"][:300] + "..."
        })
    return {"panels": results, "total_panels": len(results), "variants_available": [v["id"] for v in VARIANTS]}


@app.get("/api/panels")
async def list_panels():
    return {
        "panels": [
            {"panel_id": p["panel_id"], "category": p["category"], "scene_description": p["scene_description"],
             "source_file": p["source_file"], "characters": [c["name"] for c in p["characters"]],
             "requires_clinical_review": p["requires_clinical_review"]}
            for p in SAMPLE_PANELS
        ]
    }


@app.get("/api/panels/{panel_id}")
async def get_panel(panel_id: str):
    for panel in SAMPLE_PANELS:
        if panel["panel_id"] == panel_id:
            return {"panel": panel}
    raise HTTPException(status_code=404, detail=f"Panel {panel_id} not found")


@app.get("/api/variants")
async def list_variants():
    return {"variants": VARIANTS}


@app.post("/api/transform")
async def transform_panel(request: TransformRequest):
    panel = next((p for p in SAMPLE_PANELS if p["panel_id"] == request.panel_id), None)
    if not panel:
        raise HTTPException(status_code=404, detail=f"Panel {request.panel_id} not found")

    valid_variants = [v["id"] for v in VARIANTS]
    if request.variant_type not in valid_variants:
        raise HTTPException(status_code=400, detail=f"Invalid variant_type. Must be one of: {valid_variants}")

    transform_spec = generate_transform_spec(panel, request.variant_type, request.target_characters)
    prompts = build_prompt(panel, transform_spec)

    return {
        "panel_id": request.panel_id,
        "variant_type": request.variant_type,
        "transform_spec": transform_spec,
        "prompts": prompts
    }


# Vercel handler
handler = app
