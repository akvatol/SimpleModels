"""HTML report generator for conformer generation and optimization results."""

import datetime
import html
import io
from pathlib import Path
from typing import Any

from ase.io import write as ase_write

EV_TO_KCAL = 23.0605  # 1 eV = 23.0605 kcal/mol


def _atoms_to_xyz_string(atoms: Any) -> str:
    """Convert ASE Atoms object to XYZ format string."""
    try:
        buf = io.StringIO()
        ase_write(buf, atoms, format="xyz")
        return buf.getvalue()
    except Exception:
        return ""


def _get_formula(atoms: Any) -> str:
    try:
        return atoms.get_chemical_formula()
    except Exception:
        return "Unknown"


def _get_energy(conf: dict[str, Any]) -> float | None:
    """Extract energy from conformer dict (eV)."""
    energy = conf.get("energy")
    if energy is None:
        atoms = conf.get("atoms")
        if atoms is not None:
            try:
                energy = atoms.get_potential_energy()
            except Exception:
                pass
    return energy


class Reporter:
    """Generates a self-contained HTML report for conformer generation and optimization results."""

    def generate_html_report(
        self,
        selected_conformers: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> str:
        """Generate an HTML report with 3D viewer, energy table, and distribution chart.

        :param selected_conformers: List of conformer dicts with 'atoms' and optionally 'energy' keys.
        :param config: Pipeline configuration dict.
        :return: Path to the written HTML file.
        """
        output_dir = Path(config.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        report_filename = config.get("report_path", "report.html")
        report_path = output_dir / report_filename
        report_path.parent.mkdir(parents=True, exist_ok=True)

        html = self._build_html(selected_conformers, config)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        return str(report_path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_html(
        self,
        conformers: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> str:
        n = len(conformers)
        formula = _get_formula(conformers[0]["atoms"]) if n > 0 and conformers[0].get("atoms") else "N/A"
        formula_escaped = html.escape(formula)
        generator_type = config.get("generator_type", "unknown")
        generator_type_escaped = html.escape(str(generator_type))
        optimized = config.get("enable_optimization", False)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Collect energies and XYZ data
        energies_ev: list[float | None] = [_get_energy(c) for c in conformers]
        valid_energies = [e for e in energies_ev if e is not None]
        min_energy = min(valid_energies) if valid_energies else None

        rel_energies_kcal: list[float | None] = []
        for e in energies_ev:
            if e is not None and min_energy is not None:
                rel_energies_kcal.append(round((e - min_energy) * EV_TO_KCAL, 4))
            else:
                rel_energies_kcal.append(None)

        xyz_strings: list[str] = []
        for c in conformers:
            atoms = c.get("atoms")
            xyz_strings.append(_atoms_to_xyz_string(atoms) if atoms is not None else "")

        # Build JS data arrays
        js_xyz_array = self._js_string_array(xyz_strings)
        js_rel_energies = self._js_number_array(rel_energies_kcal)
        js_abs_energies = self._js_number_array(energies_ev)
        js_labels = "[" + ", ".join(f'"#{i + 1}"' for i in range(n)) + "]"

        # Build table rows
        table_rows = self._build_table_rows(conformers, energies_ev, rel_energies_kcal)

        # Summary cards
        energy_range = ""
        if valid_energies:
            energy_range = f"{(max(valid_energies) - min(valid_energies)) * EV_TO_KCAL:.3f} kcal/mol"

        status_badge = (
            '<span class="badge badge-optimized">Post-Optimization</span>'
            if optimized
            else '<span class="badge badge-generated">Post-Generation</span>'
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Conformer Report — {formula_escaped}</title>
  <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f1117;
      --surface: #1a1d27;
      --surface2: #252836;
      --border: #2e3147;
      --accent: #6c8ef5;
      --accent2: #54d9a3;
      --warn: #f5a623;
      --text: #e2e4f0;
      --muted: #7b80a0;
      --danger: #f56c6c;
      --radius: 10px;
      --shadow: 0 4px 24px rgba(0,0,0,0.4);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}
    /* ── Header ── */
    header {{
      background: linear-gradient(135deg, #1a1d27 0%, #12152a 100%);
      border-bottom: 1px solid var(--border);
      padding: 24px 40px;
      display: flex;
      align-items: center;
      gap: 20px;
    }}
    header .logo {{
      font-size: 2rem;
      font-weight: 800;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    header .meta {{ flex: 1; }}
    header .meta h1 {{ font-size: 1.4rem; font-weight: 700; }}
    header .meta p {{ font-size: 0.85rem; color: var(--muted); margin-top: 4px; }}
    .badge {{
      display: inline-block;
      padding: 3px 12px;
      border-radius: 99px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      margin-left: 10px;
    }}
    .badge-optimized {{ background: #1a3a2a; color: var(--accent2); border: 1px solid var(--accent2); }}
    .badge-generated  {{ background: #1a2a3a; color: var(--accent);  border: 1px solid var(--accent);  }}
    /* ── Layout ── */
    .page {{ max-width: 1400px; margin: 0 auto; padding: 32px 40px; }}
    /* ── Summary cards ── */
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow);
    }}
    .card .label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }}
    .card .value {{ font-size: 1.6rem; font-weight: 700; margin-top: 6px; color: var(--accent); }}
    .card .sub   {{ font-size: 0.8rem;  color: var(--muted); margin-top: 4px; }}
    /* ── Two-column layout ── */
    .two-col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 32px;
    }}
    @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
    /* ── Panel ── */
    .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow);
    }}
    .panel h2 {{
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 10px;
    }}
    /* ── 3D Viewer ── */
    #viewer-wrap {{ position: relative; }}
    #mol-viewer {{
      width: 100%;
      height: 380px;
      background: #0a0c14;
      border-radius: 8px;
      overflow: hidden;
    }}
    .viewer-controls {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }}
    .viewer-controls label {{ font-size: 0.85rem; color: var(--muted); }}
    .viewer-controls select, .viewer-controls button {{
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 0.85rem;
      cursor: pointer;
    }}
    .viewer-controls button:hover {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
    #conf-label {{
      font-size: 0.8rem;
      color: var(--accent2);
      background: var(--surface2);
      border-radius: 6px;
      padding: 4px 10px;
    }}
    /* ── Chart ── */
    #chart-container {{ position: relative; height: 380px; }}
    .offline-note {{
      margin-top: 8px;
      font-size: 0.82rem;
      color: var(--warn);
    }}
    /* ── Table ── */
    .table-wrap {{ overflow-x: auto; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    thead tr {{ background: var(--surface2); }}
    thead th {{
      padding: 12px 14px;
      text-align: left;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.07em;
      border-bottom: 2px solid var(--border);
    }}
    tbody tr {{ border-bottom: 1px solid var(--border); transition: background 0.15s; }}
    tbody tr:hover {{ background: var(--surface2); cursor: pointer; }}
    tbody tr.active {{ background: #1a2a3a; }}
    tbody td {{ padding: 11px 14px; }}
    td.rank {{ font-weight: 700; color: var(--accent); }}
    td.energy-rel {{ color: var(--accent2); font-weight: 600; }}
    td.energy-abs {{ color: var(--muted); font-size: 0.82rem; }}
    .medal {{ margin-right: 4px; }}
    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 24px;
      font-size: 0.78rem;
      color: var(--muted);
      border-top: 1px solid var(--border);
      margin-top: 40px;
    }}
  </style>
</head>
<body>

<header>
  <div class="logo">⬡</div>
  <div class="meta">
    <h1>Conformer Report &mdash; <code>{formula_escaped}</code> {status_badge}</h1>
    <p>
      Generated on {timestamp} &nbsp;|&nbsp; Generator: <strong>{generator_type_escaped}</strong>
      &nbsp;|&nbsp; SimpleModels Pipeline
    </p>
  </div>
</header>

<div class="page">

  <!-- Summary cards -->
  <div class="cards">
    <div class="card">
      <div class="label">Conformers</div>
      <div class="value">{n}</div>
      <div class="sub">selected</div>
    </div>
    <div class="card">
      <div class="label">Formula</div>
        <div class="value" style="font-size:1.2rem">{formula_escaped}</div>
      <div class="sub">chemical formula</div>
    </div>
    <div class="card">
      <div class="label">Lowest Energy</div>
      <div class="value" style="font-size:1.2rem">{f"{min_energy:.4f} eV" if min_energy is not None else "N/A"}</div>
      <div class="sub">{f"{min_energy * EV_TO_KCAL:.3f} kcal/mol" if min_energy is not None else ""}</div>
    </div>
    <div class="card">
      <div class="label">Energy Range</div>
      <div class="value" style="font-size:1.1rem">{energy_range or "N/A"}</div>
      <div class="sub">max − min spread</div>
    </div>
    <div class="card">
      <div class="label">Optimization</div>
      <div class="value" style="font-size:1rem; color: {"var(--accent2)" if optimized else "var(--warn)"}">
        {"ON" if optimized else "OFF"}
      </div>
      <div class="sub">{config.get("optimizer_type", "dft") if optimized else "not applied"}</div>
    </div>
  </div>

  <!-- 3D viewer + chart -->
  <div class="two-col">

    <div class="panel">
      <h2>3D Structure Viewer</h2>
      <div class="viewer-controls">
        <label>Conformer:</label>
        <select id="conf-select" onchange="loadConformer(this.value)">
          {self._build_select_options(n, rel_energies_kcal)}
        </select>
        <span id="conf-label">Select a conformer</span>
        <button onclick="toggleStyle()">Toggle Style</button>
        <button onclick="viewer.spin(!spinning); spinning=!spinning">Spin</button>
      </div>
      <div id="mol-viewer"></div>
    </div>

    <div class="panel">
      <h2>Relative Energy Distribution</h2>
      <div id="chart-container">
        <canvas id="energyChart"></canvas>
      </div>
    </div>

  </div>

  <!-- Conformer table -->
  <div class="panel">
    <h2>Conformer Rankings</h2>
    <div class="table-wrap">
      <table id="conf-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Rank</th>
            <th>Relative Energy (kcal/mol)</th>
            <th>Absolute Energy (eV)</th>
            <th>Formula</th>
            <th>Source File</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </div>
  </div>

</div>

<footer>
  SimpleModels &mdash; Conformer Generation Pipeline &nbsp;|&nbsp; Report generated {timestamp}
</footer>

<script>
// ── Data ──
const xyzData    = {js_xyz_array};
const relEnergy  = {js_rel_energies};
const absEnergy  = {js_abs_energies};
const labels     = {js_labels};

// ── 3Dmol viewer ──
let viewer = null;
let currentStyle = 'stick';
let spinning = false;

function setFallbackMessage(containerId, message) {{
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="offline-note">${{message}}</div>`;
}}

function initViewer() {{
  if (typeof $3Dmol === 'undefined') {{
    setFallbackMessage('mol-viewer', '3D viewer unavailable: failed to load 3Dmol.js (offline or blocked CDN).');
    return;
  }}

  const el = document.getElementById('mol-viewer');
  viewer = $3Dmol.createViewer(el, {{
    backgroundColor: '#0a0c14',
    antialias: true,
  }});
  if (xyzData.length > 0) loadConformer(0);
}}

function loadConformer(idx) {{
  idx = parseInt(idx);
  if (!viewer || !xyzData[idx]) return;
  viewer.clear();
  viewer.addModel(xyzData[idx], 'xyz');
  applyStyle();
  viewer.zoomTo();
  viewer.render();

  // Update label
  const eStr = relEnergy[idx] !== null ? relEnergy[idx].toFixed(3) + ' kcal/mol' : 'N/A';
  document.getElementById('conf-label').textContent = `#${{idx+1}} | ΔE = ${{eStr}}`;

  // Sync select
  document.getElementById('conf-select').value = idx;

  // Highlight table row
  document.querySelectorAll('#conf-table tbody tr').forEach((r, i) => {{
    r.classList.toggle('active', i === idx);
  }});
}}

function applyStyle() {{
  if (!viewer) return;
  viewer.setStyle({{}}, {{}});
  if (currentStyle === 'stick') {{
    viewer.setStyle({{}}, {{stick: {{radius: 0.15}}, sphere: {{scale: 0.3}}}});
  }} else if (currentStyle === 'sphere') {{
    viewer.setStyle({{}}, {{sphere: {{scale: 0.5}}}});
  }} else {{
    viewer.setStyle({{}}, {{line: {{}}}});
  }}
  viewer.render();
}}

function toggleStyle() {{
  const styles = ['stick', 'sphere', 'line'];
  currentStyle = styles[(styles.indexOf(currentStyle) + 1) % styles.length];
  applyStyle();
}}

// Click table row → load conformer
document.querySelectorAll('#conf-table tbody tr').forEach((row, i) => {{
  row.addEventListener('click', () => loadConformer(i));
}});

// ── Chart.js ──
function initChart() {{
  if (typeof Chart === 'undefined') {{
    setFallbackMessage(
      'chart-container',
      'Energy chart unavailable: failed to load Chart.js (offline or blocked CDN).'
    );
    return;
  }}

  const validPairs = labels
    .map((l, i) => ({{ label: l, e: relEnergy[i] }}))
    .filter(p => p.e !== null);

  const ctx = document.getElementById('energyChart').getContext('2d');
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: validPairs.map(p => p.label),
      datasets: [{{
        label: 'ΔE (kcal/mol)',
        data: validPairs.map(p => p.e),
        backgroundColor: validPairs.map(p =>
          p.e < 1  ? 'rgba(84,217,163,0.8)'  :
          p.e < 5  ? 'rgba(108,142,245,0.8)' :
          p.e < 10 ? 'rgba(245,166,35,0.8)'  :
                     'rgba(245,108,108,0.8)'
        ),
        borderColor:  validPairs.map(p =>
          p.e < 1  ? '#54d9a3' :
          p.e < 5  ? '#6c8ef5' :
          p.e < 10 ? '#f5a623' :
                     '#f56c6c'
        ),
        borderWidth: 1,
        borderRadius: 4,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: ctx => ` ΔE = ${{ctx.parsed.y.toFixed(4)}} kcal/mol`
          }}
        }}
      }},
      scales: {{
        x: {{
          ticks: {{ color: '#7b80a0', maxRotation: 90, font: {{ size: 10 }} }},
          grid:  {{ color: '#2e3147' }},
        }},
        y: {{
          ticks: {{ color: '#7b80a0' }},
          grid:  {{ color: '#2e3147' }},
          title: {{ display: true, text: 'ΔE (kcal/mol)', color: '#7b80a0' }},
        }}
      }}
    }}
  }});
}}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {{
  initViewer();
  initChart();
}});
</script>
</body>
</html>"""

    def _build_table_rows(
        self,
        conformers: list[dict[str, Any]],
        energies_ev: list[float | None],
        rel_energies_kcal: list[float | None],
    ) -> str:
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        rows = []
        for i, (conf, e_ev, e_rel) in enumerate(zip(conformers, energies_ev, rel_energies_kcal)):
            atoms = conf.get("atoms")
            formula = _get_formula(atoms) if atoms is not None else "N/A"
            source = conf.get("file", conf.get("source", "—"))
            if source and len(str(source)) > 40:
                source = "…" + str(source)[-37:]

            formula_escaped = html.escape(formula)
            source_escaped = html.escape(str(source))

            medal = medals.get(i, "")
            rel_str = f"{e_rel:.4f}" if e_rel is not None else "N/A"
            abs_str = f"{e_ev:.6f}" if e_ev is not None else "N/A"

            rows.append(
                f"<tr>"
                f"<td class='rank'>{medal} {i + 1}</td>"
                f"<td>{i + 1}</td>"
                f"<td class='energy-rel'>{rel_str}</td>"
                f"<td class='energy-abs'>{abs_str}</td>"
                f"<td>{formula_escaped}</td>"
                f"<td style='font-size:0.8rem;color:var(--muted)'>{source_escaped}</td>"
                f"</tr>"
            )
        return "\n".join(rows)

    def _build_select_options(self, n: int, rel_energies_kcal: list[float | None]) -> str:
        options = []
        for i in range(n):
            e = rel_energies_kcal[i]
            label = f"#{i + 1}" + (f" — ΔE={e:.3f} kcal/mol" if e is not None else "")
            options.append(f'<option value="{i}">{label}</option>')
        return "\n".join(options)

    @staticmethod
    def _js_string_array(strings: list[str]) -> str:
        escaped = []
        for raw_str in strings:
            # Escape backslashes, backticks, and ${} for JS template safety
            escaped_str = raw_str.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
            escaped.append(f"`{escaped_str}`")
        return "[" + ", ".join(escaped) + "]"

    @staticmethod
    def _js_number_array(numbers: list[float | None]) -> str:
        parts = []
        for n in numbers:
            parts.append("null" if n is None else str(round(n, 6)))
        return "[" + ", ".join(parts) + "]"
