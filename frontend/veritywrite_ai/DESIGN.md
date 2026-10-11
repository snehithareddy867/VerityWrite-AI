---
name: VerityWrite AI
colors:
  surface: '#121318'
  surface-dim: '#121318'
  surface-bright: '#38393f'
  surface-container-lowest: '#0d0e13'
  surface-container-low: '#1a1b20'
  surface-container: '#1e1f25'
  surface-container-high: '#292a2f'
  surface-container-highest: '#34343a'
  on-surface: '#e3e1e9'
  on-surface-variant: '#cbc3d7'
  inverse-surface: '#e3e1e9'
  inverse-on-surface: '#2f3036'
  outline: '#958ea0'
  outline-variant: '#494454'
  surface-tint: '#d0bcff'
  primary: '#d0bcff'
  on-primary: '#3c0091'
  primary-container: '#a078ff'
  on-primary-container: '#340080'
  inverse-primary: '#6d3bd7'
  secondary: '#cebdff'
  on-secondary: '#361e74'
  secondary-container: '#503a8f'
  on-secondary-container: '#c1acff'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00a572'
  on-tertiary-container: '#00311f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e9ddff'
  primary-fixed-dim: '#d0bcff'
  on-primary-fixed: '#23005c'
  on-primary-fixed-variant: '#5516be'
  secondary-fixed: '#e8ddff'
  secondary-fixed-dim: '#cebdff'
  on-secondary-fixed: '#21005e'
  on-secondary-fixed-variant: '#4d378c'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#121318'
  on-background: '#e3e1e9'
  surface-variant: '#34343a'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system embodies developer-grade rigor, precision, and forensic transparency for next-generation AI writing, humanization, and text authenticity verification. Built on the Modern Corporate/AI SaaS aesthetic, it rejects superficial ornamentation in favor of high-legibility workspaces, deterministic visual feedback, and surgical control.

### Target Audience & Tone
Engineers, technical writers, researchers, and enterprise content creators requiring granular insight into algorithmic detection, text humanization heuristics, and provenance scores. The emotional tone is authoritative, composed, and analytical—offering quiet competence and zero cognitive fatigue during extended editing and verification sessions.

### Visual Character
- **Dark-First Foundation:** Deep obsidian-tinted neutrals eliminate eye strain and allow syntactical highlights to lead the eye.
- **Electric Violet Signal:** Vibrant violet accents direct attention to generative actions and verified outcomes without overwhelming text analysis.
- **Micro-Structured Depth:** Subtle hairline dividers and tonal elevation take precedence over heavy diffusion or theatrical drop-shadows.

## Colors

The palette is engineered specifically for deep-contrast text editing, analytical inspection, and real-time diff evaluation.

### Core Canvas & Surfaces
- **Canvas Base:** `#101116` — The deep, non-reflective base canvas for core editor regions.
- **Sidebar & Chrome:** `#15161D` — Structural navigation and tool drawers.
- **Elevated Surfaces:** `#1B1D26` — Inspector cards, floating inspector palettes, and analysis modals.
- **Input & Recessed Wells:** `#14151C` — Text fields, raw token editors, and console wells.
- **Hairline Borders:** `#2D2F3A` — Boundary outlines delivering crisp structural separation.

### Brand & Interactive Accents
- **Primary Accent (`#8B5CF6`):** Electric violet for key trigger buttons, selected active states, and AI engine controls.
- **Secondary Accent (`#B9A2FF`):** Soft lavender used for secondary pill badges, active hover states, and contextual caret highlights.

### Verification & Trust Status
- **Success (`#10B981`):** Verified human, authentic scoring, passed authenticity heuristics.
- **Review / Warning (`#F59E0B`):** Ambiguous entropy, moderate AI probability, rewrite suggested.
- **Critical / Error (`#EF4444`):** Machine signature detected, failed validation, blocked payload.

## Typography

Typography in this design system emphasizes strict vertical metric alignment, neutral geometric cadence, and high character distinction. `Inter` provides systematic legibility across prose and dense interface panels.

### Hierarchy & Composition Rules
- **Display & Section Titles:** Restrained negative tracking (`-0.015em` to `-0.02em`) preserves tightness and avoids float at large scales.
- **Editorial Text Area:** Standard `body-lg` at 16px with a generous 26px line height ensures distraction-free review of extended analytical documents.
- **Metadata and Heuristics:** Micro-labels and confidence ratings employ uppercase or tracked medium weights (`label-sm`, `label-md`) to clearly delineate system-generated metrics from user input.
- **Monospaced Complement:** System monospaced font declarations are reserved exclusively for diff hashes, perplexity matrices, and raw character counts.

## Layout & Spacing

A strict 8px spatial grid underpins all element relationships, padding tokens, and structural alignments.

### Grid & Structural Paneling
- **Desktop Workflow (1200px+):** Tri-pane layout utilizing a 64px collapsed/240px expanded navigation rail (`#15161D`), a fluid central editor panel (`#101116`), and an auxiliary 360px inspection sidebar (`#15161D`).
- **Gutter Rhythm:** Internal inspector columns use 24px (`gutter: 1.5rem`) gaps, compressing to 16px (`1rem`) on compact views.
- **Canvas Margins:** Section-level wrapper margins anchor at 32px (`2rem`) for wide viewports and collapse to 16px (`1rem`) on mobile viewports.
- **Component Padding Scale:**
  - Micro toggles and badge insets: `space-xs` (4px) to `space-sm` (8px).
  - Form fields and button interiors: `space-sm` vertical (8px) by `space-md` horizontal (16px).
  - Cards, panels, and modals: `space-lg` (24px) for dense data, `space-xl` (32px) for unencumbered reading canvases.

