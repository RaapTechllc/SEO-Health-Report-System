# SEO Health Report - Frontend

A welcoming, modern React UI for the SEO Health Report system.

## Tech Stack
- **React** (Vite)
- **Tailwind CSS** (Styling)
- **Lucide React** (Icons)

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open http://localhost:5173 to see the app.

## Project Structure
- `src/components/`: Reusable UI components (ScoreGauge, ReportViewer, etc.)
- `src/mockData.js`: Sample data structure matching the Python backend output.
- `src/App.jsx`: Main application logic.

## Integration Plan
Currently uses mock data. To integrate with the backend:
1. Create a FastAPI/Flask endpoint that runs the python audit.
2. Update `App.jsx` `handleAnalyze` function to `fetch` from that endpoint.
