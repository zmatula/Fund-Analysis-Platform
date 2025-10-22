# Feature Specification: Dual Simulation Mode Redesign

## Overview
Redesign the simulation configuration to support two distinct simulation modes:
1. **Past Performance** - Direct simulation of historical returns
2. **Deconstructed Performance** - Multi-stage alpha/beta decomposition with forward beta simulation

---

## 1. Past Performance Mode

### Description
Simulate fund performance using historical investment data directly, with two variants:
- **Gross Return**: Raw investment returns without fees or carry
- **Net Return**: Returns after fees and carry

### User Flow
1. User selects "Past Performance" mode in Configuration tab
2. System runs two parallel simulations:
   - Gross simulation (no fees, no carry, no leverage)
   - Net simulation (with fees, carry, leverage per config)
3. Results tab displays both simulations side-by-side with distribution plots

### Implementation Tasks

#### Task 1.1: Update Configuration UI
**File**: `fund_simulation/app.py`
- Replace current simulation type radio button with two options:
  - "Past Performance"
  - "Deconstructed Performance"
- When "Past Performance" selected, disable leverage/fee/carry inputs (greyed out)
- Add info text explaining that both gross and net returns will be calculated

#### Task 1.2: Update Simulation Engine
**File**: `fund_simulation/fund_simulation/simulation.py`
- Modify `run_single_simulation()` to accept `apply_costs` parameter
- When `apply_costs=False`: Skip leverage, fees, carry calculations
- When `apply_costs=True`: Include all costs as currently implemented

#### Task 1.3: Update Run Simulation Controller
**File**: `fund_simulation/app.py` - `render_run_simulation()`
- When "Past Performance" mode:
  - Run two simulations sequentially:
    1. Gross simulation (`apply_costs=False`)
    2. Net simulation (`apply_costs=True`)
  - Store both in session state as `gross_results`, `net_results`

#### Task 1.4: Update Results Display
**File**: `fund_simulation/app.py` - `render_results()`
- Detect "Past Performance" mode
- Display two-column layout:
  - Left: Gross Return statistics and distributions
  - Right: Net Return statistics and distributions
- Show 4 distribution plots total (Gross MOIC, Gross IRR, Net MOIC, Net IRR)

---

## 2. Deconstructed Performance Mode

### Description
Multi-stage simulation that decomposes returns into alpha and beta components, then reconstructs forward performance.

### Stages
1. **Alpha Simulation**: Excess returns above beta (already implemented)
2. **Beta Simulation**: Forward Monte Carlo simulation of beta index
3. **Gross Performance**: Reconstruct total returns (alpha × beta) without costs
4. **Net Performance**: Reconstruct total returns with fees and carry

### User Flow
1. User selects "Deconstructed Performance" mode
2. User must upload beta price data (required)
3. User configures beta simulation parameters:
   - Simulation horizon (days/years)
   - Number of paths
   - Jump detection quantile (default 0.99)
4. System runs all 4 stages and displays results

---

## 3. Beta Forward Simulation Engine

### Implementation Tasks

#### Task 3.1: Create Beta Simulation Module
**New File**: `fund_simulation/fund_simulation/beta_simulation.py`

**Dependencies**:
```python
import numpy as np
import pandas as pd
from arch import arch_model
from hmmlearn.hmm import GaussianHMM
from scipy import stats
from typing import Tuple, Dict, List
from datetime import datetime, timedelta
```

**Core Function**:
```python
def simulate_beta_forward(
    beta_index: BetaPriceIndex,
    horizon_days: int,
    n_paths: int,
    seed: int = 42,
    jump_quantile: float = 0.99
) -> Tuple[pd.DataFrame, Dict]:
    """
    Generate forward price paths using AR(1)+GJR-GARCH(1,1)-t with HMM regimes and jumps.

    Args:
        beta_index: Historical beta price index
        horizon_days: Simulation horizon in days
        n_paths: Number of Monte Carlo paths
        seed: Random seed for reproducibility
        jump_quantile: Quantile threshold for jump detection (default 0.99)

    Returns:
        Tuple of:
        - DataFrame with shape (horizon_days+1, n_paths), indexed by dates
        - Dict with fitted parameters and diagnostics
    """
```

**Sub-functions**:
```python
def preprocess_prices(beta_index: BetaPriceIndex) -> pd.Series:
    """Convert BetaPriceIndex to time series with log returns."""

def fit_ar_gjr_garch(returns: pd.Series) -> Dict:
    """Fit AR(1)+GJR-GARCH(1,1) with Student-t errors using arch package."""

def fit_hmm_regime(conditional_vol: np.ndarray) -> Dict:
    """Fit 2-state HMM on log-variance for regime switching."""

def detect_jumps(std_residuals: np.ndarray, quantile: float) -> Dict:
    """Estimate Poisson jump parameters from standardized residuals."""

def simulate_single_path(
    horizon: int,
    ar_params: Dict,
    hmm_params: Dict,
    jump_params: Dict,
    last_price: float,
    last_return: float,
    last_vol: float,
    rng: np.random.Generator
) -> np.ndarray:
    """Simulate a single forward price path."""
```