## Elevation & Depth

Depth is established primarily through tonal surface tiers and crisp low-contrast outlines rather than dramatic drops. This keeps the interface developer-grade, technical, and precise.

### Layering Architecture
- **Layer 0 (Base Canvas):** `#101116` — Full-screen root wrapper and primary editor backplane.
- **Layer 1 (Recessed Inputs):** `#14151C` — Text fields, source inputs, and log viewers; framed with a 1px border of `#2D2F3A`.
- **Layer 2 (Sidebar & Structural Shelves):** `#15161D` — Bordered on edge seams by `1px solid #2D2F3A`.
- **Layer 3 (Inspector Panels & Cards):** `#1B1D26` — Bordered with `1px solid #2D2F3A` with an ambient glow of `0 4px 20px -2px rgba(0, 0, 0, 0.45)`.
- **Layer 4 (Modals & Command Palette):** `#1B1D26` — Elevated above the interface with a 1px border of `#3E4252` and a double shadow: `0 16px 40px -8px rgba(0, 0, 0, 0.7)`, accented by a subtle primary atmospheric ring (`0 0 0 1px rgba(139, 92, 246, 0.15)`).

## Shapes

The design system adopts roundedness level `2`, balancing modern software ergonomics with industrial precision. Corner radiuses follow an intentional progression that prevents visual distortion at nested boundaries:

- **Inner Interactive Tokens (Buttons, Inputs, Badges):** 8px (`0.5rem`) radius ensures sharp, crisp action targets without feeling rounded or childish.
- **Surrounding Cards and Containers:** 10px to 12px (`rounded-lg`, ~`0.75rem`–`1rem`) radius, providing gentle, modern containment while preserving clean grid lines.
- **Flyout Drawers and Overlays:** 16px (`rounded-xl`, `1.5rem`) radius for elevated, transient overlays.
- **Status Pills and Verification Chips:** Full-pill radiuses (9999px) exclusively reserved for compact verification labels to signal atomic metadata.

## Components

### Buttons
- **Primary:** Filled `#8B5CF6` background, `#FFFFFF` text, 8px border radius, font `label-md` weight 600. Subtle hover transition to `#7C3AED` with a focused ring of `0 0 0 2px #101116, 0 0 0 4px #8B5CF6`.
- **Secondary:** Surface `#1B1D26`, 1px outline `#2D2F3A`, text `#E2E8F0`. Hover transitions border to `#8B5CF6` and text to `#FFFFFF`.
- **Ghost / Tool:** Transparent background, text `#94A3B8`. Hover yields `#1B1D26` fill and `#E2E8F0` text.
- **Action Verification:** Active state triggers a discrete animated left-border highlight in `#10B981` (Humanized) or `#8B5CF6` (Processing).

### Text Inputs & Editor Viewports
- Background `#14151C`, border `1px solid #2D2F3A`, text `#F8FAFC`, placeholder `#64748B`.
- Focused state: Border transitions to `#8B5CF6` with an inner shadow ring of `0 0 0 1px #8B5CF6`.
- Monospace metadata footer docked inside the input container for word count, character density, and real-time perplexity markers.

### Trust & Verification Chips
- Compact badges (24px height, 8px horizontal padding, 9999px radius).
- **Passed/Human:** Background `rgba(16, 185, 129, 0.12)`, text `#10B981`, 1px border `rgba(16, 185, 129, 0.25)`.
- **Review/AI Risk:** Background `rgba(245, 158, 11, 0.12)`, text `#F59E0B`, 1px border `rgba(245, 158, 11, 0.25)`.
- **High AI Signature:** Background `rgba(239, 68, 68, 0.12)`, text `#EF4444`, 1px border `rgba(239, 68, 68, 0.25)`.

### Cards & Inspector Panels
- Background `#1B1D26`, border `1px solid #2D2F3A`, border-radius 10px.
- Panel headers feature a subtle bottom border (`1px solid #2D2F3A`) separating header controls from dynamic score dials, entropy heatmaps, and synonym replacements.

### Selection Controls (Checkboxes & Radios)
- Box dimension: 16x16px, background `#14151C`, border `1px solid #2D2F3A`, border-radius 4px (checkbox) or circular (radio).
- Selected state: Fill `#8B5CF6` with white checkmark/dot icon. Hover state displays `rgba(139, 92, 246, 0.2)` expansion glow.

### Specialized Verification Components
- **Diff Comparison Stream:** Parallel viewports with added humanized passages highlighted in `rgba(16, 185, 129, 0.15)` and removed generative syntaxes struck through with `rgba(239, 68, 68, 0.2)`.
- **Perplexity Gauge:** Segmented linear meter utilizing a gradient transition between `#10B981`, `#F59E0B`, and `#8B5CF6` against a track of `#14151C`.