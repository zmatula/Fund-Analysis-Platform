# Monte Carlo Fund Simulation - Architecture & Data Flow

**Version:** 1.0
**Last Updated:** 2025-10-19

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Flow Diagrams](#data-flow-diagrams)
3. [Component Interaction](#component-interaction)
4. [Simulation Flow](#simulation-flow)
5. [File Structure](#file-structure)

---

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                            │
│                     (Streamlit Web Application)                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Page 1:    │  │   Page 2:    │  │   Page 3:    │           │
│  │ Data Import  │→ │Configuration │→ │   Run Sim    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                              │                     │
│                                              ↓                     │
│                                     ┌──────────────┐              │
│                                     │   Page 4:    │              │
│                                     │   Results    │              │
│                                     └──────────────┘              │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│                       BUSINESS LOGIC LAYER                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  CSV Parser    │  │  Configuration   │  │  Simulation     │  │
│  │  & Validator   │  │  Manager         │  │  Engine         │  │
│  └────────────────┘  └──────────────────┘  └─────────────────┘  │
│                                                                    │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Hash          │  │  Statistics      │  │  Progress       │  │
│  │  Generator     │  │  Calculator      │  │  Tracker        │  │
│  └────────────────┘  └──────────────────┘  └─────────────────┘  │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│                       CALCULATION ENGINE                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│  │  Holding Period     │  │  IRR Calculator                  │  │
│  │  Calculator         │  │  (Newton-Raphson)                │  │
│  └─────────────────────┘  └──────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│  │  Cash Flow          │  │  Financial Engineering           │  │
│  │  Aggregator         │  │  Processor                       │  │
│  └─────────────────────┘  └──────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│  │  Portfolio Size     │  │  Random Investment               │  │
│  │  Generator          │  │  Selector                        │  │
│  └─────────────────────┘  └──────────────────────────────────┘  │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Investment Objects (in-memory list)                      │   │
│  │  - investment_name, fund_name, dates, moic, irr          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Configuration Object (in-memory)                         │   │
│  │  - fund info, financial params, simulation params         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Simulation Results (list of SimulationResult objects)    │   │
│  │  - simulation_id, moic, irr, investments, etc.           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Summary Statistics (SimulationSummary object)            │   │
│  │  - mean, median, percentiles for MOIC and IRR            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. CSV Import Flow

```
┌─────────────┐
│  CSV File   │
└──────┬──────┘
       │
       ↓
┌─────────────────────┐
│  Read CSV Contents  │
│  (line by line)     │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────────────┐
│  Parse Each Row             │
│  - Split by comma (6 cols) │
│  - Validate column count    │
└──────┬──────────────────────┘
       │
       ↓
┌─────────────────────────────┐
│  Parse & Validate Fields    │
│  ┌─────────────────────┐   │
│  │ Investment Name     │   │
│  │ Fund Name           │   │
│  │ Entry Date          │   │
│  │ Latest Date         │   │
│  │ MOIC (float)        │   │
│  │ IRR (float)         │   │
│  └─────────────────────┘   │
└──────┬──────────────────────┘
       │
       ├─── Parse Error? ───→ [Error: Row X, Column Y, Message]
       │
       ↓ [Valid]
┌─────────────────────────────┐
│  Create Investment Object   │
│  - Convert dates            │
│  - Adjust IRR if = -1.0     │
│  - Validate relationships   │
└──────┬──────────────────────┘
       │
       ↓
┌─────────────────────────────┐
│  Check for Duplicates       │
│  (name + fund combination)  │
└──────┬──────────────────────┘
       │
       ├─── Duplicate? ───→ [Warning: Duplicate detected]
       │
       ↓
┌─────────────────────────────┐
│  Add to Investment List     │
└──────┬──────────────────────┘
       │
       ↓
┌─────────────────────────────┐
│  Investment Universe Ready  │
│  (List[Investment])         │
└─────────────────────────────┘
```

### 2. Configuration Flow

```
┌─────────────────────────┐
│  User Input Form        │
│  ┌───────────────────┐ │
│  │ Fund Name         │ │
│  │ Fund Manager      │ │
│  │ Leverage Rate     │ │
│  │ Cost of Capital   │ │
│  │ Management Fee    │ │
│  │ Carry Rate        │ │
│  │ Hurdle Rate       │ │
│  │ Simulation Count  │ │
│  │ Inv Count Mean    │ │
│  │ Inv Count Std Dev │ │
│  └───────────────────┘ │
└──────────┬──────────────┘
           │
           ↓
┌──────────────────────────────┐
│  Validate Each Parameter     │
│  - Check ranges              │
│  - Check required fields     │
│  - Type validation           │
└──────────┬───────────────────┘
           │
           ├─── Invalid? ───→ [Display Errors]
           │
           ↓ [Valid]
┌──────────────────────────────┐
│  Create Configuration Object │
└──────────┬───────────────────┘
           │
           ↓
┌──────────────────────────────┐
│  Generate Hashes             │
│  ┌────────────────────────┐ │
│  │ 1. Sort investments    │ │
│  │ 2. JSON serialize      │ │
│  │ 3. SHA256 data_hash    │ │
│  │ 4. Add config params   │ │
│  │ 5. SHA256 total_hash   │ │
│  └────────────────────────┘ │
└──────────┬───────────────────┘
           │
           ↓
┌──────────────────────────────┐
│  Check Duplicate Run         │
│  (total_hash in history?)    │
└──────────┬───────────────────┘
           │
           ├─── Exists? ───→ [Warning: Already Run]
           │
           ↓ [New]
┌──────────────────────────────┐
│  Configuration Ready         │
└──────────────────────────────┘
```

### 3. Single Simulation Iteration Flow

```
┌────────────────────────────────────────────────────────────┐
│              START SINGLE SIMULATION (ID = i)              │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
           ┌─────────────────────┐
           │ Generate Portfolio  │
           │ Size (normal dist)  │
           │ - Sample from N(μ,σ)│
           │ - Round to integer  │
           │ - Bound [1, 2×max]  │
           └─────────┬───────────┘
                     │
                     ↓
           ┌─────────────────────┐
           │ Select Investments  │
           │ WITH REPLACEMENT    │
           │ (random_state.choice)│
           └─────────┬───────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│   FOR EACH SELECTED INVESTMENT                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Calculate Holding Period                        │    │
│   │ days = 365 × ln(MOIC) / ln(1 + IRR)             │    │
│   └─────────────────┬───────────────────────────────┘    │
│                     │                                      │
│                     ↓                                      │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Create Cash Flows                               │    │
│   │ - Investment: $1,000,000                        │    │
│   │ - Exit Day: days_held                           │    │
│   │ - Exit Amount: $1M × MOIC                       │    │
│   └─────────────────┬───────────────────────────────┘    │
│                     │                                      │
│                     ↓                                      │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Aggregate Cash Flows                            │    │
│   │ cash_flows[exit_day] += exit_amount             │    │
│   └─────────────────────────────────────────────────┘    │
│                                                             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
           ┌─────────────────────────┐
           │ Calculate Total Capital │
           │ - Total Invested = count × $1M │
           │ - Leverage = Invested × leverage_rate │
           │ - Total Capital = Invested + Leverage │
           └─────────┬───────────────┘
                     │
                     ↓
           ┌─────────────────────────┐
           │ Calculate Time Period   │
           │ - max_day = max(cash_flows.keys()) │
           │ - years = max_day / 365 │
           └─────────┬───────────────┘
                     │
                     ↓
           ┌─────────────────────────┐
           │ Calculate Gross Returns │
           │ - Total Returned = Σ(cash_flows) │
           │ - Gross Profit = Returned - Total Capital │
           └─────────┬───────────────┘
                     │
                     ↓
           ┌─────────────────────────────────────────┐
           │ Calculate Financial Engineering         │
           │ ┌─────────────────────────────────────┐│
           │ │ 1. Leverage Cost = Leverage ×       ││
           │ │    cost_of_capital × years          ││
           │ │                                     ││
           │ │ 2. Management Fees = Total Capital ×││
           │ │    fee_rate × years                 ││
           │ │                                     ││
           │ │ 3. Hurdle Return = Total Capital ×  ││
           │ │    (1 + hurdle_rate × years)        ││
           │ │                                     ││
           │ │ 4. Excess = max(0, Returned -       ││
           │ │    Hurdle Return)                   ││
           │ │                                     ││
           │ │ 5. Carry = Excess × carry_rate      ││
           │ └─────────────────────────────────────┘│
           └─────────┬───────────────────────────────┘
                     │
                     ↓
           ┌─────────────────────────────────────────┐
           │ Calculate Net Returns                   │
           │ Net Returned = Total Returned -         │
           │    Leverage Cost - Mgmt Fees - Carry    │
           │                                         │
           │ Net Profit = Net Returned -             │
           │    Total Invested                       │
           │                                         │
           │ Net MOIC = Net Returned /               │
           │    Total Invested                       │
           └─────────┬───────────────────────────────┘
                     │
                     ↓
           ┌─────────────────────────────────────────┐
           │ Calculate Net IRR                       │
           │ 1. Reduction factor = Net Returned /    │
           │    Total Returned                       │
           │                                         │
           │ 2. Net cash flows = cash_flows ×        │
           │    reduction_factor                     │
           │                                         │
           │ 3. IRR = newton_raphson(net_cash_flows, │
           │    total_invested)                      │
           └─────────┬───────────────────────────────┘
                     │
                     ↓
           ┌─────────────────────────────────────────┐
           │ Return SimulationResult                 │
           │ - simulation_id                         │
           │ - investments_selected                  │
           │ - investment_count                      │
           │ - total_invested                        │
           │ - total_returned (net)                  │
           │ - moic (net)                            │
           │ - irr (net)                             │
           │ - gross_profit                          │
           │ - net_profit                            │
           │ - fees_paid                             │
           │ - carry_paid                            │
           │ - leverage_cost                         │
           └─────────────────────────────────────────┘
```

### 4. Complete Monte Carlo Simulation Flow

```
┌────────────────────────────────────────────────────────────┐
│           START MONTE CARLO SIMULATION                     │
│  Inputs: investments, config                               │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
           ┌─────────────────────────┐
           │ Initialize Random State │
           │ RandomState(seed=42)    │
           └─────────┬───────────────┘
                     │
                     ↓
           ┌─────────────────────────┐
           │ Initialize Results List │
           │ results = []            │
           └─────────┬───────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│   FOR i in range(config.simulation_count):                 │
├────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Run Single Simulation                           │    │
│   │ result = run_single_simulation(                 │    │
│   │     investments, config, i, random_state)       │    │
│   └─────────────────┬───────────────────────────────┘    │
│                     │                                      │
│                     ↓                                      │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Append Result                                   │    │
│   │ results.append(result)                          │    │
│   └─────────────────┬───────────────────────────────┘    │
│                     │                                      │
│                     ↓                                      │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Report Progress (every 100 simulations)        │    │
│   │ if (i + 1) % 100 == 0:                          │    │
│   │     progress((i+1) / total)                     │    │
│   └─────────────────────────────────────────────────┘    │
│                                                             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│   CALCULATE SUMMARY STATISTICS                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Extract MOIC and IRR Arrays                     │    │
│   │ moics = [r.moic for r in results]               │    │
│   │ irrs = [r.irr for r in results]                 │    │
│   └─────────────────┬───────────────────────────────┘    │
│                     │                                      │
│                     ↓                                      │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Calculate MOIC Statistics                       │    │
│   │ - mean, median, std_dev                         │    │
│   │ - min, max                                      │    │
│   │ - percentiles: 5th, 25th, 75th, 95th           │    │
│   └─────────────────┬───────────────────────────────┘    │
│                     │                                      │
│                     ↓                                      │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Calculate IRR Statistics                        │    │
│   │ - mean, median, std_dev                         │    │
│   │ - min, max                                      │    │
│   │ - percentiles: 5th, 25th, 75th, 95th           │    │
│   └─────────────────┬───────────────────────────────┘    │
│                     │                                      │
│                     ↓                                      │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Create SimulationSummary Object                 │    │
│   │ - config, total_runs, timestamp                 │    │
│   │ - all MOIC and IRR statistics                   │    │
│   └─────────────────────────────────────────────────┘    │
│                                                             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
           ┌─────────────────────────┐
           │ Return Results          │
           │ (results, summary)      │
           └─────────────────────────┘
```

### 5. Results Visualization Flow

```
┌─────────────────────────┐
│  Simulation Results     │
│  - List[SimulationResult]│
│  - SimulationSummary    │
└──────────┬──────────────┘
           │
           ├──────────────────────────────────────┐
           │                                       │
           ↓                                       ↓
┌──────────────────────────┐          ┌──────────────────────────┐
│  Display Summary Stats   │          │  Generate Histograms     │
│  ┌────────────────────┐ │          │  ┌────────────────────┐ │
│  │ Total Runs         │ │          │  │ MOIC Distribution  │ │
│  │ Mean MOIC          │ │          │  │ - 50 bins          │ │
│  │ Median MOIC        │ │          │  │ - Mean line        │ │
│  │ Std Dev MOIC       │ │          │  │ - Median line      │ │
│  │ Min/Max MOIC       │ │          │  └────────────────────┘ │
│  │                    │ │          │                          │
│  │ Mean IRR           │ │          │  ┌────────────────────┐ │
│  │ Median IRR         │ │          │  │ IRR Distribution   │ │
│  │ Std Dev IRR        │ │          │  │ - 50 bins          │ │
│  │ Min/Max IRR        │ │          │  │ - Mean line        │ │
│  └────────────────────┘ │          │  │ - Median line      │ │
└──────────────────────────┘          │  └────────────────────┘ │
                                      └──────────────────────────┘
           │                                       │
           └───────────────┬───────────────────────┘
                           │
                           ↓
                ┌──────────────────────────┐
                │  Percentile Table        │
                │  ┌────────────────────┐ │
                │  │ Percentile │ MOIC  │ │
                │  │ 5th        │ X.XXx │ │
                │  │ 25th       │ X.XXx │ │
                │  │ 50th       │ X.XXx │ │
                │  │ 75th       │ X.XXx │ │
                │  │ 95th       │ X.XXx │ │
                │  │            │       │ │
                │  │ Percentile │ IRR   │ │
                │  │ 5th        │ XX.X% │ │
                │  │ 25th       │ XX.X% │ │
                │  │ 50th       │ XX.X% │ │
                │  │ 75th       │ XX.X% │ │
                │  │ 95th       │ XX.X% │ │
                │  └────────────────────┘ │
                └──────────────────────────┘
```

---

## Component Interaction

### Module Dependencies

```
┌─────────────┐
│   app.py    │  (Main Streamlit Application)
└──────┬──────┘
       │
       ├─────────┬─────────────┬─────────────┬────────────┐
       │         │             │             │            │
       ↓         ↓             ↓             ↓            ↓
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐
│ models.py│ │data_im-  │ │simulat-  │ │ visual-│ │ utils.py│
│          │ │port.py   │ │ion.py    │ │ ization│ │         │
│          │ │          │ │          │ │ .py    │ │         │
└──────────┘ └──────────┘ └────┬─────┘ └────────┘ └─────────┘
                                │
                                ↓
                         ┌─────────────┐
                         │calculators.py│
                         │- IRR calc    │
                         │- Holding pd  │
                         │- MOIC calc   │
                         └─────────────┘
```

### Interaction Sequence

```
USER                UI                 LOGIC              CALCULATOR
 │                  │                   │                     │
 │ Upload CSV       │                   │                     │
 ├─────────────────>│                   │                     │
 │                  │ Parse & Validate  │                     │
 │                  ├──────────────────>│                     │
 │                  │                   │ Validate Fields     │
 │                  │                   ├────────────────────>│
 │                  │                   │ <Return Errors>     │
 │                  │                   │<────────────────────┤
 │                  │ <Show Errors>     │                     │
 │                  │<──────────────────┤                     │
 │ [Fix & Resubmit] │                   │                     │
 │ ─────────────────>                   │                     │
 │                  │ Success           │                     │
 │                  │<──────────────────┤                     │
 │                  │                   │                     │
 │ Configure Params │                   │                     │
 ├─────────────────>│                   │                     │
 │                  │ Validate Config   │                     │
 │                  ├──────────────────>│                     │
 │                  │ Generate Hash     │                     │
 │                  │ ──────────────────>                     │
 │                  │ <Return Config>   │                     │
 │                  │<──────────────────┤                     │
 │                  │                   │                     │
 │ Run Simulation   │                   │                     │
 ├─────────────────>│                   │                     │
 │                  │ Start Simulation  │                     │
 │                  ├──────────────────>│                     │
 │                  │                   │ For each iteration: │
 │                  │                   │ ──────────────────> │
 │                  │                   │ - Generate portfolio│
 │                  │                   │ - Select investments│
 │                  │                   │ - Calculate cash    │
 │                  │                   │   flows             │
 │                  │                   │ - Calculate returns │
 │                  │                   │ - Calculate IRR     │
 │                  │                   │ <Return Result>     │
 │                  │                   │<────────────────────│
 │                  │ Progress Update   │                     │
 │                  │<──────────────────┤                     │
 │ [Progress: 34%]  │                   │                     │
 │<─────────────────┤                   │                     │
 │                  │                   │ ...                 │
 │                  │ Complete          │                     │
 │                  │<──────────────────┤                     │
 │                  │                   │                     │
 │                  │ Calculate Stats   │                     │
 │                  ├──────────────────>│                     │
 │                  │ <Return Summary>  │                     │
 │                  │<──────────────────┤                     │
 │                  │                   │                     │
 │ View Results     │                   │                     │
 ├─────────────────>│                   │                     │
 │                  │ Generate Charts   │                     │
 │                  │ (internally)      │                     │
 │ [Display Charts] │                   │                     │
 │<─────────────────┤                   │                     │
```

---

## Simulation Flow

### Detailed Step-by-Step Execution

#### Phase 1: Initialization (happens once)

1. **Load Investment Data**
   - Parse CSV file
   - Validate each row
   - Create Investment objects
   - Store in list

2. **Configure Simulation**
   - Collect user parameters
   - Validate ranges
   - Generate hashes
   - Check for duplicates

3. **Initialize Random State**
   - Create RandomState(seed=42)
   - Ensures reproducibility

#### Phase 2: Iteration Loop (happens N times)

**For iteration `i` from 0 to simulation_count:**

**Step 1:** Generate Portfolio Size
```python
size = random_state.normal(mean, std_dev)
size = round(size)
size = max(1, min(size, len(investments) * 2))
```

**Step 2:** Select Investments
```python
indices = random_state.choice(len(investments), size, replace=True)
selected = [investments[idx] for idx in indices]
```

**Step 3:** Build Cash Flow Schedule
```python
cash_flows = {}  # {day: amount}
total_invested = 0

for investment in selected:
    # Calculate holding period
    days = 365 * ln(investment.moic) / ln(1 + investment.irr)

    # Add exit cash flow
    exit_amount = 1_000_000 * investment.moic
    if days in cash_flows:
        cash_flows[days] += exit_amount
    else:
        cash_flows[days] = exit_amount

    total_invested += 1_000_000
```

**Step 4:** Calculate Total Capital
```python
leverage_amount = total_invested * config.leverage_rate
total_capital = total_invested + leverage_amount
```

**Step 5:** Calculate Time Period
```python
max_day = max(cash_flows.keys())
years_held = max_day / 365.0
```

**Step 6:** Calculate Costs
```python
leverage_cost = leverage_amount * config.cost_of_capital * years_held
management_fees = total_capital * config.fee_rate * years_held
```

**Step 7:** Calculate Gross Returns
```python
total_returned = sum(cash_flows.values())
gross_profit = total_returned - total_capital
```

**Step 8:** Calculate Carry
```python
hurdle_return = total_capital * (1 + config.hurdle_rate * years_held)
excess_return = max(0, total_returned - hurdle_return)
carry_paid = excess_return * config.carry_rate
```

**Step 9:** Calculate Net Returns
```python
net_returned = total_returned - leverage_cost - management_fees - carry_paid
net_profit = net_returned - total_invested
net_moic = net_returned / total_invested
```

**Step 10:** Calculate Net IRR
```python
reduction_factor = net_returned / total_returned if total_returned > 0 else 0
net_cash_flows = {day: cf * reduction_factor for day, cf in cash_flows.items()}
net_irr = newton_raphson_irr(net_cash_flows, total_invested)
```

**Step 11:** Store Result
```python
result = SimulationResult(
    simulation_id=i,
    investments_selected=[inv.name for inv in selected],
    investment_count=len(selected),
    total_invested=total_invested,
    total_returned=net_returned,
    moic=net_moic,
    irr=net_irr,
    gross_profit=gross_profit,
    net_profit=net_profit,
    fees_paid=management_fees,
    carry_paid=carry_paid,
    leverage_cost=leverage_cost
)
results.append(result)
```

**Step 12:** Report Progress
```python
if (i + 1) % 100 == 0:
    progress_callback((i + 1) / simulation_count)
```

#### Phase 3: Aggregation (happens once)

1. **Extract Metrics**
   ```python
   moics = [r.moic for r in results]
   irrs = [r.irr for r in results]
   ```

2. **Calculate Statistics**
   ```python
   summary = SimulationSummary(
       total_runs=len(results),
       mean_moic=np.mean(moics),
       median_moic=np.median(moics),
       std_moic=np.std(moics),
       # ... percentiles ...
   )
   ```

3. **Generate Visualizations**
   - MOIC histogram (50 bins)
   - IRR histogram (50 bins)
   - Percentile table

4. **Return Results**
   ```python
   return results, summary
   ```

---

## File Structure

### Recommended Python Project Structure

```
fund_simulation/
│
├── app.py                     # Main Streamlit application
│   ├── Page 1: Data Import
│   ├── Page 2: Configuration
│   ├── Page 3: Run Simulation
│   └── Page 4: Results
│
├── models.py                  # Data models
│   ├── Investment
│   ├── SimulationConfiguration
│   ├── SimulationResult
│   └── SimulationSummary
│
├── data_import.py             # CSV parsing & validation
│   ├── parse_csv()
│   ├── validate_investment()
│   └── check_duplicates()
│
├── simulation.py              # Monte Carlo engine
│   ├── run_monte_carlo_simulation()
│   ├── run_single_simulation()
│   ├── generate_portfolio_size()
│   └── select_investments()
│
├── calculators.py             # Core calculations
│   ├── calculate_holding_period()
│   ├── calculate_irr()
│   ├── calculate_moic()
│   └── apply_financial_engineering()
│
├── statistics.py              # Statistical analysis
│   ├── calculate_summary()
│   ├── calculate_percentiles()
│   └── generate_distributions()
│
├── visualization.py           # Charts & graphs
│   ├── create_histogram()
│   ├── create_percentile_table()
│   └── format_results()
│
├── utils.py                   # Utility functions
│   ├── generate_hash()
│   ├── format_currency()
│   ├── format_percentage()
│   └── validate_config()
│
├── requirements.txt           # Dependencies
│   ├── streamlit
│   ├── pandas
│   ├── numpy
│   ├── plotly
│   └── python-dateutil
│
└── README.md                  # Project documentation
```

---

## Key Design Decisions

### 1. Why Streamlit?
- Rapid development of data applications
- Built-in state management
- Easy visualization integration
- No frontend coding required

### 2. Why NumPy for Random Numbers?
- Reproducible with seed
- Fast vectorized operations
- Industry-standard library
- Good performance at scale

### 3. Why Newton-Raphson for IRR?
- Guaranteed convergence for well-behaved cash flows
- Fast (usually < 10 iterations)
- Mathematically robust
- Industry-standard approach

### 4. Why Hash-Based Deduplication?
- Deterministic (same inputs → same hash)
- Efficient (O(1) lookup)
- Cryptographically secure (SHA256)
- Captures all relevant parameters

### 5. Why Selection WITH Replacement?
- Models concentration risk realistically
- Same investment can appear multiple times
- Simpler implementation
- Matches industry practice

---

**End of Architecture & Data Flow Documentation**