#### Task 3.2: Beta Simulation Configuration UI
**File**: `fund_simulation/app.py` - `render_configuration()`
- Add conditional section when "Deconstructed Performance" selected:
  - Number input: "Simulation Horizon (Days)" (default: 3650 = 10 years)
  - Number input: "Beta Paths" (default: 1000)
  - Slider: "Jump Detection Quantile" (0.90-0.999, default 0.99)
  - Info box: Warning if beta data has < 500 observations

#### Task 3.3: Update SimulationConfiguration Model
**File**: `fund_simulation/fund_simulation/models.py`
```python
@dataclass
class SimulationConfiguration:
    # ... existing fields ...

    # Beta Simulation Parameters
    beta_horizon_days: int = 3650  # 10 years default
    beta_n_paths: int = 1000
    beta_jump_quantile: float = 0.99
```

---

## 4. Performance Reconstruction

### Implementation Tasks

#### Task 4.1: Create Reconstruction Module
**New File**: `fund_simulation/fund_simulation/reconstruction.py`

```python
def reconstruct_gross_performance(
    alpha_results: List[SimulationResult],
    beta_paths: pd.DataFrame,
    beta_start_date: datetime,
    config: SimulationConfiguration
) -> List[SimulationResult]:
    """
    Reconstruct gross returns by combining alpha with simulated beta.

    For each alpha simulation:
    1. For each investment with alpha_moic and days_held
    2. Select a random beta path
    3. Calculate beta_moic over holding period from path
    4. Reconstruct: total_moic = alpha_moic * (beta_moic ^ β)
    5. Aggregate to portfolio level

    Returns:
        List of SimulationResult with reconstructed gross returns
    """

def reconstruct_net_performance(
    gross_results: List[SimulationResult],
    config: SimulationConfiguration
) -> List[SimulationResult]:
    """
    Apply fees, carry, and leverage to gross results.

    Returns:
        List of SimulationResult with net returns after costs
    """
```

#### Task 4.2: Update Run Simulation Controller
**File**: `fund_simulation/app.py` - `render_run_simulation()`

When "Deconstructed Performance" mode:
```python
# Stage 1: Alpha Simulation
alpha_results = run_monte_carlo_simulation(
    investments, config, beta_index=beta_index,
    apply_costs=False  # No costs for alpha
)

# Stage 2: Beta Simulation
beta_paths, beta_diagnostics = simulate_beta_forward(
    beta_index, config.beta_horizon_days,
    config.beta_n_paths, seed=42,
    jump_quantile=config.beta_jump_quantile
)

# Stage 3: Gross Performance Reconstruction
gross_results = reconstruct_gross_performance(
    alpha_results, beta_paths,
    beta_index.prices[-1].date, config
)

# Stage 4: Net Performance Reconstruction
net_results = reconstruct_net_performance(
    gross_results, config
)

# Store all 4 stages
st.session_state.alpha_results = alpha_results
st.session_state.beta_paths = beta_paths
st.session_state.gross_results = gross_results
st.session_state.net_results = net_results
```

---

## 5. Results Display

### Implementation Tasks

#### Task 5.1: Deconstructed Performance Results UI
**File**: `fund_simulation/app.py` - `render_results()`

Layout structure:
```
📊 Deconstructed Performance Results

Stage 1: Alpha (Excess Returns)
├── Statistics table (mean, median, percentiles)
├── Distribution plots (MOIC, IRR)

Stage 2: Beta Forward Simulation
├── Path visualization (spaghetti plot of beta paths)
├── Statistics (mean terminal value, percentiles)
├── Diagnostics (AIC, BIC, regime probs, jump intensity)

Stage 3: Gross Performance (Alpha × Beta)
├── Statistics table
├── Distribution plots (MOIC, IRR)

Stage 4: Net Performance (After Costs)
├── Statistics table
├── Distribution plots (MOIC, IRR)
├── Cost breakdown (fees, carry, leverage costs)
```

#### Task 5.2: Beta Path Visualization
**File**: `fund_simulation/app.py`

Create plotly chart showing:
- 50-100 random beta paths (thin lines)
- Median path (thick line)
- 5th/95th percentile bands (shaded area)
- X-axis: Time (dates)
- Y-axis: Price level

---

## 6. Updated Data Flow

