export default defineNuxtConfig({
  devtools: { enabled: true },

  srcDir: 'app/',
  serverDir: './server',

  modules: [
    "@nuxtjs/tailwindcss",
    "@pinia/nuxt",
    "@vueuse/nuxt",
    "@nuxt/image",
  ],

  css: ["~/assets/css/main.css"],

  // Registrar los componentes por nombre de archivo (sin prefijo de carpeta):
  // el código usa <PatientFormModal>, <StudiesMonthlyChart>, <ProbBar>, etc.
  components: [{ path: "~/components", pathPrefix: false }],

  runtimeConfig: {
    jwtSecret:        process.env.JWT_SECRET,
    jwtRefreshSecret: process.env.JWT_REFRESH_SECRET,
    pythonAiUrl:      process.env.PYTHON_AI_URL || "http://localhost:8000",
    public: {
      appName:    "PeleAnálise",
      appVersion: "1.0.0",
    },
  },

  // Los archivos subidos (uploads/) se sirven con server/routes/uploads/[...path].get.ts

  tailwindcss: { configPath: "tailwind.config.ts" },
  typescript:  { strict: true, typeCheck: false },

  app: {
    head: {
      title: "PeleAnálise — Sistema de Análisis Dermatológico",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
      ],
      link: [
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" },
      ],
    },
  },

  compatibilityDate: "2024-07-01",
});
