"""
TWU Adaptive Re-Illustration API
================================

FastAPI application for the TWU panel analysis and transformation pipeline.
Deployed on Vercel as serverless functions.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json


# ============================================================================
# Domain Models (copied from twu_reillustration_prototype.py for Vercel)
# ============================================================================

class PanelCategory(Enum):
    NARRATOR_SINGLE = "narrator_single"
    THERAPIST_SINGLE = "therapist_single"
    CLIENT_SINGLE = "client_single"
    DIALOGUE_THERAPY = "dialogue_therapy"
    DIALOGUE_DOMESTIC = "dialogue_domestic"
    MULTI_CHARACTER = "multi_character"
    CONCEPTUAL_DIAGRAM = "conceptual_diagram"
    DIAGRAM_ONLY = "diagram_only"


class EmotionBand(Enum):
    DISTRESSED = "distressed"
    STRUGGLING = "struggling"
    NEUTRAL = "neutral"
    HOPEFUL = "hopeful"
    POSITIVE = "positive"


class CharacterRole(Enum):
    CLIENT = "client"
    THERAPIST = "therapist"
    NARRATOR = "narrator"
    PARTNER = "partner"
    SUPPORTING = "supporting"


@dataclass
class Character:
    role: CharacterRole
    name: str
    gender: str
    approximate_age: str
    emotion: EmotionBand
    expression_description: str
    pose_description: str
    clothing_description: str
    position_in_frame: str
    is_speaking: bool


@dataclass
class TherapeuticElement:
    element_type: str
    content_description: str
    therapeutic_purpose: str
    must_preserve: bool = True


@dataclass
class PanelMetadata:
    panel_id: str
    source_file: str
    page_number: int
    panel_position: str
    category: PanelCategory
    scene_description: str
    setting: str
    lighting: str
    mood: str
    characters: List[Character]
    narrative_stage: str
    therapeutic_skill: str
    therapeutic_elements: List[TherapeuticElement]
    speech_bubbles: List[str]
    text_overlays: List[str]
    locked_elements: List[str]
    adaptable_elements: List[str]
    required_emotion_preservation: bool = True
    required_composition_preservation: bool = True
    requires_clinical_review: bool = False


@dataclass
class TransformationSpec:
    source_panel_id: str
    target_variant: str
    character_transforms: Dict[str, Dict[str, str]]
    preserve_pose: bool = True
    preserve_expression_type: bool = True
    preserve_composition: bool = True
    preserve_lighting: bool = True
    preserve_therapeutic_elements: bool = True
    controlnet_mode: str = "canny"
    controlnet_strength: float = 0.8
    denoise_strength: float = 0.4
    min_structural_similarity: float = 0.85
    emotion_must_match: bool = True


# ============================================================================
# Pipeline Components
# ============================================================================

class TransformationSpecGenerator:
    GENDER_SWAP_PRESET = {
        "male_to_female": {
            "gender": "female",
            "name_transform": {"Leo": "Leah", "Ian": "Dr. Sarah"},
            "appearance_notes": "Transform to female presentation while preserving age, expression, and pose"
        },
        "female_to_male": {
            "gender": "male",
            "name_transform": {"Ali": "Alex", "Rebecca": "Robert"},
            "appearance_notes": "Transform to male presentation while preserving age, expression, and pose"
        }
    }

    ETHNICITY_PRESETS = {
        "diverse_v1": {"skin_tone": "medium brown", "features": "South Asian features"},
        "diverse_v2": {"skin_tone": "dark brown", "features": "African features"},
        "diverse_v3": {"skin_tone": "light", "features": "East Asian features"}
    }

    AGE_PRESETS = {
        "younger": {"approximate_age": "young_adult", "age_range": "25-35"},
        "older": {"approximate_age": "senior", "age_range": "65-75"}
    }

    def generate_spec(self, panel_metadata: PanelMetadata, variant_type: str,
                      target_characters: Optional[List[str]] = None) -> TransformationSpec:
        character_transforms = {}

        if target_characters is None:
            target_characters = [c.name for c in panel_metadata.characters if c.role == CharacterRole.CLIENT]

        if variant_type.startswith("gender_swap"):
            direction = "male_to_female" if "female" in variant_type else "female_to_male"
            preset = self.GENDER_SWAP_PRESET[direction]
            for char in panel_metadata.characters:
                if char.name in target_characters:
                    character_transforms[char.name] = {
                        "gender": preset["gender"],
                        "new_name": preset["name_transform"].get(char.name, char.name),
                        "appearance_notes": preset["appearance_notes"],
                        "preserve_emotion": char.emotion.value,
                        "preserve_pose": char.pose_description
                    }

        elif variant_type.startswith("diverse"):
            preset = self.ETHNICITY_PRESETS.get(variant_type, self.ETHNICITY_PRESETS["diverse_v1"])
            for char in panel_metadata.characters:
                if char.name in target_characters:
                    character_transforms[char.name] = {
                        "skin_tone": preset["skin_tone"],
                        "features": preset["features"],
                        "preserve_emotion": char.emotion.value,
                        "preserve_pose": char.pose_description
                    }

        elif variant_type.startswith("age"):
            age_direction = "younger" if "younger" in variant_type else "older"
            preset = self.AGE_PRESETS[age_direction]
            for char in panel_metadata.characters:
                if char.name in target_characters:
                    character_transforms[char.name] = {
                        "approximate_age": preset["approximate_age"],
                        "age_range": preset["age_range"],
                        "preserve_emotion": char.emotion.value,
                        "preserve_pose": char.pose_description
                    }

        # Determine ControlNet mode
        if panel_metadata.category in [PanelCategory.CONCEPTUAL_DIAGRAM, PanelCategory.DIAGRAM_ONLY]:
            controlnet_mode, controlnet_strength, denoise_strength = "canny", 0.9, 0.3
        elif panel_metadata.category in [PanelCategory.DIALOGUE_THERAPY, PanelCategory.DIALOGUE_DOMESTIC]:
            controlnet_mode, controlnet_strength, denoise_strength = "openpose", 0.75, 0.45
        else:
            controlnet_mode, controlnet_strength, denoise_strength = "lineart", 0.8, 0.4

        return TransformationSpec(
            source_panel_id=panel_metadata.panel_id,
            target_variant=variant_type,
            character_transforms=character_transforms,
            controlnet_mode=controlnet_mode,
            controlnet_strength=controlnet_strength,
            denoise_strength=denoise_strength,
            min_structural_similarity=0.85 if panel_metadata.requires_clinical_review else 0.80
        )


class PromptBuilder:
    STYLE_PROMPT = """Professional illustration in clean vector style with consistent line weights,
