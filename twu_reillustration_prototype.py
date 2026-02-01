"""
TWU Adaptive Re-Illustration Prototype
======================================

This prototype demonstrates the core pipeline for generating demographic variants
of THIS WAY UP illustrated therapy content while preserving therapeutic fidelity.

Components:
1. Panel Analyzer - Extracts scene metadata using vision-language analysis
2. Transformation Spec Generator - Creates constrained transformation parameters
3. Prompt Builder - Generates img2img prompts for demographic variants
4. Validation Framework - Checks output fidelity to source

Author: TWU Research Team
Version: 0.1 (Proof of Concept)
"""

import json
import base64
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


class PanelCategory(Enum):
    """Classification of panel types by transformation complexity"""
    NARRATOR_SINGLE = "narrator_single"  # Single character direct address (Rebecca)
    THERAPIST_SINGLE = "therapist_single"  # Therapist explaining (Ian)
    CLIENT_SINGLE = "client_single"  # Client alone (Leo)
    DIALOGUE_THERAPY = "dialogue_therapy"  # Client + therapist interaction
    DIALOGUE_DOMESTIC = "dialogue_domestic"  # Client + partner/family
    MULTI_CHARACTER = "multi_character"  # 3+ characters
    CONCEPTUAL_DIAGRAM = "conceptual_diagram"  # Character + diagram/metaphor
    DIAGRAM_ONLY = "diagram_only"  # Pure diagram/text, no characters


class EmotionBand(Enum):
    """Emotional state classification for therapeutic accuracy"""
    DISTRESSED = "distressed"  # High anxiety, frustration, despair
    STRUGGLING = "struggling"  # Moderate difficulty, skepticism
    NEUTRAL = "neutral"  # Calm, attentive
    HOPEFUL = "hopeful"  # Engaged, optimistic
    POSITIVE = "positive"  # Relief, success, happiness


class CharacterRole(Enum):
    """Role classification for characters"""
    CLIENT = "client"  # The person receiving therapy (Leo)
    THERAPIST = "therapist"  # Clinical guide (Ian)
    NARRATOR = "narrator"  # Course guide (Rebecca)
    PARTNER = "partner"  # Spouse/partner (Ali)
    SUPPORTING = "supporting"  # Other characters


@dataclass
class Character:
    """Character metadata within a panel"""
    role: CharacterRole
    name: str
    gender: str
    approximate_age: str
    emotion: EmotionBand
    expression_description: str
    pose_description: str
    clothing_description: str
    position_in_frame: str  # e.g., "left", "center", "right", "foreground"
    is_speaking: bool


@dataclass
class TherapeuticElement:
    """Therapeutic content that must be preserved"""
    element_type: str  # "thought_bubble", "diagram", "worksheet", "metaphor", etc.
    content_description: str
    therapeutic_purpose: str
    must_preserve: bool = True


@dataclass
class PanelMetadata:
    """Complete metadata for a single panel"""
    panel_id: str
    source_file: str
    page_number: int
    panel_position: str  # e.g., "top_left", "bottom_right"
    
    # Classification
    category: PanelCategory
    
    # Scene description
    scene_description: str
    setting: str
    lighting: str
    mood: str
    
    # Characters
    characters: List[Character]
    
    # Therapeutic content
    narrative_stage: str  # e.g., "problem_introduction", "skill_teaching", "practice", "resolution"
    therapeutic_skill: str  # e.g., "psychoeducation", "stimulus_control", "cognitive_restructuring"
    therapeutic_elements: List[TherapeuticElement]
    
    # Dialogue/text
    speech_bubbles: List[str]
    text_overlays: List[str]
    
    # Transformation constraints
    locked_elements: List[str]  # Elements that cannot change
    adaptable_elements: List[str]  # Elements that can be personalized
    
    # Validation criteria
    required_emotion_preservation: bool = True
    required_composition_preservation: bool = True
    requires_clinical_review: bool = False


@dataclass
class TransformationSpec:
    """Specification for a demographic transformation"""
    source_panel_id: str
    target_variant: str  # e.g., "female_client", "younger_client", "diverse_v1"
    
    # Character transformations
    character_transforms: Dict[str, Dict[str, str]]  # {character_name: {attribute: new_value}}
    
    # What to preserve
    preserve_pose: bool = True
    preserve_expression_type: bool = True
    preserve_composition: bool = True
    preserve_lighting: bool = True
    preserve_therapeutic_elements: bool = True
    
    # Generation parameters
    controlnet_mode: str = "canny"  # or "lineart", "openpose", "depth"
    controlnet_strength: float = 0.8
    denoise_strength: float = 0.4  # Lower = closer to original
    
    # Validation thresholds
    min_structural_similarity: float = 0.85
    emotion_must_match: bool = True


