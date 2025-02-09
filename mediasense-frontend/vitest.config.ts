/// <reference types="vitest" />

import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'url'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    include: ['tests/**/*.spec.ts'],
    css: {
      modules: {
        classNameStrategy: 'non-scoped'
      }
    },
    deps: {
      inline: [
        'element-plus',
        '@element-plus/icons-vue'
      ]
    },
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    transformMode: {
      web: [/\.[jt]sx$/],
      ssr: [/\.vue$/, /\.[jt]s$/]
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,vue}']
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
}) 