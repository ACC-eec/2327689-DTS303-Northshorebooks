# UI Style Guide - Fable.co Style Clone

This document describes the design system used in the Northshore Books application, inspired by Fable.co's visual design.

## Layout Grid

### Container
- **Max-width**: 1100-1200px for main content sections
- **Padding**: 
  - Desktop: 64-96px vertical, 24-32px horizontal
  - Mobile: 40-64px vertical, 16-24px horizontal

### Breakpoints
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

### Grid System
- **Product Grid**: 3 columns on desktop, 2 on tablet, 1 on mobile
- **Gap**: 24-32px between grid items

---

## Typography

### Font Families
- **Serif Display**: 'DM Serif Display' (Google Fonts) - for headlines and section titles
- **Sans**: 'Inter' (Google Fonts) - for body text and UI elements

### Type Scale
- **Hero Serif**: `clamp(44px, 5vw, 72px)` with line-height 0.95-1.05
- **Section Serif**: 32-44px
- **Page Title**: `clamp(32px, 4vw, 44px)`
- **Body**: 16-18px, line-height 1.5-1.7
- **Small Meta** (price, author): 14-15px

### Typography Usage
- Headlines: Serif font, tight letter spacing (-0.02em)
- Body text: Sans font, relaxed line height
- UI elements: Sans font, medium weight (500)

---

## Spacing System

### Spacing Tokens
- `--spacing-xs`: 8px
- `--spacing-sm`: 16px
- `--spacing-md`: 24px
- `--spacing-lg`: 32px
- `--spacing-xl`: 64px
- `--spacing-2xl`: 96px

### Usage
- Section padding: `--spacing-xl` to `--spacing-2xl`
- Component gaps: `--spacing-md` to `--spacing-lg`
- Internal spacing: `--spacing-xs` to `--spacing-sm`

---

## Color Tokens

### Primary Colors
- `--forest-900`: #1a4d3a (deep hero green)
- `--forest-800`: #2d5a47 (pattern tones)
- `--forest-700`: #3d6b54 (lighter green)

### Neutral Colors
- `--cream-50`: #faf8f5 (warm off-white)
- `--ink-900`: #1a1a1a (near-black text/icons)
- `--muted-600`: #6b7280 (muted gray secondary text)
- `--border-200`: #e5e7eb (light border)
- `--white`: #ffffff

### Usage
- Backgrounds: `--white`, `--cream-50`, `--forest-900`
- Text: `--ink-900` (primary), `--muted-600` (secondary)
- Borders: `--border-200`
- Icons: `--ink-900` (on light), `--white` (on dark)

---

## Component Specifications

### Navbar
- **Height**: 72px desktop, 64px mobile
- **Background**: White (or transparent overlay on dark hero)
- **Layout**: Hamburger (left) → Brand (center) → User/Cart icons (right)
- **Spacing**: 24px horizontal padding minimum
- **Border**: 1px solid `--border-200` at bottom

### Buttons
- **Pill Button**: 
  - Border-radius: `--radius-pill` (9999px)
  - Padding: 14-16px vertical, 26-30px horizontal
  - Background: White with soft shadow
  - Text: Black, medium weight

- **Small Button**: 
  - Padding: 8px 16px
  - Font size: 14px

### Search Bar
- **Height**: 56-64px
- **Border-radius**: `--radius-pill` (9999px)
- **Border**: 1px solid `--border-200`
- **Shadow**: Soft shadow (`--shadow-soft`)
- **Search Icon**: Black circular button (44-48px) embedded at right

### Product Cards
- **Image**: 
  - Aspect ratio: 2:3
  - Border-radius: `--radius-card` (16px)
  - Shadow: Minimal (`--shadow-card`)

- **Text Layout**:
  - Title: Sans, medium weight, 18px
  - Author: Sans, lighter, 14px, muted color
  - Price: Sans, medium weight, 16px, spaced below

### Hero Sections

#### Dark Green Hero
- **Background**: `--forest-900` with subtle geometric pattern
- **Text**: White
- **Layout**: Left side (headline + CTA), Right side (illustration placeholder)
- **Headline**: Large serif, 2 lines, tight letter spacing

