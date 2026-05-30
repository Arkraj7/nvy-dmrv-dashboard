import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://arkraj7.github.io/nvy-dmrv-dashboard',
  outDir: './dist',
  publicDir: './public',
  srcDir: './src',
  build: {
    assets: 'assets',
  },
  server: {
    port: 4321,
  },
});
