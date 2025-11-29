/** @type {import('tailwindcss').Config} */
export default {
    content: [
        './src/templates/**/*.html',
        './src/static/js/**/*.js',
    ],
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
            colors: {
                slate: {
                    850: '#1e293b',
                    900: '#0f172a',
                    950: '#020617',
                },
                background: '#0a0a0a',
                foreground: '#fafafa',
                card: '#18181b',
                'card-foreground': '#fafafa',
                primary: '#22d3ee',
                'primary-foreground': '#0a0a0a',
                secondary: '#27272a',
                'secondary-foreground': '#fafafa',
                muted: '#27272a',
                'muted-foreground': '#a1a1aa',
                accent: '#fbbf24',
                'accent-foreground': '#0a0a0a',
                destructive: '#ef4444',
                'destructive-foreground': '#fafafa',
                success: '#22c55e',
                border: '#27272a',
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
    ],
};
