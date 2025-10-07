# Shared Brand Assets

This directory contains all shared logos, icons, and favicons for the platform.

## Files

- `favicon.ico` - Standard favicon (16x16, 32x32, 48x48)
- `favicon.png` - PNG version of favicon
- `icon.png` - Application icon (larger format)
- `icon.svg` - Vector version of application icon

## Usage

All projects should symlink to these assets rather than maintaining their own copies:

### Python
```bash
cd py/static
ln -s ../../branding/assets/favicon.ico .
ln -s ../../branding/assets/icon.svg .
```

### TypeScript/Next.js
```bash
cd ts/apps/next/public
ln -s ../../../../branding/assets/favicon.ico .
ln -s ../../../../branding/assets/icon.svg .
```

## Updating Icons

To update icons across all projects:
1. Replace the files in this directory
2. All projects using symlinks will automatically get the updated versions

## Generating Favicons

When you need different sizes, use the source `icon.svg` or `icon.png` to generate them.