class PanelAnalyzer:
    """
    Analyzes panels using vision-language models to extract metadata.
    
    In production, this would call GPT-4V or Gemini Vision API.
    For this prototype, we provide structured prompts for manual/API use.
    """
    
    ANALYSIS_PROMPT_TEMPLATE = """Analyze this illustrated therapy panel and extract structured metadata.

## Instructions
You are analyzing a panel from a Cognitive Behavioral Therapy (CBT) course for insomnia. 
Extract detailed information about the scene to enable faithful re-illustration with demographic variants.

## Required Analysis

### 1. Panel Category
Classify as one of:
- NARRATOR_SINGLE: Single narrator character (Rebecca - woman in pink jacket) addressing viewer
- THERAPIST_SINGLE: Therapist (Ian - older man with glasses) explaining alone
- CLIENT_SINGLE: Client (Leo - middle-aged man with grey hair) alone
- DIALOGUE_THERAPY: Client and therapist in conversation
- DIALOGUE_DOMESTIC: Client with partner (Ali - blonde woman) or family
- MULTI_CHARACTER: Three or more characters
- CONCEPTUAL_DIAGRAM: Character(s) with diagram, chart, or metaphorical illustration
- DIAGRAM_ONLY: Pure diagram or text without characters

### 2. Scene Description
- Overall scene description (1-2 sentences)
- Setting (e.g., "therapy office", "bedroom at night", "living room")
- Lighting (e.g., "warm indoor", "dark nighttime", "bright daylight")
- Mood (e.g., "tense", "hopeful", "educational")

### 3. Characters Present
For EACH character visible:
- Role: client/therapist/narrator/partner/supporting
- Name (if identifiable): Leo, Ian, Rebecca, Ali, or "unknown"
- Gender: male/female
- Approximate age: young_adult/middle_aged/older
- Emotion: distressed/struggling/neutral/hopeful/positive
- Expression: Describe facial expression in detail
- Pose: Describe body position and gesture
- Clothing: Describe what they're wearing
- Position: Where in frame (left/center/right, foreground/background)
- Speaking: Is this character speaking (has speech bubble pointing to them)?

### 4. Therapeutic Content
- Narrative stage: problem_introduction/psychoeducation/skill_teaching/practice/reflection/resolution
- Therapeutic skill being addressed: sleep_hygiene/stimulus_control/cognitive_restructuring/relaxation/sleep_scheduling
- Therapeutic elements present:
  * Thought bubbles (describe content)
  * Diagrams (describe type and content)
  * Worksheets or forms
  * Metaphorical illustrations
  * Educational text/labels

### 5. Text Content
- List all speech bubble text verbatim
- List all other text (labels, captions, diagram text)

### 6. Transformation Constraints
- Locked elements (must not change): List specific elements that are therapeutically critical
- Adaptable elements: List elements that could be personalized (character demographics, setting details)

### 7. Clinical Flags
- Does this panel contain sensitive content requiring clinical review? (yes/no)
- Reason if yes

Respond in JSON format matching the PanelMetadata schema."""

    def generate_analysis_prompt(self, image_path: str) -> str:
        """Generate the analysis prompt for a panel image"""
        return self.ANALYSIS_PROMPT_TEMPLATE
    
    def encode_image_base64(self, image_path: str) -> str:
        """Encode image for API submission"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def parse_analysis_response(self, response_json: str) -> PanelMetadata:
        """Parse API response into PanelMetadata object"""
        data = json.loads(response_json)
        
        # Convert nested structures
        characters = [
            Character(
                role=CharacterRole(c["role"]),
                name=c["name"],
                gender=c["gender"],
                approximate_age=c["approximate_age"],
                emotion=EmotionBand(c["emotion"]),
                expression_description=c["expression"],
                pose_description=c["pose"],
                clothing_description=c["clothing"],
                position_in_frame=c["position"],
                is_speaking=c["speaking"]
            )
            for c in data.get("characters", [])
        ]
        
        therapeutic_elements = [
            TherapeuticElement(
                element_type=te["type"],
                content_description=te["description"],
                therapeutic_purpose=te["purpose"],
                must_preserve=te.get("must_preserve", True)
            )
            for te in data.get("therapeutic_elements", [])
        ]
        
        return PanelMetadata(
            panel_id=data.get("panel_id", ""),
            source_file=data.get("source_file", ""),
            page_number=data.get("page_number", 0),
            panel_position=data.get("panel_position", ""),
            category=PanelCategory(data.get("category", "client_single")),
            scene_description=data.get("scene_description", ""),
            setting=data.get("setting", ""),
            lighting=data.get("lighting", ""),
            mood=data.get("mood", ""),
            characters=characters,
            narrative_stage=data.get("narrative_stage", ""),
            therapeutic_skill=data.get("therapeutic_skill", ""),
            therapeutic_elements=therapeutic_elements,
            speech_bubbles=data.get("speech_bubbles", []),
            text_overlays=data.get("text_overlays", []),
            locked_elements=data.get("locked_elements", []),
            adaptable_elements=data.get("adaptable_elements", []),
            required_emotion_preservation=data.get("required_emotion_preservation", True),
            required_composition_preservation=data.get("required_composition_preservation", True),
            requires_clinical_review=data.get("requires_clinical_review", False)
        )


class TransformationSpecGenerator:
    """
    Generates transformation specifications for demographic variants.
    """
    
    # Standard transformation presets
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
        "diverse_v1": {
            "skin_tone": "medium brown",
            "features": "South Asian features",
            "appearance_notes": "Preserve expression, age, and pose exactly"
        },
        "diverse_v2": {
            "skin_tone": "dark brown", 
            "features": "African features",
            "appearance_notes": "Preserve expression, age, and pose exactly"
        },
        "diverse_v3": {
            "skin_tone": "light",
            "features": "East Asian features", 
            "appearance_notes": "Preserve expression, age, and pose exactly"
        }
    }
    
    AGE_PRESETS = {
        "younger": {
            "approximate_age": "young_adult",
            "age_range": "25-35",
            "appearance_notes": "Younger appearance while preserving expression and pose"
        },
        "older": {
            "approximate_age": "senior",
            "age_range": "65-75",
            "appearance_notes": "Older appearance while preserving expression and pose"
        }
    }
    
    def generate_spec(
        self,
        panel_metadata: PanelMetadata,
        variant_type: str,
        target_characters: Optional[List[str]] = None
    ) -> TransformationSpec:
        """
        Generate a transformation specification for a panel.
        
        Args:
            panel_metadata: Source panel metadata
            variant_type: Type of variant (e.g., "gender_swap_female", "diverse_v1")
            target_characters: Which characters to transform (None = all adaptable)
        """
        character_transforms = {}
        
        # Determine which characters to transform
        if target_characters is None:
            # Transform client by default, leave therapist/narrator unchanged
            target_characters = [
                c.name for c in panel_metadata.characters 
                if c.role == CharacterRole.CLIENT
            ]
        
        # Apply transformation preset
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
                        "appearance_notes": preset["appearance_notes"],
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
                        "appearance_notes": preset["appearance_notes"],
                        "preserve_emotion": char.emotion.value,
                        "preserve_pose": char.pose_description
                    }
        
        # Determine appropriate ControlNet mode based on panel category
        if panel_metadata.category in [PanelCategory.CONCEPTUAL_DIAGRAM, PanelCategory.DIAGRAM_ONLY]:
            controlnet_mode = "canny"  # Preserve line work precisely
            controlnet_strength = 0.9
            denoise_strength = 0.3
        elif panel_metadata.category in [PanelCategory.DIALOGUE_THERAPY, PanelCategory.DIALOGUE_DOMESTIC]:
            controlnet_mode = "openpose"  # Preserve character poses
            controlnet_strength = 0.75
            denoise_strength = 0.45
        else:
            controlnet_mode = "lineart"
            controlnet_strength = 0.8
            denoise_strength = 0.4
        
        # Flag for clinical review if sensitive
        requires_review = panel_metadata.requires_clinical_review or \
                         panel_metadata.category == PanelCategory.CONCEPTUAL_DIAGRAM
        
        return TransformationSpec(
            source_panel_id=panel_metadata.panel_id,
            target_variant=variant_type,
            character_transforms=character_transforms,
            preserve_pose=True,
            preserve_expression_type=True,
            preserve_composition=True,
            preserve_lighting=True,
            preserve_therapeutic_elements=True,
            controlnet_mode=controlnet_mode,
            controlnet_strength=controlnet_strength,
            denoise_strength=denoise_strength,
            min_structural_similarity=0.85 if requires_review else 0.80,
            emotion_must_match=True
        )


class PromptBuilder:
    """
    Builds generation prompts from panel metadata and transformation specs.
    """
    
    STYLE_PROMPT = """Professional illustration in clean vector style with consistent line weights, 
