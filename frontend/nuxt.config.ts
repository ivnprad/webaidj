// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: true },
  pages:true,
  nitro: {
    devProxy: {
      '/api/': {
        target: 'http://localhost:8000/api',
        changeOrigin: true,
      },
    },
  },
  css: [
    '@fortawesome/fontawesome-free/css/all.css',
  ],
})
