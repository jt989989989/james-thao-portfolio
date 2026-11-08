import { defineConfig } from 'vite';

export default defineConfig({
  // Relative base so the built app works from any sub-path,
  // e.g. GitHub Pages at /james-thao-portfolio/projects/adhd-my-way/www/
  base: './',
  build: {
    outDir: 'www',
    emptyOutDir: true,
  },
});
