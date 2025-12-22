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
        port: 5173,
        host: '0.0.0.0',
        cors: true,
        proxy: {
            '/api': {
                target: 'http://localhost:20020',
                changeOrigin: true,
            },
            '/ws': {
                target: 'ws://localhost:20020',
                ws: true,
            },
            '/auth': {
                target: 'http://localhost:20880',
                changeOrigin: true,
            },
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
