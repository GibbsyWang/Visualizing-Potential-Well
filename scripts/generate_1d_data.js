import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const L_MIN = 1.0;
const L_MAX = 5.0;
const L_STEP = 0.05;
const X_POINTS = 200;
const N_MAX = 7;

const energy = (n, L) => (n ** 2 * Math.PI ** 2) / (2 * L ** 2);
const psi = (x, n, L) => Math.sqrt(2 / L) * Math.sin((n * Math.PI * x) / L);

const L_values = [];
for (let L = L_MIN; L <= L_MAX + 1e-9; L += L_STEP) {
  L_values.push(Number(L.toFixed(2)));
}

const n_values = Array.from({ length: N_MAX }, (_, i) => i + 1);

const energy_traces = n_values.map((n) => ({
  n,
  x: L_values,
  y: L_values.map((L) => energy(n, L))
}));

const L_data = L_values.map((L) => {
  const step = L / X_POINTS;
  const x = [];
  for (let i = 0; i <= X_POINTS; i += 1) {
    x.push(Number((i * step).toFixed(6)));
  }

  const perN = n_values.map((n) => {
    const psiArr = x.map((xVal) => psi(xVal, n, L));
    const psi2 = psiArr.map((val) => val ** 2);
    const energyVal = energy(n, L);
    const offset = psiArr.map((val) => (val * 5) / (L ** 2) + energyVal);
    return {
      n,
      psi: psiArr,
      psi2,
      energy: energyVal,
      offset
    };
  });

  const yTicks = perN.map((item) => item.offset[0]);
  const minY = yTicks[0] || 0;
  const maxY = Math.max(...yTicks, 250 / (L ** 2));
  const tickStep = Math.max(1, Math.floor(yTicks.length / 6));
  const tickvals = yTicks.filter((_, i) => i % tickStep === 0).slice(0, 7);
  const ticktext = tickvals.map((val) => val.toFixed(1));

  return {
    L,
    x,
    perN,
    layout3: {
      yaxis: {
        range: [minY, maxY],
        tickvals,
        ticktext
      }
    }
  };
});

const data = {
  meta: {
    L_min: L_MIN,
    L_max: L_MAX,
    L_step: L_STEP,
    x_points: X_POINTS,
    n_max: N_MAX
  },
  L_values,
  n_values,
  energy_traces,
  L_data
};

const outDir = path.resolve(__dirname, '..', 'public', 'data');
fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, '1d-data.json');
fs.writeFileSync(outPath, JSON.stringify(data, null, 2), 'utf8');
console.log(`Wrote ${outPath}`);