flat color fills with subtle gradients for shading, warm but professional color palette.
Style matches THIS WAY UP CBT course illustrations."""

    NEGATIVE_PROMPT = """photorealistic, 3d render, photograph, blurry, low quality,
distorted faces, extra limbs, violence, gore, nsfw, weapons, blood,
medical emergency, self-harm, disturbing imagery, scary, horror"""

    def build_prompt(self, panel_metadata: PanelMetadata, transform_spec: TransformationSpec) -> Dict[str, str]:
        scene_parts = [
            f"Clinical therapy illustration depicting: {panel_metadata.scene_description}",
            f"Setting: {panel_metadata.setting}",
            f"Lighting: {panel_metadata.lighting}",
            f"Mood: {panel_metadata.mood}"
        ]

        char_descriptions = []
        for char in panel_metadata.characters:
            transform = transform_spec.character_transforms.get(char.name, {})
            if transform:
                gender = transform.get("gender", char.gender)
                new_name = transform.get("new_name", char.name)
                char_desc = f"{new_name}: {gender}, expression showing {char.emotion.value}"
            else:
                char_desc = f"{char.name}: {char.gender}, expression showing {char.emotion.value}"
            char_desc += f", {char.pose_description}, positioned {char.position_in_frame}"
            char_descriptions.append(char_desc)

        prompt_parts = [self.STYLE_PROMPT, "", "Scene:"] + scene_parts + ["", "Characters:"] + char_descriptions
        positive_prompt = "\n".join(prompt_parts)

        controlnet_prompt = f"""Use {transform_spec.controlnet_mode} ControlNet at strength {transform_spec.controlnet_strength}.
