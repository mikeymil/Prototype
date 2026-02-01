# TWU Adaptive Re-Illustration: Generation Prompts
# Panel: INS_L1_P2_03 (Leo and Ali bedroom scene)
# Target Variant: Gender swap - Leo → Leah (female client)

## SOURCE PANEL ANALYSIS

**Panel ID:** INS_L1_P2_03
**Category:** DIALOGUE_DOMESTIC  
**Scene:** Leo sitting on bed edge expressing frustration about sleep, Ali standing nearby showing concern

**Original Characters:**
- Leo (client): Male, Caucasian, 45-55, distressed, sitting on bed edge
- Ali (partner): Female, Caucasian, 40-50, concerned, standing

**Therapeutic Intent:** Show the impact of insomnia on the client and introduce supportive partner dynamic

---

## VARIANT 1: Gender Swap (Leo → Leah)

### Generation Approach: img2img with ControlNet

**ControlNet Mode:** OpenPose (to preserve character poses and spatial relationship)
**ControlNet Strength:** 0.75
**Denoise Strength:** 0.45

### Positive Prompt

```
Professional therapy course illustration in clean vector style.
Consistent line weights, flat colors with subtle gradient shading.
Warm color palette matching THIS WAY UP illustration style.

SCENE: Bedroom interior, morning. Warm indoor lighting.
- Bed with grey bedding, wooden frame
- Two bedside tables with lamps
- Window with horizontal blinds in background
- Beige/warm brown walls

CHARACTER 1 (LEFT - CLIENT):
- Middle-aged woman (45-55 years old)
- Caucasian features
- Short to medium grey-streaked hair
- EXPRESSION: Tired, frustrated, hand raised to forehead showing distress
- POSE: Sitting on edge of bed, hunched posture, one hand to head
- CLOTHING: White tank top, blue and white striped pajama pants
- EMOTION: Distressed, exhausted, vulnerable

CHARACTER 2 (RIGHT - PARTNER):  
- Middle-aged woman (40-50 years old)
- Caucasian features, blonde hair
- EXPRESSION: Concerned, attentive, looking at partner
- POSE: Standing near bed, body turned toward seated partner, gesturing while speaking
- CLOTHING: Light teal top, blue knee-length skirt
- EMOTION: Worried, supportive

INTERACTION: Partner showing concern for client's sleep struggles.
Intimate domestic moment, supportive relationship dynamic.

Speech bubbles present (content will be overlaid separately).
```

### Negative Prompt

```
photorealistic, 3d render, photograph, anime, manga, 
blurry, low quality, distorted faces, extra limbs, 
wrong number of fingers, deformed hands,
violence, gore, nsfw, weapons, blood,
medical emergency, self-harm, scary, horror,
masculine features on female character,
wrong pose, different composition, 
characters in wrong positions
```

### Generation Parameters

```json
{
  "model": "stable-diffusion-xl",
  "controlnet": {
    "mode": "openpose",
    "strength": 0.75,
    "source": "INS_L1_P2_03_original.png"
  },
  "generation": {
    "denoise_strength": 0.45,
    "cfg_scale": 7.5,
    "steps": 30,
    "seed": "random_or_fixed_for_reproducibility"
  },
  "output": {
    "width": 800,
    "height": 600,
    "format": "png"
  }
}
```

---

## VARIANT 2: Ethnicity Variant (South Asian client)

### Positive Prompt

```
Professional therapy course illustration in clean vector style.
Consistent line weights, flat colors with subtle gradient shading.
Warm color palette matching THIS WAY UP illustration style.

SCENE: Bedroom interior, morning. Warm indoor lighting.
- Bed with grey bedding, wooden frame
- Two bedside tables with lamps  
- Window with horizontal blinds in background
- Beige/warm brown walls

CHARACTER 1 (LEFT - CLIENT):
- Middle-aged man (45-55 years old)
- South Asian features, medium brown skin tone
- Short grey-streaked dark hair
- EXPRESSION: Tired, frustrated, hand raised to forehead showing distress
- POSE: Sitting on edge of bed, hunched posture, one hand to head
- CLOTHING: White tank top, blue and white striped pajama pants
- EMOTION: Distressed, exhausted, vulnerable

CHARACTER 2 (RIGHT - PARTNER):
- Middle-aged woman (40-50 years old)
- South Asian features, medium brown skin tone, dark hair
- EXPRESSION: Concerned, attentive, looking at partner
- POSE: Standing near bed, body turned toward seated partner, gesturing while speaking
- CLOTHING: Light teal top, blue knee-length skirt (or culturally appropriate alternative)
- EMOTION: Worried, supportive

INTERACTION: Partner showing concern for client's sleep struggles.
Intimate domestic moment, supportive relationship dynamic.

Speech bubbles present (content will be overlaid separately).
```

