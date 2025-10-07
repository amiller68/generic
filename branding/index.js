// Main entry point for the branding package

const tokens = require('./core/tokens.json');
const tailwindPreset = require('./tailwind/preset.js');

module.exports = {
  tokens,
  tailwindPreset,
  // Helper to get CSS variable value
  getCSSVariable: (name, mode = 'light') => {
    const themeTokens = mode === 'dark' ? tokens.colors.semantic.dark : tokens.colors.semantic.light;

    // Navigate nested properties
    const keys = name.split('.');
    let value = themeTokens;
    for (const key of keys) {
      value = value?.[key];
      if (value && typeof value === 'object' && value.DEFAULT) {
        value = value.DEFAULT;
      }
    }
    return value;
  },
  // Helper to generate CSS variables string
  generateCSSVariables: (mode = 'light') => {
    const themeTokens = mode === 'dark' ? tokens.colors.semantic.dark : tokens.colors.semantic.light;
    let css = '';

    const processTokens = (obj, prefix = '--') => {
      for (const [key, value] of Object.entries(obj)) {
        if (typeof value === 'object') {
          if (value.DEFAULT) {
            css += `  ${prefix}${key}: ${value.DEFAULT};\n`;
            css += `  ${prefix}${key}-foreground: ${value.foreground};\n`;
          } else {
            processTokens(value, `${prefix}${key}-`);
          }
        } else {
          css += `  ${prefix}${key}: ${value};\n`;
        }
      }
    };

    processTokens(themeTokens);
    return css;
  }
};