Denoise strength: {transform_spec.denoise_strength}
Preserve exact composition and pose from source image."""

        validation_notes = [
            f"Structural similarity must be >= {transform_spec.min_structural_similarity}",
            "Character emotions must match source panel",
            "All therapeutic elements must be present and correct"
        ]

        return {
            "positive_prompt": positive_prompt,
            "negative_prompt": self.NEGATIVE_PROMPT,
            "controlnet_prompt": controlnet_prompt,
            "validation_notes": "\n".join(validation_notes),
            "generation_params": {
                "controlnet_mode": transform_spec.controlnet_mode,
                "controlnet_strength": transform_spec.controlnet_strength,
                "denoise_strength": transform_spec.denoise_strength
            }
        }


# ============================================================================
# Sample Data
# ============================================================================

def create_sample_metadata_for_demo() -> List[PanelMetadata]:
    return [
        PanelMetadata(
            panel_id="insomnia_L1_P1_narrator_intro",
            source_file="lesson1_page-01.png",
            page_number=1,
            panel_position="top_left",
            category=PanelCategory.NARRATOR_SINGLE,
            scene_description="Course narrator Rebecca welcomes user to the sleep program",
            setting="neutral background with blue gradient",
            lighting="soft, even studio lighting",
            mood="warm, welcoming, professional",
            characters=[
                Character(
                    role=CharacterRole.NARRATOR, name="Rebecca", gender="female",
                    approximate_age="middle_aged", emotion=EmotionBand.POSITIVE,
                    expression_description="friendly smile, open expression",
                    pose_description="facing viewer, hand raised in welcoming gesture",
                    clothing_description="pink blazer over white top",
                    position_in_frame="center", is_speaking=True
                )
            ],
            narrative_stage="introduction",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[],
            speech_bubbles=["Welcome to the online Sleep program!"],
            text_overlays=[],
            locked_elements=["speech bubble content", "welcoming gesture"],
            adaptable_elements=["character demographics", "clothing colors"],
            requires_clinical_review=False
        ),
        PanelMetadata(
            panel_id="insomnia_L1_P2_therapy_intro",
            source_file="lesson1_page-02.png",
            page_number=2,
            panel_position="bottom_left",
            category=PanelCategory.DIALOGUE_THERAPY,
            scene_description="Leo meets his psychologist Ian for the first time",
            setting="therapy office with bookshelf, plant, wooden desk",
            lighting="warm indoor lighting",
            mood="professional, hopeful",
            characters=[
                Character(
                    role=CharacterRole.THERAPIST, name="Ian", gender="male",
                    approximate_age="older", emotion=EmotionBand.POSITIVE,
                    expression_description="warm professional smile",
                    pose_description="seated at desk, leaning slightly forward",
                    clothing_description="light blue button-down shirt, glasses",
                    position_in_frame="right", is_speaking=True
                ),
                Character(
                    role=CharacterRole.CLIENT, name="Leo", gender="male",
                    approximate_age="middle_aged", emotion=EmotionBand.NEUTRAL,
                    expression_description="attentive, slightly uncertain",
                    pose_description="seated across from therapist",
                    clothing_description="casual collared shirt",
                    position_in_frame="left", is_speaking=False
                )
            ],
            narrative_stage="problem_introduction",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[],
            speech_bubbles=["Great to meet you, Leo."],
            text_overlays=[],
            locked_elements=["therapy office setting", "therapeutic relationship dynamic"],
            adaptable_elements=["client demographics", "client clothing"],
            requires_clinical_review=False
        ),
        PanelMetadata(
            panel_id="insomnia_L1_P3_bed_distress",
            source_file="lesson1_page-03.png",
            page_number=3,
            panel_position="top_right",
            category=PanelCategory.CLIENT_SINGLE,
            scene_description="Leo lying awake in bed at night, unable to sleep",
            setting="bedroom at night, dark with bedside lamp glow",
            lighting="dim nighttime, warm lamp light",
            mood="frustrated, exhausted, anxious",
            characters=[
                Character(
                    role=CharacterRole.CLIENT, name="Leo", gender="male",
                    approximate_age="middle_aged", emotion=EmotionBand.DISTRESSED,
                    expression_description="tired eyes, furrowed brow, hand on forehead",
                    pose_description="lying in bed, head on pillow",
                    clothing_description="sleepwear/t-shirt",
                    position_in_frame="center", is_speaking=False
                )
            ],
            narrative_stage="problem_introduction",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[
                TherapeuticElement(
                    element_type="thought_bubble",
                    content_description="Racing anxious thoughts about not sleeping",
                    therapeutic_purpose="Illustrate cognitive component of insomnia"
                )
            ],
            speech_bubbles=[],
            text_overlays=["I would lie awake worrying..."],
            locked_elements=["distressed expression", "bedroom setting", "lying pose"],
            adaptable_elements=["character demographics", "bedroom decor"],
            requires_clinical_review=False
        ),
        PanelMetadata(
            panel_id="insomnia_L1_P5_circadian_diagram",
            source_file="lesson1_page-05.png",
            page_number=5,
            panel_position="top_left",
            category=PanelCategory.CONCEPTUAL_DIAGRAM,
            scene_description="Ian explaining circadian rhythm with clock diagram",
            setting="therapy office",
            lighting="indoor lighting",
            mood="educational",
            characters=[
                Character(
                    role=CharacterRole.THERAPIST, name="Ian", gender="male",
                    approximate_age="older", emotion=EmotionBand.NEUTRAL,
                    expression_description="explaining, educational",
                    pose_description="gesturing toward diagram",
                    clothing_description="light blue shirt, glasses",
                    position_in_frame="right", is_speaking=True
                )
            ],
            narrative_stage="psychoeducation",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[
                TherapeuticElement(
                    element_type="diagram",
                    content_description="Circadian Rhythm clock showing 24-hour cycle",
                    therapeutic_purpose="Visual explanation of sleep regulation"
                )
            ],
            speech_bubbles=["The second process is your Circadian Rhythm."],
            text_overlays=["Circadian Rhythm"],
            locked_elements=["circadian rhythm diagram", "educational content"],
            adaptable_elements=["therapist demographics"],
            requires_clinical_review=True
        ),
        PanelMetadata(
            panel_id="insomnia_L1_P2_bedroom_domestic",
            source_file="lesson1_page-02.png",
            page_number=2,
            panel_position="middle",
            category=PanelCategory.DIALOGUE_DOMESTIC,
            scene_description="Leo and Ali in bedroom discussing sleep problems",
            setting="bedroom, morning or evening",
            lighting="warm indoor domestic lighting",
            mood="concerned, supportive",
            characters=[
                Character(
                    role=CharacterRole.CLIENT, name="Leo", gender="male",
                    approximate_age="middle_aged", emotion=EmotionBand.STRUGGLING,
                    expression_description="tired, frustrated",
                    pose_description="sitting on edge of bed",
                    clothing_description="striped pajamas",
                    position_in_frame="left", is_speaking=True
                ),
                Character(
                    role=CharacterRole.PARTNER, name="Ali", gender="female",
                    approximate_age="middle_aged", emotion=EmotionBand.NEUTRAL,
                    expression_description="concerned, listening",
                    pose_description="sitting beside partner",
                    clothing_description="casual sleepwear",
                    position_in_frame="right", is_speaking=False
                )
            ],
            narrative_stage="problem_introduction",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[],
            speech_bubbles=["Another awful sleep - It's like I've lost my ability to sleep."],
            text_overlays=[],
            locked_elements=["domestic supportive dynamic", "bedroom setting"],
            adaptable_elements=["both character demographics", "bedroom decor"],
            requires_clinical_review=False
        )
    ]


# ============================================================================
# FastAPI App
# ============================================================================

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

spec_generator = TransformationSpecGenerator()
prompt_builder = PromptBuilder()


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
    sample_panels = create_sample_metadata_for_demo()
    results = []
    for panel in sample_panels:
        transform_spec = spec_generator.generate_spec(panel, "gender_swap_female", ["Leo"])
        prompts = prompt_builder.build_prompt(panel, transform_spec)
        results.append({
            "panel_id": panel.panel_id,
            "category": panel.category.value,
            "scene_description": panel.scene_description,
            "characters": [{"name": c.name, "role": c.role.value, "emotion": c.emotion.value} for c in panel.characters],
            "transform_spec": {
                "variant": transform_spec.target_variant,
                "characters_transformed": list(transform_spec.character_transforms.keys()),
                "controlnet_mode": transform_spec.controlnet_mode
            },
            "prompt_excerpt": prompts["positive_prompt"][:300] + "..."
        })
    return {"panels": results, "total_panels": len(results), "variants_available": ["gender_swap_female", "gender_swap_male", "diverse_v1", "diverse_v2", "diverse_v3", "age_younger", "age_older"]}


@app.get("/api/panels")
async def list_panels():
    sample_panels = create_sample_metadata_for_demo()
    return {
        "panels": [
            {"panel_id": p.panel_id, "category": p.category.value, "scene_description": p.scene_description,
             "source_file": p.source_file, "characters": [c.name for c in p.characters],
             "requires_clinical_review": p.requires_clinical_review}
            for p in sample_panels
        ]
    }


@app.get("/api/panels/{panel_id}")
async def get_panel(panel_id: str):
    for panel in create_sample_metadata_for_demo():
        if panel.panel_id == panel_id:
            return {"panel": {**asdict(panel), "category": panel.category.value}}
    raise HTTPException(status_code=404, detail=f"Panel {panel_id} not found")


@app.get("/api/variants")
async def list_variants():
    return {
        "variants": [
            {"id": "gender_swap_female", "name": "Female Client", "description": "Transform male client (Leo) to female (Leah)", "type": "gender"},
            {"id": "gender_swap_male", "name": "Male Partner", "description": "Transform female partner (Ali) to male (Alex)", "type": "gender"},
            {"id": "diverse_v1", "name": "South Asian", "description": "South Asian features and skin tone", "type": "ethnicity"},
            {"id": "diverse_v2", "name": "African", "description": "African features and skin tone", "type": "ethnicity"},
            {"id": "diverse_v3", "name": "East Asian", "description": "East Asian features and skin tone", "type": "ethnicity"},
            {"id": "age_younger", "name": "Younger (25-35)", "description": "Young adult presentation", "type": "age"},
            {"id": "age_older", "name": "Older (65-75)", "description": "Senior presentation", "type": "age"}
        ]
    }


@app.post("/api/transform")
async def transform_panel(request: TransformRequest):
    sample_panels = create_sample_metadata_for_demo()
    panel = next((p for p in sample_panels if p.panel_id == request.panel_id), None)
    if not panel:
        raise HTTPException(status_code=404, detail=f"Panel {request.panel_id} not found")

    valid_variants = ["gender_swap_female", "gender_swap_male", "diverse_v1", "diverse_v2", "diverse_v3", "age_younger", "age_older"]
    if request.variant_type not in valid_variants:
        raise HTTPException(status_code=400, detail=f"Invalid variant_type. Must be one of: {valid_variants}")

    transform_spec = spec_generator.generate_spec(panel, request.variant_type, request.target_characters)
    prompts = prompt_builder.build_prompt(panel, transform_spec)

    return {
        "panel_id": request.panel_id,
        "variant_type": request.variant_type,
        "transform_spec": asdict(transform_spec),
        "prompts": prompts
    }


# Vercel handler
handler = app
