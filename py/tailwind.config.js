/** @type {import('tailwindcss').Config} */
// Auto-generated from branding/tailwind/preset.js
// DO NOT EDIT DIRECTLY - Edit branding/tailwind/preset.js instead

const brandingPreset = require('../branding/tailwind/preset.js');

module.exports = {
  content: [
    "./templates/**/*.html",
    "./src/**/*.py",
  ],
  presets: [brandingPreset],
  theme: {
    extend: {
      // Python-specific theme extensions can go here
    },
  },
  plugins: [],
}
