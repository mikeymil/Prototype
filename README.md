# TWU Adaptive Re-Illustration System
## Prototype Documentation

### Overview

This prototype demonstrates a pipeline for generating demographic variants of THIS WAY UP illustrated therapy content while preserving therapeutic fidelity. The system treats your existing 2,500-3,000 canonical illustrations as blueprints that can be re-rendered with different demographic presentations.

### Core Principle

**Adaptive imagery, not adaptive therapy.**

The therapeutic content, narrative structure, emotional arcs, and clinical messaging remain fixed. Only surface-level demographic characteristics change: gender, ethnicity, age presentation—allowing users to see themselves in the story while receiving identical evidence-based treatment.

---

## System Components

### 1. Panel Analyzer (`twu_reillustration_prototype.py`)

**Purpose:** Extract structured metadata from each canonical panel.

**Capabilities:**
- Classifies panels into complexity categories (narrator, dialogue, diagram, etc.)
- Identifies characters and their attributes (pose, emotion, role)
- Extracts therapeutic elements that must be preserved
- Flags locked vs. adaptable elements
- Generates structured JSON metadata

**In Production:** Would use vision-language models (GPT-4V, Gemini Vision) to automatically analyze all ~3,000 panels across your 20 programs.

### 2. Transformation Spec Generator

**Purpose:** Create constrained transformation parameters for each variant type.

**Supported Variants:**
- Gender swap (Leo → Leah)
- Ethnicity variants (multiple presets)
- Age adjustments (younger/older presentation)
- Combined transformations

**Key Constraints:**
- Preserves pose exactly
- Preserves emotional expression type
- Preserves composition and spatial relationships
- Maintains therapeutic element positioning

### 3. Prompt Builder

**Purpose:** Generate precise prompts for image generation APIs.

**Output Package:**
- Positive prompt (detailed scene description with transformations applied)
- Negative prompt (safety and quality guardrails)
- ControlNet parameters (structural preservation)
- Validation criteria

### 4. Output Validator

**Purpose:** Verify generated images meet fidelity requirements.

**Checks:**
- Structural similarity to source
- Emotion preservation
- Therapeutic element presence
- Style consistency
- Clinical safety

---

## Panel Complexity Categories

| Category | Example | Transformation Difficulty |
|----------|---------|--------------------------|
| NARRATOR_SINGLE | Rebecca explaining concepts | LOW |
| THERAPIST_SINGLE | Ian teaching a skill | LOW |
| CLIENT_SINGLE | Leo lying awake in bed | LOW-MEDIUM |
| DIALOGUE_THERAPY | Leo and Ian in session | MEDIUM |
| DIALOGUE_DOMESTIC | Leo and Ali at home | MEDIUM |
| MULTI_CHARACTER | Family scenes | HIGH |
| CONCEPTUAL_DIAGRAM | CBT cycle with character | HIGH (requires compositing) |
| DIAGRAM_ONLY | Charts, graphs | N/A (no transformation needed) |

---

## Transformation Approach

### For Character Panels (Categories 1-6)

**Method:** img2img with ControlNet

1. Extract structural guidance from source (edges, pose, depth)
2. Apply ControlNet to lock composition
3. Generate variant with demographic changes via img2img
4. Lower denoise strength preserves more of original
5. Validate output against source metadata

**Parameters:**
- ControlNet strength: 0.75-0.90 (higher = more structural fidelity)
- Denoise strength: 0.30-0.45 (lower = closer to original)

### For Diagram Panels (Category 7)

**Method:** Hybrid compositing

1. Mask diagram/text regions (these are LOCKED)
2. Generate character variant in unmasked regions only
3. Composite original diagram back over generated image
4. Overlay translated text if language variant

### For Text Elements

**Method:** Separate text layer

1. Generate images WITHOUT text (or with placeholder regions)
2. Overlay text as separate compositing step
3. Enables easy language localization
4. Ensures text is always crisp and correct

---

## Variant Matrix (Example: Insomnia Course)

