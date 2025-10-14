# Barones Free Space Cleaner Website

This directory contains the source code for the project website.

## Technology Stack

- **Framework**: React with Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Deployment**: Manus deployment platform

## Local Development

```bash
# Install dependencies
pnpm install

# Run development server
pnpm run dev

# Build for production
pnpm run build
```

## Deployment

The website is deployed at: https://barones-nrc69p.manus.space

To deploy updates:
1. Make changes to the source files
2. Build the project: `pnpm run build`
3. Deploy using Manus deployment tools

## File Structure

- `src/` - React source code
  - `App.jsx` - Main application component
  - `App.css` - Application styles
  - `assets/` - Images and static assets
  - `components/` - Reusable UI components
- `public/` - Static files
  - `downloads/` - Package files (.deb, .rpm)
- `index.html` - HTML entry point
- `vite.config.js` - Vite configuration
- `tailwind.config.js` - Tailwind CSS configuration

## Updating Package Downloads

When releasing a new version:

1. Copy new .deb and .rpm files to `public/downloads/`
2. Update version numbers in `src/App.jsx`:
   - Download links (href attributes)
   - Installation commands (code blocks)
3. Rebuild and redeploy

## Notes

- The website source is stored in this repository for easy editing across sessions
- Logo files are in `src/assets/logos/`
- Package files should match the releases in the GitHub releases page