flat color fills with subtle gradients for shading, warm but professional color palette. 
Style matches THIS WAY UP CBT course illustrations."""

    NEGATIVE_PROMPT = """photorealistic, 3d render, photograph, blurry, low quality, 
distorted faces, extra limbs, violence, gore, nsfw, weapons, blood, 
medical emergency, self-harm, disturbing imagery, scary, horror"""
    
    def build_prompt(
        self,
        panel_metadata: PanelMetadata,
        transform_spec: TransformationSpec
    ) -> Dict[str, str]:
        """
        Build complete prompt package for image generation.
        
        Returns dict with:
        - positive_prompt: Main generation prompt
        - negative_prompt: What to avoid
        - controlnet_prompt: Structural guidance notes
        - validation_notes: What to check in output
        """
        
        # Build scene description
        scene_parts = [
            f"Clinical therapy illustration depicting: {panel_metadata.scene_description}",
            f"Setting: {panel_metadata.setting}",
            f"Lighting: {panel_metadata.lighting}",
            f"Mood: {panel_metadata.mood}"
        ]
        
        # Build character descriptions with transformations applied
        char_descriptions = []
        for char in panel_metadata.characters:
            transform = transform_spec.character_transforms.get(char.name, {})
            
            if transform:
                # Apply transformation
                gender = transform.get("gender", char.gender)
                new_name = transform.get("new_name", char.name)
                age_desc = transform.get("approximate_age", char.approximate_age)
                skin_tone = transform.get("skin_tone", "")
                features = transform.get("features", "")
                
                char_desc = f"{new_name}: {gender}, {age_desc}"
                if skin_tone:
                    char_desc += f", {skin_tone} skin tone"
                if features:
                    char_desc += f", {features}"
                char_desc += f", expression showing {char.emotion.value} ({char.expression_description})"
                char_desc += f", {char.pose_description}"
                char_desc += f", wearing {char.clothing_description}"
                char_desc += f", positioned {char.position_in_frame}"
            else:
                # Keep original
                char_desc = f"{char.name}: {char.gender}, {char.approximate_age}"
                char_desc += f", expression showing {char.emotion.value} ({char.expression_description})"
                char_desc += f", {char.pose_description}"
                char_desc += f", wearing {char.clothing_description}"
                char_desc += f", positioned {char.position_in_frame}"
            
            char_descriptions.append(char_desc)
        
        # Build therapeutic elements description
        therapeutic_parts = []
        for elem in panel_metadata.therapeutic_elements:
            if elem.must_preserve:
                therapeutic_parts.append(
                    f"MUST INCLUDE: {elem.element_type} - {elem.content_description}"
                )
        
        # Compose full prompt
        prompt_parts = [
            self.STYLE_PROMPT,
            "",
            "Scene:",
        ]
        prompt_parts.extend(scene_parts)
        prompt_parts.extend(["", "Characters:"])
        prompt_parts.extend(char_descriptions)
        prompt_parts.extend(["", "Therapeutic elements to preserve:"])
        prompt_parts.extend(therapeutic_parts if therapeutic_parts else ["None specific"])
        
        positive_prompt = "\n".join(prompt_parts)
        
        # ControlNet guidance
        controlnet_prompt = f"""Use {transform_spec.controlnet_mode} ControlNet at strength {transform_spec.controlnet_strength}.