| Variant | Client | Partner | Therapist | Narrator | Panels Affected |
|---------|--------|---------|-----------|----------|-----------------|
| Original | Leo (M) | Ali (F) | Ian (M) | Rebecca (F) | - |
| Female Client | Leah (F) | Alex (M) | Ian (M) | Rebecca (F) | ~120 |
| Diverse V1 | Leo (M, South Asian) | Ali (F, South Asian) | Ian (M) | Rebecca (F) | ~100 |
| Diverse V2 | Leo (M, African) | Ali (F, African) | Ian (M) | Rebecca (F) | ~100 |
| Female + Diverse | Leah (F, East Asian) | Alex (M, East Asian) | Ian (M) | Rebecca (F) | ~120 |
| Younger | Leo (M, 30s) | Ali (F, 30s) | Ian (M) | Rebecca (F) | ~100 |

**Total for one course:** ~6 variants × ~150 panels = ~900 generated images
**Total for 20 courses:** ~18,000 generated images (if applying all variants)

---

## Quality Assurance Pipeline

### Automated Checks (every image)

1. **Content Moderation** - Flag inappropriate content
2. **Structural Similarity** - SSIM/LPIPS score vs source
3. **Emotion Classification** - Verify facial expressions match
4. **Required Element Detection** - Therapeutic elements present
5. **Style Consistency** - Color palette and line weight analysis

### Clinician Review (triggered by)

- Diagram panels (therapeutic content critical)
- Low similarity scores
- Emotion mismatch detected
- New LoRA/model versions
- Random sampling (1 in N)

### Approval Workflow

```
Generate → Automated QA → [Pass] → Approved Pool
                        → [Flag] → Clinician Review → Approve/Reject
```

---

## Implementation Path

### Phase 1: Proof of Concept (Current)

- [x] Panel analysis framework
- [x] Metadata schema design
- [x] Transformation spec generator
- [x] Prompt builder
- [x] Sample panel analysis (Insomnia L1-L2)

### Phase 2: Single Course Pilot

- [ ] Extract all panels from Insomnia course (~150 images)
- [ ] Generate metadata for all panels (VLM analysis)
- [ ] Create one variant set (e.g., gender swap)
- [ ] Manual QA of full variant course
- [ ] User testing: engagement metrics comparison

### Phase 3: Production Pipeline

- [ ] Automated batch processing
- [ ] LoRA training for character consistency
- [ ] Clinician review interface
- [ ] Integration with TWU delivery platform
- [ ] A/B testing framework

### Phase 4: Full Catalogue

- [ ] Process all 20 programs
- [ ] Multiple variant sets per program
- [ ] Language localization support
- [ ] Continuous improvement from user feedback

---

## Files in This Prototype

```
/home/claude/twu_prototype/
├── twu_reillustration_prototype.py    # Core pipeline code
├── panels/                             # Extracted page images
│   ├── lesson1_page-01.png
│   ├── lesson1_page-02.png
│   └── ...
├── metadata/
│   └── lesson1_page02_analysis.json   # Detailed panel analysis
└── outputs/
    ├── demo_results.json              # Pipeline demo output
    └── generation_prompts_INS_L1_P2_03.md  # Example generation prompts
```

---

## Key Technical Decisions

1. **img2img only** - No pure text-to-image; always transform from canonical source
2. **ControlNet required** - Structural preservation is non-negotiable
3. **Text as overlay** - Never generate text inside images
4. **Metadata as contract** - Clinical requirements encoded in machine-readable format
5. **Fallback to canonical** - If generation fails QA, show original
6. **Full audit trail** - Every generation logged with parameters

---

## Next Steps

To move from prototype to pilot:

1. **Select test panels** - Pick 10-15 representative panels across complexity categories
2. **API testing** - Run actual generations through Gemini Flash Image or similar
3. **Evaluate output quality** - Can we achieve sufficient fidelity?
4. **LoRA consideration** - Do we need character fine-tuning for consistency?
5. **Cost modeling** - API costs at scale for your variant matrix
6. **User research** - Does demographic matching actually improve engagement?

---

## Contact

This prototype was developed to demonstrate feasibility for the TWU adaptive re-illustration system. The architecture is designed to scale across the full THIS WAY UP catalogue while maintaining clinical governance and therapeutic integrity.