---

## VARIANT 3: Combined (Female client, ethnically diverse)

### Positive Prompt

```
Professional therapy course illustration in clean vector style.
Consistent line weights, flat colors with subtle gradient shading.
Warm color palette matching THIS WAY UP illustration style.

SCENE: Bedroom interior, morning. Warm indoor lighting.
- Bed with grey bedding, wooden frame
- Two bedside tables with lamps
- Window with horizontal blinds in background
- Beige/warm brown walls

CHARACTER 1 (LEFT - CLIENT):
- Middle-aged woman (45-55 years old)  
- East Asian features, light skin tone
- Short to medium black hair with grey streaks
- EXPRESSION: Tired, frustrated, hand raised to forehead showing distress
- POSE: Sitting on edge of bed, hunched posture, one hand to head
- CLOTHING: White tank top, blue and white striped pajama pants
- EMOTION: Distressed, exhausted, vulnerable

CHARACTER 2 (RIGHT - PARTNER):
- Middle-aged man (45-55 years old)
- East Asian features, light skin tone, short dark hair
- EXPRESSION: Concerned, attentive, looking at partner
- POSE: Standing near bed, body turned toward seated partner, gesturing while speaking
- CLOTHING: Casual shirt, comfortable pants
- EMOTION: Worried, supportive

INTERACTION: Partner showing concern for client's sleep struggles.
Intimate domestic moment, supportive relationship dynamic.

Speech bubbles present (content will be overlaid separately).
```

---

## VALIDATION CHECKLIST

After generation, verify:

### Structural Fidelity
- [ ] Character positions match source (client LEFT, partner RIGHT)
- [ ] Bed and room layout preserved
- [ ] Character poses match (sitting vs standing)
- [ ] Spatial relationship between characters maintained

### Emotional Accuracy  
- [ ] Client shows DISTRESSED emotion (frustrated, tired, hand to head)
- [ ] Partner shows CONCERNED emotion (worried, attentive)
- [ ] Supportive relationship dynamic evident

### Therapeutic Integrity
- [ ] Scene conveys impact of insomnia on daily life
- [ ] Partner support is visible and appropriate
- [ ] No unintended negative or harmful elements

### Style Consistency
- [ ] Line weights consistent with TWU style
- [ ] Color palette matches (warm, professional)
- [ ] Flat color with subtle gradients
- [ ] Clean vector illustration look

### Technical Quality
- [ ] Faces properly formed, no distortion
- [ ] Hands correct (no extra fingers)
- [ ] Clothing renders correctly
- [ ] Background elements clean

---

## TEXT OVERLAY REQUIREMENTS

Speech bubbles to be composited after generation:

**Bubble 1 (pointing to client):**
"Another awful sleep - It's like I've lost my ability to sleep, [Partner Name]."

**Bubble 2 (pointing to partner):**
"I know, hon. I heard you tossing and turning and saw you on your phone at 3am."

**Name substitutions for variants:**
- Original: Ali
- If partner becomes male: Alex, Sam, or other gender-neutral/male name
- Should match demographic variant being generated

---

## CLINICAL REVIEW FLAGS

This panel: **LOW RISK** - Standard domestic scene

Review required if:
- Generated emotions don't match source
- Relationship dynamic appears altered
- Any unexpected elements introduced
- Style significantly deviates from TWU standard

Automatic approval criteria:
- Structural similarity score ≥ 0.80
- Emotion classification matches source
- No flagged content detected
