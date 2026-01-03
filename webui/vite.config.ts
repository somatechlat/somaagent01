import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
    root: '.',
    base: '/',

    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
            '@components': resolve(__dirname, 'src/components'),
            '@views': resolve(__dirname, 'src/views'),
            '@stores': resolve(__dirname, 'src/stores'),
            '@services': resolve(__dirname, 'src/services'),
            '@styles': resolve(__dirname, 'src/styles'),
            '@utils': resolve(__dirname, 'src/utils'),
        },
    },

    server: {
        port: 30173,  // Cluster pattern: 30xxx for frontend
        host: '0.0.0.0',
        cors: true,
        proxy: {
            // Django Ninja API
            '/api/v2': {
                target: 'http://localhost:8010',
                changeOrigin: true,
            },
            // Legacy/Fallback (If needed, but VIBE rules say pure Django)
            '/static': {
                target: 'http://localhost:8010',
                changeOrigin: true,
            }
        },
    },

    build: {
        outDir: 'dist',
        emptyOutDir: true,
        sourcemap: true,
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'index.html'),
            },
        },
    },

    esbuild: {
        target: 'esnext',
    },
});
