"""
TWU Adaptive Re-Illustration API
================================

FastAPI application for the TWU panel analysis and transformation pipeline.
Deployed on Vercel as serverless functions.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import base64
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from twu_reillustration_prototype import (
    PanelAnalyzer,
    TransformationSpecGenerator,
    PromptBuilder,
    OutputValidator,
    PanelMetadata,
    PanelCategory,
    Character,
    CharacterRole,
    EmotionBand,
    TherapeuticElement,
    create_sample_metadata_for_demo
)
from dataclasses import asdict

app = FastAPI(
    title="TWU Re-Illustration API",
    description="API for generating demographic variants of THIS WAY UP therapy illustrations",
    version="0.1.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
analyzer = PanelAnalyzer()
spec_generator = TransformationSpecGenerator()
prompt_builder = PromptBuilder()
validator = OutputValidator()


# Pydantic models for API
class TransformRequest(BaseModel):
    panel_id: str
    variant_type: str  # "gender_swap_female", "diverse_v1", "age_younger", etc.
    target_characters: Optional[List[str]] = None


class AnalysisResponse(BaseModel):
    panel_id: str
    category: str
    scene_description: str
    characters: List[Dict[str, Any]]
    therapeutic_elements: List[Dict[str, Any]]
    locked_elements: List[str]
    adaptable_elements: List[str]


class TransformResponse(BaseModel):
    panel_id: str
    variant_type: str
    transform_spec: Dict[str, Any]
    prompts: Dict[str, Any]
    validation_prompt: str


class DemoResult(BaseModel):
    panels: List[Dict[str, Any]]
    total_panels: int
    variants_available: List[str]


@app.get("/")
async def root():
    """API root - returns service info"""
    return {
        "service": "TWU Re-Illustration API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "demo": "/api/demo",
            "panels": "/api/panels",
            "transform": "/api/transform",
            "analyze_prompt": "/api/analyze/prompt",
            "variants": "/api/variants"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/demo")
async def run_demo() -> DemoResult:
    """
    Run the demo pipeline with sample panels.
    Returns transformation specs and prompts for all sample panels.
    """
    sample_panels = create_sample_metadata_for_demo()
    results = []

    for panel in sample_panels:
        # Generate transformation spec for gender swap
        transform_spec = spec_generator.generate_spec(
            panel_metadata=panel,
            variant_type="gender_swap_female",
            target_characters=["Leo"]
        )

        # Build prompts
        prompts = prompt_builder.build_prompt(panel, transform_spec)

        results.append({
            "panel_id": panel.panel_id,
            "category": panel.category.value,
            "scene_description": panel.scene_description,
            "characters": [
                {
                    "name": c.name,
                    "role": c.role.value,
                    "emotion": c.emotion.value
                }
                for c in panel.characters
            ],
            "transform_spec": {
                "variant": transform_spec.target_variant,
                "characters_transformed": list(transform_spec.character_transforms.keys()),
                "controlnet_mode": transform_spec.controlnet_mode,
                "denoise_strength": transform_spec.denoise_strength
            },
            "prompt_excerpt": prompts["positive_prompt"][:300] + "..."
        })

    return DemoResult(
        panels=results,
        total_panels=len(results),
        variants_available=["gender_swap_female", "gender_swap_male", "diverse_v1", "diverse_v2", "diverse_v3", "age_younger", "age_older"]
    )


@app.get("/api/panels")
async def list_panels():
    """List all available sample panels"""
    sample_panels = create_sample_metadata_for_demo()
    return {
        "panels": [
            {
                "panel_id": p.panel_id,
                "category": p.category.value,
                "scene_description": p.scene_description,
                "source_file": p.source_file,
                "characters": [c.name for c in p.characters],
                "requires_clinical_review": p.requires_clinical_review
            }
            for p in sample_panels
        ]
    }


@app.get("/api/panels/{panel_id}")
async def get_panel(panel_id: str):
    """Get detailed metadata for a specific panel"""
    sample_panels = create_sample_metadata_for_demo()

    for panel in sample_panels:
        if panel.panel_id == panel_id:
            return {
                "panel": {
                    **asdict(panel),
                    "category": panel.category.value,
                    "characters": [
                        {
                            **asdict(c),
                            "role": c.role.value,
                            "emotion": c.emotion.value
                        }
                        for c in panel.characters
                    ],
                    "therapeutic_elements": [
                        asdict(te)
                        for te in panel.therapeutic_elements
                    ]
                }
            }

    raise HTTPException(status_code=404, detail=f"Panel {panel_id} not found")


@app.get("/api/variants")
async def list_variants():
    """List all available transformation variants"""
    return {
        "variants": [
            {
                "id": "gender_swap_female",
                "name": "Female Client",
                "description": "Transform male client (Leo) to female (Leah)",
                "type": "gender"
            },
            {
                "id": "gender_swap_male",
                "name": "Male Partner",
                "description": "Transform female partner (Ali) to male (Alex)",
                "type": "gender"
            },
            {
                "id": "diverse_v1",
                "name": "South Asian",
                "description": "South Asian features and skin tone",
                "type": "ethnicity"
            },
            {
                "id": "diverse_v2",
                "name": "African",
                "description": "African features and skin tone",
                "type": "ethnicity"
            },
            {
                "id": "diverse_v3",
                "name": "East Asian",
                "description": "East Asian features and skin tone",
                "type": "ethnicity"
            },
            {
                "id": "age_younger",
                "name": "Younger (25-35)",
                "description": "Young adult presentation",
                "type": "age"
            },
            {
                "id": "age_older",
                "name": "Older (65-75)",
                "description": "Senior presentation",
                "type": "age"
            }
        ]
    }


@app.post("/api/transform")
async def transform_panel(request: TransformRequest) -> TransformResponse:
    """
    Generate transformation spec and prompts for a panel.

    Args:
        request: Contains panel_id, variant_type, and optional target_characters

    Returns:
        Transformation specification and generation prompts
    """
    sample_panels = create_sample_metadata_for_demo()
    panel = None

    for p in sample_panels:
        if p.panel_id == request.panel_id:
            panel = p
            break

    if not panel:
        raise HTTPException(status_code=404, detail=f"Panel {request.panel_id} not found")

    # Validate variant type
    valid_variants = [
        "gender_swap_female", "gender_swap_male",
        "diverse_v1", "diverse_v2", "diverse_v3",
        "age_younger", "age_older"
    ]
    if request.variant_type not in valid_variants:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid variant_type. Must be one of: {valid_variants}"
        )

    # Generate transformation spec
    transform_spec = spec_generator.generate_spec(
        panel_metadata=panel,
        variant_type=request.variant_type,
        target_characters=request.target_characters
    )

    # Build prompts
    prompts = prompt_builder.build_prompt(panel, transform_spec)

    # Generate validation prompt
    validation_prompt = validator.generate_validation_prompt(panel, transform_spec)

    return TransformResponse(
        panel_id=request.panel_id,
        variant_type=request.variant_type,
        transform_spec=asdict(transform_spec),
        prompts=prompts,
        validation_prompt=validation_prompt
    )


@app.get("/api/analyze/prompt")
async def get_analysis_prompt():
    """
    Get the VLM analysis prompt template.
    Use this prompt with GPT-4V or Gemini Vision to analyze new panels.
    """
    return {
        "prompt": analyzer.ANALYSIS_PROMPT_TEMPLATE,
        "instructions": "Send this prompt along with a panel image to a vision-language model (GPT-4V, Gemini Vision) to extract structured metadata.",
        "expected_output": "JSON matching the PanelMetadata schema"
    }


@app.post("/api/analyze/parse")
async def parse_analysis(response_json: Dict[str, Any]):
    """
    Parse a VLM analysis response into structured metadata.

    Args:
        response_json: The JSON response from a vision-language model

    Returns:
        Parsed and validated panel metadata
    """
    try:
        # Manually construct metadata from response
        # This is a simplified version - in production would have full validation
        return {
            "status": "parsed",
            "metadata": response_json,
            "warnings": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse response: {str(e)}")


# Vercel requires this handler
handler = app
