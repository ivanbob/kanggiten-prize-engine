# Design System: Kanggiten Prize Engine
**Project ID:** 4381839766349587902

**Source of truth:** `Design/Kangitten logobook.pdf` (Version 1, 2026).
Supersedes House Felt, Gyroscope-as-logo, and the 2025 brand-book cover.

This is the only visual source of truth. Do not use House Felt gold, felt green, Newsreader/Fraunces, chip stacks, poker chrome, or interlocking 3D rings as the logomark.

## 1. Visual Theme & Atmosphere

Kanggiten is a premium iGaming **technology ecosystem**. Slogan: **“The new standard of iGaming platform.”**

Mood: nocturnal, precise, high-velocity. Black canvas, Electric Violet identity, Lime as the only sharp action signal (5–10% of the UI). Luxury through engineering, not ornament.

Anti-patterns: gold hairlines, oak/felt palettes, serif display type, chip motifs, neon slot cabinets, light-gray SaaS, hype copy (“revolutionary”, “game-changing”), and **any invented logomark**.

## 2. Logo (mandatory)

The official logomark is **not** 3D glass rings. Rings and gyro motifs are graphic atmosphere only.

**Mark:** a perfect circle in Electric Violet `#781DFF`. Inside: three identical white (or knock-out) right-pointing chevrons with softly rounded elbows. The chevrons read as motion and as the right half of the letter **K**.

**Lockups:**
- Horizontal (default for product chrome): mark on the left, wordmark **Kanggiten** on the right. Mark height matches the cap-height of **K**.
- Vertical: stacked, for narrow rails and splash.
- Avatar / icon / favicon: the circle mark alone. On black: violet circle, chevrons knock out to black. Inverted: white circle on violet, chevrons in violet.

**Wordmark:** Maven Pro, sentence case “Kanggiten”, black on light / white on dark. Never outline, never gradient, never a different typeface.

**Clear space:** one **K** height on every side. **Minimum height: 40px.**

**Forbidden on the logo (logobook p.09):**
- Gradients, extra colors, outlines, shadows, glow, extra effects
- Stretching, rotating, moving the mark relative to the word
- Transparency on the logo itself
- Low-contrast color-on-color (violet mark on a near-violet field)

Glass and bloom belong on chrome, never on the mark or the wordmark.

## 3. Color Palette & Roles

Brand merch ratio: **90–95% Electric Violet / 5–10% Lime**. Operator UI inverts the canvas to black so the product stays readable; violet still owns identity, lime still owns action.

| Role | Name | Hex | Use |
|---|---|---|---|
| Canvas | Black | `#000000` | Page background |
| Surface | Deep well | `#0A0614` | Sidebar, cards (black with a violet hint) |
| Raised | Violet well | `#140A24` | Inputs, nested panels |
| Primary | Electric Violet | `#781DFF` | Logo, nav, hairlines, focus. RGB 120,29,255. Pantone 2091 C |
| Pattern | Pattern Violet | `#944DFF` | Background pattern at 85–90% of this hue |
| Accent | Lime | `#D0FF43` | CTAs, scores, success, key stats only |
| Reflex | Bright Pink | `#FF43D0` | Graphic gradient stop — never body text |
| Reflex | Bloom | `#D043FF` | Graphic gradient stop, hover bloom |
| Ink on lime | Black | `#000000` | Text on lime buttons |
| Ink on violet | White | `#FFFFFF` | Text on violet fills |
| Text | White | `#FFFFFF` | Headings, amounts |
| Muted | Cool mist | `#B8B3C7` | Labels, helper copy |
| Danger | Hot fault | `#FF4D6A` | Blocking errors |

Data viz extras (charts only): `#1DA4FF`, `#1DFF78`, `#FF781D`, `#43D0FF`, `#FFE91D`, `#43FFD0`.

Graphic gradients (never on the logo): `#781DFF` → `#FF43D0` → `#D043FF`.

## 4. Typography Rules

- Titles / product name: **Maven Pro** (Regular–Black). Geometric, flowing. UI titles stay sentence case.
- Body / UI / forms: **Nunito Sans**, 14–15px body, 11–12px labels.
- Money and ranks: **JetBrains Mono** tabular lining figures.
- Stitch fallback (Maven Pro is not in the Stitch font list): headlines **Outfit**, body **Nunito Sans**, labels **JetBrains Mono**.
- Base size 15px, line-height 1.45. Overlines +0.12em in lime or violet.

Voice: short sentences. Sharp. Conversion-first. “Generate a prize table.” not “Craft a luxurious ladder.”

## 5. Component Styling

- **Buttons:** 12px radius, 40px height. Primary = lime fill, black label. Secondary = transparent with 1px violet/40 hairline. Hover: 12px violet bloom, no bounce.
- **Inputs:** Raised violet-well, 1px `#781DFF` at 28% alpha, 12px radius, white text. Focus: hairline to 70% violet + 8px bloom.
- **Cards:** 16px radius, 1px violet/22 border, optional 16–24px backdrop blur. No hard drop-shadow.
- **Chips / presets:** Pill. Selected = lime fill or violet fill + lime dot.
- **Tables:** Flush-left ranks, flush-right money. Hairline row dividers at white/8. Podium 1–3 get a faint violet wash, not gold.
- **Score:** Large Maven Pro / Outfit numeral in lime. Sub-metrics as labeled bars.
- **Navigation:** Left rail on void. Active item: 2px lime leading edge + violet-soft fill.
- **Brand in chrome:** official circle mark + “Kanggiten” in Maven Pro (Outfit in Stitch). Product line “Prize Engine” sits under the wordmark in Nunito Sans.
- **Toasts:** Raised surface, 12px radius, 4px lime or fault bar on the left.

## 6. Layout Principles

- Desktop-first operator console, 1440px.
- Left rail 240–260px. Generate workspace: 380px form column, fluid results.
- 24px page padding, 16px stack gap, 8px control gap.
- One primary action per view (Generate / Analyze / Optimize / Recalibrate).
- Empty results: centered **official logomark** (40px minimum, typically 72–96px) and one sentence of guidance. Do not use gyroscope rings as the empty-state hero.
- Motion: 160ms ease-out. No bounce.

## 7. Graphic elements (not the logo)

Source: logobook section **04**.

- **Pattern:** modular grid of the **logo circle** (chevrons), rotations 0 / 90 / 180 / 270, even rows offset by 0.5X. Base `#944DFF` at 85–90%. Use as quiet wallpaper, never over numbers.
- **Glass / raster ribbons:** official opacities **20% / 30% / 60% / 80%**. Gradient `#781DFF` → `#FF43D0` → `#D043FF`. These are atmosphere, not identity.
- **Glassmorphism (operator chrome only):** fill `rgba(10,6,20,0.45–0.60)` + `backdrop-filter: blur(16–24px)`. 1px inset highlight `white/8` on the top edge. Outer hairline `#781DFF` at 20–30%. Active / focus 60–80%. Lime stays opaque. Money stays opaque. The logo stays 100% opaque.

Do not draw slot reels, chips, cards, felt tables, or interlocking 3D rings as a substitute for the chevron-circle mark.

## 8. UX Rules (product)

- Presets load a legal tournament so an operator can publish in two clicks.
- Always show pool exactness, paid places, first prize, and quality score before the table.
- Candidate switcher when alternatives exist.
- Analyze / Optimize share one JSON paste area.
- Recalibrate keeps philosophy; only the new guarantee changes.
- Errors quote the engine `detail` string. Ctrl/Cmd+Enter submits.
