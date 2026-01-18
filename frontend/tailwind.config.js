/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Light theme colors matching LangSmith
        'bg-primary': '#f8f9fa',
        'bg-secondary': '#ffffff',
        'bg-tertiary': '#f3f4f6',
        'bg-canvas': '#fafafa',
        'border': '#e5e7eb',
        'border-primary': '#e5e7eb',
        'border-dark': '#d1d5db',
        'text-primary': '#111827',
        'text-secondary': '#6b7280',
        'text-muted': '#9ca3af',
        // Accent colors matching LangSmith
        'accent-primary': '#7c3aed',    // Purple - main accent
        'accent-secondary': '#6d28d9',  // Darker purple - hover state
        'accent-orange': '#f97316',
        'accent-teal': '#0d9488',
        'accent-purple': '#7c3aed',
        'accent-blue': '#3b82f6',
        'accent-green': '#22c55e',
        'accent-red': '#ef4444',
        'accent-yellow': '#eab308',
      },
    },
  },
  plugins: [],
}
