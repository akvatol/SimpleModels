# SimpleModels — Implementation Plan

## Current State

The pipeline has 5 stages. Here's what works and what doesn't:

| Stage | Module | Status |
|-------|--------|--------|
| 1. Input parsing | `input_handler.py`, `processing/xyz.py` | **XYZ works**, SMILES is a stub |
| 2. Conformer generation | `conformer_generator.py` | **Done** (Minima Hopping + OpenBabel Confab) |
| 3. Analysis & selection | `analyzer.py` | **Stub** — `NotImplementedError` |
| 4. Optimization | `optimizer.py` | **Stub** — `NotImplementedError` |
| 5. Reporting | `reporter.py` | **Stub** — `NotImplementedError` |

Supporting infrastructure (`config.py`, `main.py`, `utils.py`, `__init__.py`) is fully implemented.

---

## Remaining Work

### Task 1: SMILES Input Processing (`processing/smiles.py`)

**What:** Implement `process_smile(smile: str) -> ase.Atoms` — convert a SMILES string (with optional charge and multiplicity) into an ASE Atoms object with 3D coordinates.

**How:**
- Parse the input line: `SMILES [charge] [multiplicity]` (charge defaults to 0, mult to 1).
- Use RDKit (`rdkit.Chem`) to parse the SMILES and generate a 3D conformer:
  - `Chem.MolFromSmiles()` → `Chem.AddHs()` → `AllChem.EmbedMolecule()` → `AllChem.MMFFOptimizeMolecule()`.
- Extract atomic numbers and 3D positions from the RDKit Mol, construct `ase.Atoms`.
- Store charge and multiplicity in `atoms.info["charge"]` and `atoms.info["spin"]`.

**Dependencies to add:** `rdkit` (via `rdkit-pypi` on PyPI).

**Also fix:** `process_smiles()` — currently appends raw strings, should append the Atoms objects returned by `process_smile()`.

---

### Task 2: Conformer Analyzer (`analyzer.py`)

**What:** Implement `DScribeAnalyzer.cluster_and_select(conformer_files, config) -> List[Dict]` — read conformer XYZ files, compute descriptors, cluster, and select representative conformers.

**How:**
1. **Read conformers** from XYZ files using `ase.io.read()`.
2. **Compute descriptors** using DScribe (e.g. SOAP or ACSF):
   - Create a descriptor object (e.g. `dscribe.descriptors.SOAP`).
   - Compute descriptor matrix for all conformers.
3. **Cluster** conformers using scikit-learn (e.g. `sklearn.cluster.DBSCAN`, `AgglomerativeClustering`, `sklearn.cluster.HDBSCAN` and `MaxMin` from `qc-selector` on descriptor distances).
4. **Select** one representative conformer per cluster — the one with the lowest energy (`atoms.info["energy"]` or from calculator results).
5. **Return** list of dicts, each with keys like `{"path": str, "atoms": Atoms, "energy": float, "cluster_id": int}`.

**Config keys** (under `conformers` or a new `analyzer` section):
- `descriptor_type`: `"soap"` or `"acsf"` (default `"soap"`).
- `n_clusters` or `cluster_threshold`: clustering parameter.
- `soap_rcut`, `soap_nmax`, `soap_lmax`: SOAP hyperparameters.

**Dependencies to add:** `dscribe`.

---

### Task 3: Conformer Optimizer (`optimizer.py`)

**What:** Implement `DFTConformerOptimizer.optimize_conformers(selected_conformers, config) -> List[Dict]` — re-optimize selected conformers with a more accurate calculator.

**How:**
1. For each selected conformer dict, get the `Atoms` object.
2. Attach a calculator. Options:
   - **ORB models** (already a dependency): `orb_models` provides ML potentials that can serve as ASE calculators.
   - Allow config to specify calculator type for future extensibility.
3. Run geometry optimization using `ase.optimize.BFGS` (or `LBFGS`) with `fmax` from config.
4. Update the dict with optimized atoms and new energy.
5. Re-sort by energy and return.

**Config keys** (under `optimizer` section):
- `calculator`: `"orb"` (default) — which calculator backend to use.
- `fmax`: force convergence criterion (default `0.01` eV/Å).
- `max_steps`: max optimization steps (default `500`).
- `orb_model`: which ORB model to load (default `"orb-v3"`).

---

### Task 4: HTML Reporter (`reporter.py`)

**What:** Implement `Reporter.generate_html_report(selected_conformers, config) -> str` — generate an HTML report with conformer data.

**How:**
1. Build an HTML page (use a simple Jinja2 template or raw string formatting):
   - **Summary table**: conformer index, energy (absolute and relative to lowest), cluster ID.
   - **Energy bar chart**: use a simple plotly figure.
   - **3D visualization** (optional/stretch): embed py3Dmol or just link to XYZ files.
   - **Conformer XYZ coordinates**: collapsible sections for each conformer.
2. Write to `config["report_path"]` inside `config["output_dir"]`.
3. Return the path to the generated HTML file.

**Config keys:**
- `report_path`: filename for the report (default `"report.html"`).
- Already exists in DEFAULT_CONFIG.

**Dependencies to add:** `jinja2` (optional — can also use f-strings for a simple template).

---

### Task 5: Tests

**What:** Write pytest tests for the implemented modules.

**Unit tests:**
- `test_config.py`: loading defaults, loading YAML, merging, missing file error.
- `test_xyz_processing.py`: parsing test XYZ files, charge/spin extraction.
- `test_smiles_processing.py`: SMILES to Atoms conversion (requires rdkit).
- `test_conformer_generator.py`: mock-based tests for both generators (verify output file paths, directory creation).
- `test_analyzer.py`: mock-based or small-molecule integration test.
- `test_reporter.py`: verify HTML output file creation and structure.

**Integration test:**
- `test_pipeline.py`: end-to-end test with a small molecule (e.g. ethane from test1.xyz), verifying the full pipeline produces a report.

---

### Task 6: Cleanup & Polish

- **Fix entry point** in `pyproject.toml`: currently `simplemodels.basic:main` — should be `simplemodels.main:main`.
- **Fix bare except** in `processing/xyz.py` (line ~19) — catch specific exceptions.
- **Add `rdkit-pypi`** and `dscribe` to `pyproject.toml` dependencies.
- Verify all relative imports are consistent.

---

## Suggested Implementation Order

```
Task 1 (SMILES)  ──┐
                    ├──→  Task 2 (Analyzer)  ──→  Task 3 (Optimizer)  ──→  Task 4 (Reporter)
Task 6 (Cleanup) ──┘                                                            │
                                                                                 ↓
                                                                          Task 5 (Tests)
```

Tasks 1 and 6 are independent and can be done in parallel. Tasks 2–4 should be sequential since each feeds the next stage. Tests come last to cover the full pipeline.

---

## Dependencies Summary

| Package | Purpose | Currently in pyproject.toml? |
|---------|---------|----------------------------|
| `ase` | Atoms, I/O, optimizers | Yes |
| `minimahopping` | Minima Hopping conformer search | Yes |
| `orb-models` | ML potential calculator | Yes |
| `click` | CLI | Yes |
| `pyyaml` | Config loading | Yes |
| `scikit-learn` | Clustering | Yes |
| `pandas` | Data handling | Yes |
| `seaborn` | Plotting (for reporter) | Yes |
| `rdkit-pypi` | SMILES → 3D coordinates | **No — add** |
| `dscribe` | Molecular descriptors (SOAP/ACSF) | **No — add** |
| `jinja2` | HTML templating (optional) | **No — add if needed** |
