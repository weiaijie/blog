import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
export default defineConfig({
  base: '/workbench/', plugins: [vue()],
  build: {outDir: '../site/workbench', emptyOutDir: true, manifest: true},
  server: {proxy: {'/api': 'http://10.1.1.120:18766', '/market-data.json': 'http://10.1.1.120:18766'}},
});