#### Cream Hero
- **Background**: `--cream-50`
- **Text**: `--ink-900`
- **Layout**: Centered
- **Headline**: Giant serif, dramatic scale
- **Accent**: Hand-drawn green scribble (SVG) overlaying one word

---

## Component Geometry Tokens

- `--radius-pill`: 9999px (fully rounded)
- `--radius-card`: 16px (tune 14-18px)
- `--icon`: 24px (icon size)
- `--nav-h`: 72px (navbar height)

### Shadows
- `--shadow-soft`: `0 8px 24px rgba(0, 0, 0, 0.06)` (buttons, search)
- `--shadow-card`: `0 2px 8px rgba(0, 0, 0, 0.04)` (product cards)

---

## Interaction States

### Hover
- **Buttons**: Slight transform (translateY(-1px)), increased shadow
- **Links**: Opacity 0.7
- **Icon Buttons**: Background color change (`--border-200`)

### Focus
- **Visible Focus Ring**: 2px solid `--ink-900`, 2px offset
- **All interactive elements**: Must have visible focus state

### Active
- **Buttons**: Slight scale down (0.98)
- **Links**: Opacity 0.5

### Disabled
- **Opacity**: 0.5
- **Cursor**: not-allowed
- **No hover effects**

---

## Component Classes

### Layout
- `.container` - Max-width container with padding
- `.grid-3` - 3-column responsive grid

### Navigation
- `.nav` - Navbar container
- `.nav-brand` - Brand mark and text
- `.icon-btn` - Icon button (24px)

### Buttons
- `.btn` - Base button
- `.btn--pill` - Pill-shaped button
- `.btn--primary` - Primary button (white with shadow)
- `.btn--small` - Small button
- `.btn--danger` - Danger button (red)

### Hero
- `.hero--dark` - Dark green hero section
- `.hero--cream` - Cream hero section

### Forms
- `.auth-form-container` - Authentication form container
- `.auth-form` - Form layout
- `.form-group` - Form field group
- `.form-input` - Text input
- `.form-errors` - Error message container

### Product
- `.product-card` - Product card container
- `.product-card-image` - Product image
- `.product-card-title` - Product title
- `.product-card-author` - Product author
- `.product-card-price` - Product price

### Search
- `.search-pill` - Search bar container

### Orders
- `.basket-item` - Basket item container
- `.order-card` - Order card container
- `.order-detail` - Order detail layout

---

## Visual QA Checklist

Compare implementation against Fable.co screenshots:

- [ ] Navbar spacing matches (24px horizontal padding)
- [ ] Headline scale matches (clamp(44px, 5vw, 72px))
- [ ] Pill shapes are fully rounded (9999px radius)
- [ ] Grid rhythm matches (24-32px gaps)
- [ ] Product cards have minimal shadow
- [ ] Typography hierarchy matches (serif for headlines, sans for body)
- [ ] Color palette matches (forest green, cream, ink)
- [ ] Icon style matches (thin stroke, 24px, monochrome)
- [ ] Spacing feels "breathing" and editorial
- [ ] Mobile responsive (1-2 columns on mobile/tablet)

---

## Accessibility

### Requirements
- **Focus Rings**: Visible on all interactive elements
- **Contrast**: Minimum WCAG AA (4.5:1 for text)
- **Semantic HTML**: Proper heading hierarchy, landmarks
- **Alt Text**: All images have descriptive alt text
- **Keyboard Navigation**: All functionality accessible via keyboard

### Implementation
- Focus rings: 2px solid outline with 2px offset
- Color contrast: Tested against WCAG guidelines
- Semantic HTML: Proper use of `<nav>`, `<main>`, `<footer>`, headings
- ARIA labels: Used for icon-only buttons

---

## Implementation Notes

- **No CSS Frameworks**: Plain CSS only (no Tailwind, Bootstrap, etc.)
- **Mobile-First**: Styles written mobile-first, enhanced for larger screens
- **Component-Based**: Reusable classes, no hardcoded page-specific styles
- **Original Content**: All content is original (no Fable text/images/logos copied)
- **Minimal JavaScript**: Vanilla JS only if needed for basic interactions

---

## File Locations

- **CSS**: `static/assets/css/fable-clone.css`
- **Icons**: `static/assets/icons/*.svg`
- **Templates**: `templates/*.html`
