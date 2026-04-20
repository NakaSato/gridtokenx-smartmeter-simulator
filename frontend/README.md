This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

---

## API Reference (AI & Forecasting)

The following endpoints are critical for implementing the AI Dashboard and Scenario Lab:

### AI Forecasting & Scenario Analysis
- `POST /api/v1/forecast/scenario` — **[NEW]** What-If analysis (Heatwaves, Tourist surges).
- `GET /api/v1/forecast/dual-target` — 24h forecast for Load_Tao (Yellow) vs Capacity_115kV (Blue).
- `GET /api/v1/forecast/constraints` — Bottleneck detection and BESS requirements.
- `GET /api/v1/forecast/demographics` — Daily Active Population (DAP) metrics for Tao/Phangan.
- `GET /api/v1/forecast/24h` — Legacy edge forecasting with MAPE validation.
- `POST /api/v1/forecast/train` — Retrain the LightGBM forecasting models.
