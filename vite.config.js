import { cpSync } from 'node:fs';
import { resolve } from 'node:path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    {
      name: 'copy-static-website-assets',
      apply: 'build',
      closeBundle() {
        const source = resolve(process.cwd(), 'assets');
        const destination = resolve(process.cwd(), 'dist', 'assets');

        cpSync(source, destination, {
          recursive: true,
          filter: (path) => !path.split(/[\\/]/).includes('destination-photo-source'),
        });
      },
    },
  ],
});