Denoise strength: {transform_spec.denoise_strength}
Preserve exact composition and pose from source image.
Character positions and spatial relationships must match source exactly."""
        
        # Validation notes
        validation_notes = [
            f"Structural similarity must be >= {transform_spec.min_structural_similarity}",
            "Character emotions must match source panel",
            "All therapeutic elements must be present and correct",
            "Composition and pose must match source",
        ]
        if transform_spec.character_transforms:
            validation_notes.append(
                f"Verify character transformations applied: {list(transform_spec.character_transforms.keys())}"
            )
        
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


class OutputValidator:
    """
    Validates generated outputs against source panel requirements.
    
    In production, this would use:
    - SSIM/LPIPS for structural similarity
    - Emotion classification models for expression matching
    - Object detection for therapeutic element verification
    - Vision-language models for semantic validation
    """
    
    VALIDATION_PROMPT_TEMPLATE = """Compare the source and generated images for this therapy panel transformation.

## Source Panel Description
{source_description}

## Intended Transformation
{transformation_description}

## Validation Checklist

### 1. Structural Fidelity
- Does the composition match the source? (character positions, scene layout)
- Are all required elements present in the same locations?
- Rate structural similarity: 0-100

### 2. Character Transformation
- Was the demographic transformation applied correctly?
- Does the transformed character still convey the same emotion?
- Is the pose preserved accurately?
- Rate transformation accuracy: 0-100

