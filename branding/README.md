# Krondor Platform Branding System

A unified design system and branding solution that shares visual identity across Python and TypeScript applications.

## Overview

This branding system provides:
- **Single source of truth** for design tokens (colors, typography, spacing)
- **Shared Tailwind CSS configuration** as presets
- **CSS variables** for runtime theming (light/dark mode)
- **Animation utilities** for consistent motion design
- **Shared assets** (icons, favicons, logos)

## Architecture

```
branding/
├── core/
│   └── tokens.json         # Design tokens (source of truth)
├── tailwind/
│   └── preset.js          # Shared Tailwind preset
├── styles/
│   ├── variables.css      # CSS custom properties
│   ├── animations.css     # Shared animations
│   └── utilities.css      # Utility classes
├── assets/                # Shared assets (icons, logos)
├── package.json           # npm package configuration
└── index.js              # Main entry point
```

## How It Works

### 1. Design Tokens (`core/tokens.json`)

Central repository of all design values:
- **Colors**: Base palette and semantic color mappings
- **Typography**: Font families and size scales
- **Spacing**: Consistent spacing units
- **Animations**: Duration and timing functions
- **Border Radius**: Corner radius values

### 2. Tailwind Preset (`tailwind/preset.js`)

Exports a Tailwind configuration preset that:
- Maps design tokens to Tailwind utilities
- Defines color variables using CSS custom properties
- Includes keyframe animations
- Provides base theme configuration

### 3. CSS Files

**`variables.css`**: Defines CSS custom properties for runtime theming
- Light mode (default): Black and white theme
- Dark mode: Inverted color scheme
- Semantic color mappings (primary, secondary, accent, etc.)

**`animations.css`**: Reusable animation keyframes and utilities
- Basic: fade-in, slide-up, spin, pulse
- Advanced: blob, float, drift, orbit
- Animation delay utilities

**`utilities.css`**: Common utility and component classes
- Text utilities (gradients, balance)
- Backdrop effects
- Pre-styled components (cards, buttons, inputs)

### 4. Shared Assets (`assets/`)

Common branding assets used across all platforms:
- `favicon.ico`, `favicon.png` - Browser favicons
- `icon.svg`, `icon.png` - Application icons

**Integration**:
- **Next.js**: Symlinked into `ts/apps/next/public/` (committed to git)
- **Python**: Copied to `py/static/` via `make styles` script

## Setup

### Install Dependencies

Install branding package dependencies:
```bash
make branding-setup
# Or directly:
cd branding && npm install
```

### Project Integration

Both Python and TypeScript projects already have branding integration configured.

## Usage

### Python Application

The Python app imports the branding preset and styles:

**`py/tailwind.config.js`**:
```javascript
const brandingPreset = require('../branding/tailwind/preset.js');

module.exports = {
  content: ["./templates/**/*.html", "./src/**/*.py"],
  presets: [brandingPreset],
  theme: {
    extend: {
      // Python-specific extensions
    }
  }
}
```

**`py/styles/main.css`**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Imports shared branding styles */
@import '../../branding/styles/variables.css';
@import '../../branding/styles/animations.css';
@import '../../branding/styles/utilities.css';
```

**Building styles**:
```bash
cd py
make styles        # Build CSS and copy branding assets
make styles-watch  # Watch mode
```

### TypeScript/Next.js Application

The TypeScript app imports the branding preset directly:

**`ts/apps/next/tailwind.config.ts`**:
```typescript
const brandingPreset = require('../../../branding/tailwind/preset.js');

const config: Config = {
  presets: [brandingPreset],
  theme: {
    extend: {
      // TypeScript-specific extensions
    }
  }
}
```

**`ts/apps/next/app/globals.css`**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import '../../../../branding/styles/variables.css';
@import '../../../../branding/styles/animations.css';
```

**Styles are built automatically** by Next.js during `next dev` or `next build`.

## Extending the System

### Adding New Design Tokens

1. Edit `branding/core/tokens.json`:
```json
{
  "colors": {
    "brand": {
      "primary": "#000000",
      "secondary": "#666666"
    }
  }
}
```

2. Update the Tailwind preset in `branding/tailwind/preset.js`

3. Rebuild project styles:
```bash
make styles-py   # Rebuild Python CSS
make build-ts    # Rebuild TypeScript (includes CSS)
```

### Adding Project-Specific Styles

Each project can extend the base theme:

**Python example**:
```javascript
module.exports = {
  presets: [brandingPreset],
  theme: {
    extend: {
      colors: {
        'py-special': '#123456'  // Python-only color
      }
    }
  }
}
```

**TypeScript example**:
```typescript
const config: Config = {
  presets: [brandingPreset],
  theme: {
    extend: {
      animation: {
        'ts-fancy': 'fancy 2s ease-in-out'  // TS-only animation
      }
    }
  }
}
```

### Switching Themes

The system uses CSS variables for theming. To switch themes:

```html
<!-- Light mode (default) -->
<html>

<!-- Dark mode -->
<html class="dark">
```

In JavaScript/TypeScript:
```javascript
// Toggle dark mode
document.documentElement.classList.toggle('dark');
```

## Development Workflow

### Python Development
```bash
cd py
make dev  # Starts dev server (builds styles automatically)
```

Styles are built before the dev server starts. To watch for changes separately:
```bash
make styles-watch
```

### TypeScript Development
```bash
cd ts
make dev  # Next.js handles CSS automatically
```

Next.js watches and rebuilds CSS automatically during development.

### Updating Shared Styles

When you update branding styles:

1. Edit files in `branding/` directory
2. Rebuild project styles:
   - **Python**: Run `make styles-py` or restart `make dev-py`
   - **TypeScript**: Next.js rebuilds automatically

## Maintenance

### Version Control

- Commit all files in `branding/` directory
- Project-specific Tailwind configs are committed
- Built CSS files (`py/static/css/main.css`) should be built locally or in CI/CD

### Common Tasks

**Update branding colors**:
1. Edit `branding/tailwind/preset.js`
2. Run `make styles` in affected projects

**Add new shared animation**:
1. Edit `branding/styles/animations.css`
2. Changes are picked up automatically (imported by projects)

**Update shared assets**:
1. Replace files in `branding/assets/`
2. Python: Run `make styles-py` to copy new assets
3. Next.js: Assets are symlinked, changes reflected immediately

## Benefits

1. **Consistency**: Same visual language across all platforms
2. **Maintainability**: Single source of truth for design decisions
3. **Scalability**: Easy to add new projects
4. **Flexibility**: Each project can extend base theme
5. **Performance**: Shared utilities reduce CSS duplication
6. **Developer Experience**: Simple integration via imports

## Troubleshooting

### CSS not updating in Python app
```bash
# Rebuild CSS
cd py && make styles

# Clear browser cache and reload
```

### TypeScript not finding branding preset
```bash
# Ensure relative path is correct in tailwind.config.ts
const brandingPreset = require('../../../branding/tailwind/preset.js');
```

### Dark mode not working
- Ensure `darkMode: 'class'` is in Tailwind config
- Add `class="dark"` to HTML element
- Check CSS variables are properly imported

### Assets not loading in Python
```bash
# Rebuild styles to copy assets
cd py && make styles
```
