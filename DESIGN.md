---
name: Institutional Intelligence
colors:
  surface: '#101416'
  surface-dim: '#101416'
  surface-bright: '#363a3c'
  surface-container-lowest: '#0b0f10'
  surface-container-low: '#181c1e'
  surface-container: '#1c2022'
  surface-container-high: '#262b2c'
  surface-container-highest: '#313537'
  on-surface: '#e0e3e5'
  on-surface-variant: '#c2c6d7'
  inverse-surface: '#e0e3e5'
  inverse-on-surface: '#2d3133'
  outline: '#8c90a0'
  outline-variant: '#414754'
  surface-tint: '#aec6ff'
  primary: '#aec6ff'
  on-primary: '#002e6b'
  primary-container: '#4f8eff'
  on-primary-container: '#00275e'
  inverse-primary: '#005ac4'
  secondary: '#84cfff'
  on-secondary: '#00344c'
  secondary-container: '#1c9ad4'
  on-secondary-container: '#002d42'
  tertiary: '#b4c8e2'
  on-tertiary: '#1e3246'
  tertiary-container: '#7f93aa'
  on-tertiary-container: '#172b3f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#aec6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004396'
  secondary-fixed: '#c7e7ff'
  secondary-fixed-dim: '#84cfff'
  on-secondary-fixed: '#001e2e'
  on-secondary-fixed-variant: '#004c6c'
  tertiary-fixed: '#d0e4fe'
  tertiary-fixed-dim: '#b4c8e2'
  on-tertiary-fixed: '#071d30'
  on-tertiary-fixed-variant: '#35485d'
  background: '#101416'
  on-background: '#e0e3e5'
  surface-variant: '#313537'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.2'
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  data-mono:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 40px
  xl: 64px
  gutter: 20px
  margin: 32px
---

## Brand & Style

The design system is engineered for professional traders and institutional investors who require an environment of absolute clarity and high-speed execution. The brand personality is "The Quiet Engine"—a sophisticated, always-active intelligence that processes immense complexity and presents only the essential insights.

The visual style is a refined **Glassmorphism**, moving away from "frosted glass" clichés toward a high-fidelity "Crystal UI" aesthetic. It utilizes semi-transparent layers to maintain context across the dashboard, combined with a **Minimalist** layout that prioritizes data density without visual clutter. The emotional response is one of calm control, leveraging deep oceanic blues to lower the cognitive load during high-stakes market activity.

## Colors

The palette is anchored in a deep navy core, simulating the depth and reliability of institutional infrastructure. 

- **Primary & Secondary:** Electric blue (#2F80FF) is reserved for primary actions and active states. Soft cyan (#59C3FF) provides highlights and secondary interactive elements.
- **P&L Semantics:** Profit is indicated by a soft aqua/teal rather than a harsh green, while loss is represented by a muted coral. These "cool" versions of semantic colors maintain the calm mood while ensuring instant legibility.
- **Accents:** Ice blue and Neutral white are used exclusively for typography and data points to maximize contrast against the dark background.
- **Gradients:** Use subtle axial gradients from Midnight blue to Deep navy for large surface areas to prevent visual "dead space."

## Typography

This design system uses a dual-font strategy to balance technical innovation with professional readability. 

**Space Grotesk** is used for headlines, large numbers, and data points. Its geometric, slightly futuristic character reinforces the AI-driven nature of the platform. **Manrope** serves as the primary workhorse for body text, settings, and navigation, providing a calm and balanced reading experience.

Critical financial data (prices, quantities) should utilize the `data-mono` style to ensure numbers align vertically in tables, facilitating quick scanning across columns.

## Layout & Spacing

The design system employs a **Fluid Grid** model designed for ultra-wide displays commonly used in trading desks. The layout is structured on a 12-column grid with generous 20px gutters to prevent information density from becoming overwhelming.

Spacing follows a 4px base unit. Internal component padding should be tight (8px-12px) to maximize data visibility, while external margins between major dashboard modules should be larger (24px-32px) to create distinct visual zones. Large data-heavy sections should use a "modular" approach where users can collapse or expand panels within the grid.

## Elevation & Depth

Hierarchy is established through **Glassmorphism** and tonal layering rather than traditional drop shadows.

- **Level 0 (Background):** Deep navy (#08111F).
- **Level 1 (Modules):** Midnight blue (#10233D) with a 60% opacity and a 20px backdrop-blur. Each module features a 1px border using a gradient of Electric Blue at 20% opacity to "cut" the shape out of the background.
- **Level 2 (Active Overlays/Modals):** High-opacity glass with a subtle outer glow (Electric blue at 10% opacity, 40px blur) to simulate a light-emitting source.
- **Separators:** Use 1px solid lines with 10% opacity white. Never use black or high-contrast lines for separation.

## Shapes

The design system utilizes **Soft** geometry. A base radius of 4px-8px is applied to all modules and input fields. This subtle rounding maintains the "institutional" and "structured" feel while softening the overall technological edge. 

Interactive elements like buttons use the `rounded-lg` (8px) setting. Circular shapes are reserved strictly for status indicators (Active/Inactive) and user avatars to distinguish them from functional UI components.

## Components

- **Buttons:** Primary buttons use a solid Electric Blue to Ice Blue vertical gradient. Secondary buttons use the "Ghost" style: a 1px Ice Blue border with no fill until hover.
- **Input Fields:** Fields are dark (#08111F) with a subtle inner glow. On focus, the border transitions to Soft Cyan with a low-opacity outer glow.
- **Data Cards:** Essential metrics are displayed in cards with large `display-lg` typography. Profit metrics use the Soft Aqua color for the text and a subtle 5% opacity Aqua background tint.
- **Glass Chips:** Categorical tags use a semi-transparent background (15% opacity primary color) with a high-contrast label.
- **AI Insight Module:** A specialized component featuring a continuous, slow-pulsing Electric Blue glow behind its border to indicate active AI computation.
- **Tickers:** Active price tickers should have "flash" states: a temporary text color shift to Soft Aqua (up) or Soft Coral (down) that fades back to Neutral White over 300ms.