### 3. Therapeutic Element Preservation  
- Are all therapeutic elements (thought bubbles, diagrams, etc.) present?
- Is their content accurate and readable?
- Rate therapeutic fidelity: 0-100

### 4. Style Consistency
- Does the output match the TWU illustration style?
- Are line weights, colors, and shading consistent?
- Rate style match: 0-100

### 5. Clinical Safety
- Any inappropriate or potentially harmful content?
- Any unintended changes that could affect therapeutic message?
- Pass/Fail with explanation

### 6. Overall Assessment
- Overall quality score: 0-100
- Recommendation: APPROVE / REVISE / REJECT
- Specific issues to address (if any)

Respond in JSON format."""

    def generate_validation_prompt(
        self,
        panel_metadata: PanelMetadata,
        transform_spec: TransformationSpec
    ) -> str:
        """Generate validation prompt for comparing source and output"""
        
        source_desc = f"""Panel: {panel_metadata.panel_id}
Category: {panel_metadata.category.value}
Scene: {panel_metadata.scene_description}
Characters: {', '.join(c.name + ' (' + c.emotion.value + ')' for c in panel_metadata.characters)}
Therapeutic elements: {', '.join(e.element_type for e in panel_metadata.therapeutic_elements)}
Locked elements: {', '.join(panel_metadata.locked_elements)}"""

        transform_desc = f"""Variant: {transform_spec.target_variant}