### Past Performance Mode
```
Historical Investments
    ↓
    ├─→ Gross Simulation (no costs)
    └─→ Net Simulation (with costs)
    ↓
Results Display (2 distributions)
```

### Deconstructed Performance Mode
```
Historical Investments + Beta Index
    ↓
Stage 1: Alpha Simulation (excess returns)
    ↓
Stage 2: Beta Forward Simulation (time-series model)
    ↓
Stage 3: Reconstruct Gross (alpha × beta paths)
    ↓
Stage 4: Reconstruct Net (apply costs)
    ↓
Results Display (4 stages × distributions)
```

---

## 7. Dependencies to Install

Add to `requirements.txt`:
```
arch>=5.3.0           # AR-GARCH models
hmmlearn>=0.3.0       # Hidden Markov Models
scipy>=1.9.0          # Statistical distributions
pandas>=1.5.0         # Time series handling
```

---

## 8. Testing Strategy

### Unit Tests
- `test_beta_simulation.py`:
  - Test AR-GARCH fitting with known data
  - Test HMM regime detection
  - Test jump detection logic
  - Test single path simulation
  - Test edge cases (insufficient data, non-positive prices)

- `test_reconstruction.py`:
  - Test gross performance reconstruction logic
  - Test net performance application
  - Verify alpha × beta math correctness

### Integration Tests
- Full deconstructed pipeline with sample data
- Verify all 4 stages complete successfully
- Check distribution statistics are reasonable

### Validation
- Compare "Past Performance Net" with current "Absolute" mode (should match)
- Verify reconstructed gross ≈ historical when using actual beta
- Check beta simulation produces realistic volatility clustering

---

## 9. Implementation Order

1. **Phase 1: Past Performance Mode** (Simpler, good foundation)
   - Task 1.1: Config UI changes
   - Task 1.2: Add `apply_costs` parameter to simulation
   - Task 1.3: Run dual simulations
   - Task 1.4: Display gross/net results
   - **Milestone**: Past Performance mode fully functional

2. **Phase 2: Beta Simulation Engine**
   - Task 3.1: Create beta_simulation.py module
     - Sub-task: Preprocessing and return calculation
     - Sub-task: AR-GARCH fitting
     - Sub-task: HMM regime fitting
     - Sub-task: Jump detection
     - Sub-task: Path simulation
   - Task 3.2: Beta config UI
   - Task 3.3: Update configuration model
   - **Milestone**: Beta simulation working standalone

3. **Phase 3: Performance Reconstruction**
   - Task 4.1: Create reconstruction.py module
   - Task 4.2: Update run simulation controller
   - **Milestone**: All 4 stages execute

4. **Phase 4: Results Display**
   - Task 5.1: Deconstructed results UI
   - Task 5.2: Beta path visualization
   - **Milestone**: Complete feature launch

---

## 10. Risk Mitigation

### Technical Risks
1. **AR-GARCH convergence failures**
   - Mitigation: Add fallback to simpler models (AR(1) only, constant vol)
   - Warn user if fit quality is poor (low log-likelihood)

2. **HMM instability with small samples**
   - Mitigation: Require minimum 500 observations, warn if < 1000
   - Fallback: Skip regime switching if convergence fails

3. **Jump estimation with few jumps**
   - Mitigation: Already handled in spec (use default parameters if < 3 jumps)

4. **Path explosion (prices → ∞ or 0)**
   - Mitigation: Add circuit breakers (kill path if price > 1000× or < 0.001×)
   - Log warnings for unstable paths

### User Experience Risks
1. **Confusion between modes**
   - Mitigation: Clear labeling, info tooltips, visual separation

2. **Long computation time**
   - Mitigation: Progress bars for each stage, allow cancellation

3. **Memory usage with many paths**
   - Mitigation: Stream beta paths, don't store all in memory simultaneously

---

## 11. Success Criteria

- [ ] User can select between Past Performance and Deconstructed Performance modes
- [ ] Past Performance mode displays gross and net distributions side-by-side
- [ ] Beta simulation produces realistic paths with volatility clustering
- [ ] All 4 deconstructed stages complete and display correctly
- [ ] Beta diagnostics (AIC, BIC, jump intensity) are displayed
- [ ] Results are reproducible with fixed seed
- [ ] Computation completes in < 60 seconds for 10,000 alpha sims × 1,000 beta paths
- [ ] No crashes on edge cases (insufficient data, convergence failures)

---

## 12. Future Enhancements (Out of Scope)

- Alternative time-series models (EGARCH, FIGARCH)
- Multivariate beta simulation (factor models)
- Correlation between alpha and beta
- Custom jump distribution (beyond Gaussian)
- Real-time parameter re-estimation
- Scenario analysis (stress testing specific regimes)
