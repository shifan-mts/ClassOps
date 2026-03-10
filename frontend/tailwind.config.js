/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Dark Theme Palette
                dark: {
                    primary: '#005461',
                    secondary: '#0C7779',
                    accent: '#249E94',
                    highlight: '#3BC1A8',
                },
                // Light Theme Palette
                light: {
                    bg: '#F1F3E0',
                    secondary: '#D2DCB6',
                    accent: '#A1BC98',
                    text: '#778873',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
