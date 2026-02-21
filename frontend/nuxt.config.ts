// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: true },
  pages: true,

  routeRules: {
    '/': { ssr: false },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
    },
  },

  nitro: process.env.NODE_ENV === 'development'
    ? {
        devProxy: {
          '/api/': {
            target: 'http://localhost:8000/api',
            changeOrigin: true,
          },
        },
      }
    : {},

  css: ['@fortawesome/fontawesome-free/css/all.css'],
})

