// Vite helper used to define the frontend configuration.
import { defineConfig } from 'vite'

// Allows Vite to understand and build React components.
import react from '@vitejs/plugin-react'

// Connects Tailwind CSS to Vite.
import tailwindcss from '@tailwindcss/vite'


export default defineConfig({
  plugins: [
    // Enable React support.
    react(),

    // Scan React files for Tailwind classes and generate their CSS.
    tailwindcss(),
  ],
})