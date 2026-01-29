/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                energy: {
                    green: "#00ff88",
                    blue: "#00d4ff",
                    purple: "#9d00ff",
                },
            },
        },
    },
    plugins: [],
}
