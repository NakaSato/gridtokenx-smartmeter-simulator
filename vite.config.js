import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
    root: 'src/static',
    base: '/',

    build: {
        outDir: '../../dist/static',
        emptyOutDir: true,
        manifest: true,
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'src/static/js/dashboard.js'),
            },
            output: {
                entryFileNames: 'js/[name].js',
                chunkFileNames: 'js/[name].js',
                assetFileNames: (assetInfo) => {
                    const info = assetInfo.name.split('.');
                    const ext = info[info.length - 1];
                    if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
                        return `images/[name][extname]`;
                    } else if (/woff2?|ttf|otf|eot/i.test(ext)) {
                        return `fonts/[name][extname]`;
                    }
                    return `[ext]/[name][extname]`;
                },
            },
        },
        sourcemap: true,
        minify: 'esbuild', // Use esbuild (faster and included with Vite)
    },

    server: {
        port: 5173,
        strictPort: false,
        proxy: {
            '/api': {
                target: 'http://localhost:8005',
                changeOrigin: true,
            },
            '/ws': {
                target: 'ws://localhost:8005',
                ws: true,
            },
        },
        cors: true,
    },

    resolve: {
        alias: {
            '@': resolve(__dirname, 'src/static'),
            '@js': resolve(__dirname, 'src/static/js'),
            '@css': resolve(__dirname, 'src/static/css'),
        },
    },

    css: {
        postcss: './postcss.config.js',
    },

    optimizeDeps: {
        include: ['chart.js', 'lucide'],
    },
});