Character changes: {json.dumps(transform_spec.character_transforms, indent=2)}
ControlNet mode: {transform_spec.controlnet_mode}
Expected similarity: >= {transform_spec.min_structural_similarity}"""

        return self.VALIDATION_PROMPT_TEMPLATE.format(
            source_description=source_desc,
            transformation_description=transform_desc
        )


def create_sample_metadata_for_demo() -> List[PanelMetadata]:
    """
    Create sample metadata for demonstration purposes.
    In production, this would be generated by vision-language analysis.
    """
    
    samples = [
        # Sample 1: Rebecca narrator frame (Category A - easiest)
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
                    role=CharacterRole.NARRATOR,
                    name="Rebecca",
                    gender="female",
                    approximate_age="middle_aged",
                    emotion=EmotionBand.POSITIVE,
                    expression_description="friendly smile, open expression, making eye contact",
                    pose_description="facing viewer, hand raised in welcoming gesture",
                    clothing_description="pink blazer over white top, teal earrings",
                    position_in_frame="center",
                    is_speaking=True
                )
            ],
            narrative_stage="introduction",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[],
            speech_bubbles=["Welcome to the online Sleep program!", "My name is Rebecca and I'll be helping you navigate through this four-lesson course, developed to help you improve your sleep."],
            text_overlays=[],
            locked_elements=["speech bubble content", "welcoming gesture", "professional appearance"],
            adaptable_elements=["character demographics", "clothing colors"],
            required_emotion_preservation=True,
            required_composition_preservation=True,
            requires_clinical_review=False
        ),
        
        # Sample 2: Leo and Ian therapy dialogue (Category B - medium)
        PanelMetadata(
            panel_id="insomnia_L1_P2_therapy_intro",
            source_file="lesson1_page-02.png",
            page_number=2,
            panel_position="bottom_left",
            category=PanelCategory.DIALOGUE_THERAPY,
            scene_description="Leo meets his psychologist Ian for the first time in the therapy office",
            setting="therapy office with bookshelf, plant, wooden desk",
            lighting="warm indoor lighting, natural light from window",
            mood="professional, hopeful, first meeting",
            characters=[
                Character(
                    role=CharacterRole.THERAPIST,
                    name="Ian",
                    gender="male",
                    approximate_age="older",
                    emotion=EmotionBand.POSITIVE,
                    expression_description="warm professional smile, attentive expression",
                    pose_description="seated at desk, leaning slightly forward, open body language",
                    clothing_description="light blue button-down shirt, glasses",
                    position_in_frame="right",
                    is_speaking=True
                ),
                Character(
                    role=CharacterRole.CLIENT,
                    name="Leo",
                    gender="male",
                    approximate_age="middle_aged",
                    emotion=EmotionBand.NEUTRAL,
                    expression_description="attentive, slightly uncertain, listening",
                    pose_description="seated across from therapist, hands visible",
                    clothing_description="casual collared shirt",
                    position_in_frame="left",
                    is_speaking=False
                )
            ],
            narrative_stage="problem_introduction",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[],
            speech_bubbles=["Great to meet you, Leo."],
            text_overlays=[],
            locked_elements=["therapy office setting", "professional therapeutic relationship dynamic", "spatial arrangement"],
            adaptable_elements=["client demographics", "client clothing", "office decor details"],
            required_emotion_preservation=True,
            required_composition_preservation=True,
            requires_clinical_review=False
        ),
        
        # Sample 3: Leo in bed distressed (Category A - single character, emotional)
        PanelMetadata(
            panel_id="insomnia_L1_P3_bed_distress",
            source_file="lesson1_page-03.png",
            page_number=3,
            panel_position="top_right",
            category=PanelCategory.CLIENT_SINGLE,
            scene_description="Leo lying awake in bed at night, unable to sleep, showing distress",
            setting="bedroom at night, dark with bedside lamp glow",
            lighting="dim nighttime, warm lamp light on face",
            mood="frustrated, exhausted, anxious",
            characters=[
                Character(
                    role=CharacterRole.CLIENT,
                    name="Leo",
                    gender="male",
                    approximate_age="middle_aged",
                    emotion=EmotionBand.DISTRESSED,
                    expression_description="tired eyes, furrowed brow, hand on forehead showing frustration",
                    pose_description="lying in bed, head on pillow, one hand raised to forehead",
                    clothing_description="sleepwear/t-shirt",
                    position_in_frame="center",
                    is_speaking=False
                )
            ],
            narrative_stage="problem_introduction",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[
                TherapeuticElement(
                    element_type="thought_bubble",
                    content_description="Racing anxious thoughts about not sleeping",
                    therapeutic_purpose="Illustrate cognitive component of insomnia",
                    must_preserve=True
                )
            ],
            speech_bubbles=[],
            text_overlays=["I would lie awake worrying about the kids and work..."],
            locked_elements=["distressed emotional expression", "bedroom at night setting", "lying in bed pose", "thought content"],
            adaptable_elements=["character demographics", "bedroom decor", "sleepwear style"],
            required_emotion_preservation=True,
            required_composition_preservation=True,
            requires_clinical_review=False
        ),
        
        # Sample 4: Circadian rhythm diagram (Category C - hardest)
        PanelMetadata(
            panel_id="insomnia_L1_P5_circadian_diagram",
            source_file="lesson1_page-05.png",
            page_number=5,
            panel_position="top_left",
            category=PanelCategory.CONCEPTUAL_DIAGRAM,
            scene_description="Ian explaining circadian rhythm concept with clock diagram showing brain",
            setting="therapy office",
            lighting="indoor lighting",
            mood="educational, explanatory",
            characters=[
                Character(
                    role=CharacterRole.THERAPIST,
                    name="Ian",
                    gender="male",
                    approximate_age="older",
                    emotion=EmotionBand.NEUTRAL,
                    expression_description="explaining, educational expression",
                    pose_description="gesturing toward diagram",
                    clothing_description="light blue shirt, glasses",
                    position_in_frame="right",
                    is_speaking=True
                )
            ],
            narrative_stage="psychoeducation",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[
                TherapeuticElement(
                    element_type="diagram",
                    content_description="Circadian Rhythm clock showing 24-hour cycle with brain illustration",
                    therapeutic_purpose="Visual explanation of biological sleep regulation",
                    must_preserve=True
                )
            ],
            speech_bubbles=["The second process that regulates your sleep is your Circadian Rhythm."],
            text_overlays=["Circadian Rhythm", "11", "12", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            locked_elements=["circadian rhythm diagram", "clock numbers", "brain illustration", "educational content"],
            adaptable_elements=["therapist demographics"],
            required_emotion_preservation=True,
            required_composition_preservation=True,
            requires_clinical_review=True  # Diagram content critical
        ),
        
        # Sample 5: Leo and Ali domestic scene (Category B - dialogue domestic)
        PanelMetadata(
            panel_id="insomnia_L1_P2_bedroom_domestic",
            source_file="lesson1_page-02.png", 
            page_number=2,
            panel_position="middle",
            category=PanelCategory.DIALOGUE_DOMESTIC,
            scene_description="Leo and Ali in bedroom discussing his sleep problems",
            setting="bedroom, morning or evening",
            lighting="warm indoor domestic lighting",
            mood="concerned, supportive, intimate domestic moment",
            characters=[
                Character(
                    role=CharacterRole.CLIENT,
                    name="Leo",
                    gender="male",
                    approximate_age="middle_aged",
                    emotion=EmotionBand.STRUGGLING,
                    expression_description="tired, frustrated, explaining problem",
                    pose_description="sitting on edge of bed, shoulders slightly slumped",
                    clothing_description="casual home clothes, striped pajamas",
                    position_in_frame="left",
                    is_speaking=True
                ),
                Character(
                    role=CharacterRole.PARTNER,
                    name="Ali",
                    gender="female",
                    approximate_age="middle_aged",
                    emotion=EmotionBand.NEUTRAL,
                    expression_description="concerned, listening attentively, supportive",
                    pose_description="sitting on bed beside partner, turned toward him",
                    clothing_description="casual sleepwear",
                    position_in_frame="right",
                    is_speaking=False
                )
            ],
            narrative_stage="problem_introduction",
            therapeutic_skill="psychoeducation",
            therapeutic_elements=[],
            speech_bubbles=["Another awful sleep - It's like I've lost my ability to sleep, Ali."],
            text_overlays=[],
            locked_elements=["domestic supportive dynamic", "bedroom setting", "concerned partner response"],
            adaptable_elements=["both character demographics", "bedroom decor", "clothing"],
            required_emotion_preservation=True,
            required_composition_preservation=True,
            requires_clinical_review=False
        )
    ]
    
    return samples


def run_prototype_demo():
    """
    Run a demonstration of the prototype pipeline.
    """
    print("=" * 70)
    print("TWU ADAPTIVE RE-ILLUSTRATION PROTOTYPE")
    print("=" * 70)
    print()
    
    # Initialize components
    analyzer = PanelAnalyzer()
    spec_generator = TransformationSpecGenerator()
    prompt_builder = PromptBuilder()
    validator = OutputValidator()
    
    # Get sample metadata
    sample_panels = create_sample_metadata_for_demo()
    
    print(f"Loaded {len(sample_panels)} sample panels for demonstration")
    print()
    
    # Process each sample with gender swap transformation
    results = []
    
    for panel in sample_panels:
        print("-" * 70)
        print(f"Panel: {panel.panel_id}")
        print(f"Category: {panel.category.value}")
        print(f"Scene: {panel.scene_description}")
        print()
        
        # Generate transformation spec
        transform_spec = spec_generator.generate_spec(
            panel_metadata=panel,
            variant_type="gender_swap_female",
            target_characters=["Leo"]  # Only transform client
        )
        
        print("Transformation Spec:")
        print(f"  Target variant: {transform_spec.target_variant}")
        print(f"  Characters to transform: {list(transform_spec.character_transforms.keys())}")
        print(f"  ControlNet mode: {transform_spec.controlnet_mode}")
        print(f"  Denoise strength: {transform_spec.denoise_strength}")
        print()
        
        # Build generation prompt
        prompts = prompt_builder.build_prompt(panel, transform_spec)
        
        print("Generation Prompt (excerpt):")
        print(prompts["positive_prompt"][:500] + "...")
        print()
        
        # Generate validation prompt
        validation_prompt = validator.generate_validation_prompt(panel, transform_spec)
        
        print("Validation requirements:")
        print(prompts["validation_notes"])
        print()
        
        # Store result
        results.append({
            "panel_id": panel.panel_id,
            "category": panel.category.value,
            "metadata": asdict(panel),
            "transform_spec": asdict(transform_spec),
            "prompts": prompts,
            "validation_prompt": validation_prompt
        })
    
    # Save results
    output_path = Path("/home/claude/twu_prototype/outputs/demo_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("=" * 70)
    print(f"Demo complete. Results saved to: {output_path}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_prototype_demo()
