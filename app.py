"""Monte Carlo Fund Simulation - Streamlit Application"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime

from fund_simulation.data_import import parse_csv_file
from fund_simulation.beta_import import (
    parse_beta_csv,
    detect_frequency,
    create_beta_index,
    validate_beta_coverage
)
from fund_simulation.models import SimulationConfiguration
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.statistics import calculate_summary_statistics
from fund_simulation.csv_export import export_investment_details, export_cash_flow_schedules
from fund_simulation.beta_simulation import simulate_beta_forward, __BETA_SIMULATION_VERSION__
from fund_simulation.reconstruction import reconstruct_gross_performance, reconstruct_net_performance
import numpy as np

# Removed verbose startup diagnostic


def main():
    st.set_page_config(
        page_title="Monte Carlo Fund Simulation",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Monte Carlo Fund Simulation")
    st.markdown("Simulate future fund performance using historical investment data")

    # Initialize session state
    if 'investments' not in st.session_state:
        st.session_state.investments = None
    if 'config' not in st.session_state:
        st.session_state.config = None
    if 'beta_index' not in st.session_state:
        st.session_state.beta_index = None
    if 'beta_frequency' not in st.session_state:
        st.session_state.beta_frequency = None
    if 'export_details' not in st.session_state:
        st.session_state.export_details = False

    # Results for Past Performance mode
    if 'gross_results' not in st.session_state:
        st.session_state.gross_results = None
    if 'gross_summary' not in st.session_state:
        st.session_state.gross_summary = None
    if 'net_results' not in st.session_state:
        st.session_state.net_results = None
    if 'net_summary' not in st.session_state:
        st.session_state.net_summary = None

    # Results for Deconstructed Performance mode
    if 'alpha_results' not in st.session_state:
        st.session_state.alpha_results = None
    if 'alpha_summary' not in st.session_state:
        st.session_state.alpha_summary = None
    if 'beta_paths' not in st.session_state:
        st.session_state.beta_paths = None
    if 'beta_diagnostics' not in st.session_state:
        st.session_state.beta_diagnostics = None
    if 'reconstructed_gross_results' not in st.session_state:
        st.session_state.reconstructed_gross_results = None
    if 'reconstructed_gross_summary' not in st.session_state:
        st.session_state.reconstructed_gross_summary = None
    if 'reconstructed_net_results' not in st.session_state:
        st.session_state.reconstructed_net_results = None
    if 'reconstructed_net_summary' not in st.session_state:
        st.session_state.reconstructed_net_summary = None
    if 'beta_recon_diagnostics' not in st.session_state:
        st.session_state.beta_recon_diagnostics = None
    if 'decomp_diagnostics' not in st.session_state:
        st.session_state.decomp_diagnostics = None

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Data Import",
        "⚙️ Configuration",
        "▶️ Run Simulation",
        "📈 Results"
    ])

    with tab1:
        render_data_import()

    with tab2:
        render_configuration()

    with tab3:
        render_run_simulation()

    with tab4:
        render_results()


def render_data_import():
    st.header("Import Historical Investment Data")

    st.markdown("""
    **CSV Format** (NO headers):
    - Column 1: Investment Name
    - Column 2: Fund Name
    - Column 3: Entry Date (YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, or YYYY/MM/DD)
    - Column 4: MOIC (Multiple on Invested Capital, e.g., 2.5 for 2.5x)
    - Column 5: IRR (as decimal, e.g., 0.25 for 25%)

    **Note:** Exit date will be automatically calculated from MOIC and IRR using the formula:
    days_held = 365 × ln(MOIC) / ln(1 + IRR)
    """)

    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=['csv'],
        help="CSV format: investment_name, fund_name, entry_date, MOIC, IRR"
    )

    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_path = "temp_upload.csv"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Parse CSV
        investments, errors = parse_csv_file(temp_path)

        if errors:
            st.error(f"Found {len(errors)} error(s) during import:")
            for error in errors[:10]:  # Show first 10 errors
                st.error(f"- {error}")
            if len(errors) > 10:
                st.error(f"... and {len(errors) - 10} more errors")

        if investments:
            st.success(f"✓ Successfully loaded {len(investments)} investments")

            # Display data
            df = pd.DataFrame([
                {
                    'Investment': inv.investment_name,
                    'Fund': inv.fund_name,
                    'Entry Date': inv.entry_date.date(),
                    'Exit Date (Calculated)': inv.latest_date.date(),
                    'Days Held': inv.days_held,
                    'MOIC': f"{inv.moic:.2f}x",
                    'IRR': f"{inv.irr:.2%}"
                }
                for inv in investments
            ])
            st.dataframe(df, width="stretch", height=400)

            # Store in session state
            st.session_state.investments = investments

    # Beta Price Data Section
    st.markdown("---")
    st.header("Import Beta Price Data (Optional - for Alpha Simulations)")

    st.markdown("""
    **Beta pricing data enables "alpha" simulations that measure excess returns above a benchmark.**

    **CSV Format** (2 columns, with or without headers):
    - Column 1: Date (YYYY-MM-DD, MM/DD/YYYY, etc.)
    - Column 2: Price (numeric)

    Example:
    ```
    2015-07-01,100.00
    2015-08-01,105.00
    2015-09-01,103.00
    ```
    """)

    beta_uploaded_file = st.file_uploader(
        "Upload Beta Prices CSV",
        type=['csv'],
        key="beta_uploader",
        help="CSV with date and price columns"
    )

    if beta_uploaded_file is not None:
        # Save temporarily
        beta_temp_path = "temp_beta_upload.csv"
        with open(beta_temp_path, "wb") as f:
            f.write(beta_uploaded_file.getbuffer())

        # Parse CSV
        beta_prices, beta_errors, detected_freq = parse_beta_csv(beta_temp_path)

        if beta_errors:
            st.error(f"Found {len(beta_errors)} error(s) in beta data:")
            for error in beta_errors[:10]:
                st.error(f"- {error}")
            if len(beta_errors) > 10:
                st.error(f"... and {len(beta_errors) - 10} more errors")

        if beta_prices:
            st.success(f"✓ Successfully loaded {len(beta_prices)} beta prices")

            # Show detected frequency
            if detected_freq != "insufficient_data":
                st.info(f"Auto-detected frequency: **{detected_freq.upper()}**")

            # Frequency selector
            st.markdown("**Confirm Data Frequency:**")
            st.markdown("""
            This determines how to interpolate between dates.
            For example, if you select "Monthly" and have a price dated 2015-07-01,
            we'll assume it represents mid-July (2015-07-15).
            """)

            frequency_options = ["daily", "weekly", "monthly", "quarterly", "annual", "irregular"]
            default_index = frequency_options.index(detected_freq) if detected_freq in frequency_options else 2

            user_frequency = st.selectbox(
                "Data Frequency",
                options=frequency_options,
                index=default_index,
                key="frequency_selector"
            )

            # Display sample of data
            st.markdown("**Sample Beta Prices:**")
            sample_df = pd.DataFrame([
                {
                    'Date': p.date.date(),
                    'Price': f"{p.price:.2f}"
                }
                for p in beta_prices[:10]
            ])
            st.dataframe(sample_df, width="stretch", hide_index=True)

            if len(beta_prices) > 10:
                st.text(f"... and {len(beta_prices) - 10} more prices")

            # Create beta index
            beta_index = create_beta_index(beta_prices, user_frequency)

            # Validate coverage if we have investments
            if st.session_state.investments is not None:
                is_valid, coverage_errors = validate_beta_coverage(
                    st.session_state.investments,
                    beta_index
                )

                if is_valid:
                    st.success("✓ Beta data covers all investment periods")
                else:
                    st.error("⚠️ Beta Data Coverage Issues:")
                    for error in coverage_errors:
                        st.error(f"- {error}")
                    st.warning("You can still proceed, but investments outside beta range will be skipped in alpha mode.")

            # Store in session state
            st.session_state.beta_index = beta_index
            st.session_state.beta_frequency = user_frequency


def render_configuration():
    st.header("Configure Simulation Parameters")

    if st.session_state.investments is None:
        st.warning("⚠️ Please import data first")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fund Information")
        fund_name = st.text_input("Fund Name", value="Simulated Fund")
        fund_manager = st.text_input("Fund Manager", value="Fund Manager")

        st.subheader("Financial Parameters")
        leverage_rate = st.slider(
            "Leverage Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
            help="Leverage as % of LP capital"
        ) / 100

        cost_of_capital = st.slider(
            "Cost of Capital (%)",
            min_value=0.0,
            max_value=100.0,
            value=8.0,
            step=1.0
        ) / 100

        fee_rate = st.slider(
            "Management Fee Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.1
        ) / 100

        carry_rate = st.slider(
            "Carry Rate (%)",
            min_value=0.0,
            max_value=50.0,
            value=20.0,
            step=1.0
        ) / 100

        hurdle_rate = st.slider(
            "Hurdle Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=8.0,
            step=1.0
        ) / 100

    with col2:
        st.subheader("Simulation Parameters")

        # Primary Simulation Mode Selection
        st.markdown("**Simulation Mode:**")
        simulation_mode = st.radio(
            "Select analysis mode",
            options=["past_performance", "deconstructed_performance"],
            index=0,
            format_func=lambda x: "Past Performance" if x == "past_performance" else "Deconstructed Performance",
            help="Past Performance: Simulate historical returns with gross/net splits. Deconstructed: Alpha/Beta decomposition with forward beta simulation.",
            horizontal=True
        )

        # Show info about selected mode
        if simulation_mode == "past_performance":
            st.info("📊 **Past Performance Mode**: Will run both Gross (no costs) and Net (with fees/carry) simulations side-by-side.")
        else:
            st.info("🔬 **Deconstructed Performance Mode**: 5-stage analysis - Beta Decomposition, Alpha Simulation, Beta Forward Simulation, Gross Reconstruction, Net Reconstruction.")
            # Show warning if no beta data
            if st.session_state.beta_index is None:
                st.warning("⚠️ Deconstructed mode requires beta price data. Please upload beta prices in the Data Import tab.")

        simulation_count = st.number_input(
            "Number of Simulations",
            min_value=100,
            max_value=1000000,
            value=10000,
            step=1000
        )

        investment_count_mean = st.number_input(
            "Portfolio Size (Mean)",
            min_value=1.0,
            value=10.0,
            step=1.0
        )

        investment_count_std = st.number_input(
            "Portfolio Size (Std Dev)",
            min_value=0.0,
            value=2.0,
            step=0.5
        )

        # Beta Simulation Parameters (only for Deconstructed mode)
        if simulation_mode == "deconstructed_performance":
            st.markdown("---")
            st.markdown("**Beta Forward Simulation Settings:**")
            st.caption("Constant-growth paths with exact distribution moments and user-friendly market views")

            beta_horizon_days = st.number_input(
                "Simulation Horizon (Trading Days)",
                min_value=252,
                max_value=18250,  # ~50 years
                value=2520,  # 10 years default
                step=252,
                help="Number of trading days to simulate forward (252 days per year)"
            )

            beta_n_paths = st.number_input(
                "Number of Beta Paths",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100,
                help="Number of Monte Carlo paths for beta simulation"
            )

            st.markdown("**Market Views:**")
            col1, col2 = st.columns(2)

            with col1:
                beta_outlook = st.selectbox(
                    "Return Outlook",
                    options=["pessimistic", "base", "optimistic"],
                    index=1,
                    help="Pessimistic = hist -10%, Base = historical, Optimistic = hist +10%"
                )

            with col2:
                beta_confidence = st.selectbox(
                    "Volatility Confidence",
                    options=["low", "medium", "high"],
                    index=1,
                    help="Low = 1.5× historical vol, Medium = 1.0× historical vol, High = 0.5× historical vol"
                )

            # Warn if beta data is insufficient
            if st.session_state.beta_index is not None:
                n_beta_obs = len(st.session_state.beta_index.prices)
                if n_beta_obs < 36:
                    st.warning(f"⚠️ Beta data has only {n_beta_obs} observations. Recommend at least 36 for stable estimates.")
        else:
            # Default values when not in deconstructed mode
            beta_horizon_days = 2520
            beta_n_paths = 1000
            beta_outlook = "base"
            beta_confidence = "medium"

    # Create configuration
    config = SimulationConfiguration(
        fund_name=fund_name,
        fund_manager=fund_manager,
        leverage_rate=leverage_rate,
        cost_of_capital=cost_of_capital,
        fee_rate=fee_rate,
        carry_rate=carry_rate,
        hurdle_rate=hurdle_rate,
        simulation_count=int(simulation_count),
        investment_count_mean=investment_count_mean,
        investment_count_std=investment_count_std,
        simulation_mode=simulation_mode,
        beta_horizon_days=int(beta_horizon_days),
        beta_n_paths=int(beta_n_paths),
        beta_outlook=beta_outlook,
        beta_confidence=beta_confidence
    )

    # Validate
    errors = config.validate()
    if errors:
        st.error("Configuration errors:")
        for error in errors:
            st.error(f"- {error}")
    else:
        st.success("✓ Configuration is valid")
        st.session_state.config = config


def render_run_simulation():
    st.header("Run Monte Carlo Simulation")

    if st.session_state.investments is None:
        st.warning("⚠️ Please import data first")
        return

    if st.session_state.config is None:
        st.warning("⚠️ Please configure simulation parameters")
        return

    config = st.session_state.config
    investments = st.session_state.investments

    st.info(f"Ready to run {config.simulation_count:,} simulations with {len(investments)} investments")

    # Option to export detailed data
    export_details = st.checkbox(
        "Export detailed investment and cash flow data for CSV analysis",
        value=st.session_state.export_details,
        help="Enable this to generate CSV files with investment-level details and cash flow schedules. This will use more memory."
    )
    st.session_state.export_details = export_details

    if st.button("▶️ Run Simulation", type="primary"):
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(fraction):
            progress_bar.progress(fraction)
            status_text.text(f"Progress: {fraction*100:.1f}%")

        # Run simulation based on mode
        if config.simulation_mode == "past_performance":
            # Past Performance Mode: Run both Gross and Net simulations

            # Stage 1: Gross simulation
            progress_bar.progress(0)
            status_text.text("Stage 1/2: Running gross performance simulation...")
            with st.spinner("Running gross performance simulation (no costs)..."):
                gross_results = run_monte_carlo_simulation(
                    investments,
                    config,
                    progress_callback=update_progress,
                    beta_index=None,
                    export_details=export_details,
                    apply_costs=False,  # No fees/carry/leverage
                    use_alpha=False  # Use absolute returns
                )
            gross_summary = calculate_summary_statistics(gross_results, config)

            # Stage 2: Net simulation
            progress_bar.progress(0)
            status_text.text("Stage 2/2: Running net performance simulation...")
            with st.spinner("Running net performance simulation (with costs)..."):
                net_results = run_monte_carlo_simulation(
                    investments,
                    config,
                    progress_callback=update_progress,
                    beta_index=None,
                    export_details=False,  # Only track details once
                    apply_costs=True,  # Apply fees/carry/leverage
                    use_alpha=False  # Use absolute returns
                )
            net_summary = calculate_summary_statistics(net_results, config)

            # Store results
            st.session_state.gross_results = gross_results
            st.session_state.gross_summary = gross_summary
            st.session_state.net_results = net_results
            st.session_state.net_summary = net_summary

            # Clear deconstructed results
            st.session_state.alpha_results = None
            st.session_state.alpha_summary = None
            st.session_state.beta_paths = None
            st.session_state.beta_diagnostics = None
            st.session_state.reconstructed_gross_results = None
            st.session_state.reconstructed_gross_summary = None
            st.session_state.reconstructed_net_results = None
            st.session_state.reconstructed_net_summary = None
            st.session_state.beta_recon_diagnostics = None
            st.session_state.decomp_diagnostics = None

            progress_bar.progress(1.0)
            status_text.text("✓ Completed all stages")
            st.success(f"✓ Completed {len(gross_results):,} gross and {len(net_results):,} net simulations")

        elif config.simulation_mode == "deconstructed_performance":
            # Deconstructed Performance Mode: 4-stage analysis
            # Check that beta data is available
            if st.session_state.beta_index is None:
                st.error("⚠️ Beta price data is required for Deconstructed Performance mode. Please upload beta data in the Data Import tab.")
                progress_bar.empty()
                status_text.empty()
                return

            # Stage 0: Beta Decomposition
            status_text.text("Stage 0/4: Decomposing historical beta from deals...")
            with st.spinner("Stage 0/4: Decomposing historical beta..."):
                from fund_simulation.data_import import decompose_historical_beta

                # Strip historical beta to get alpha-only returns
                alpha_investments, decomp_diagnostics = decompose_historical_beta(
                    investments,
                    st.session_state.beta_index,
                    beta_exposure=config.beta_exposure,
                    verbose=True  # Print diagnostic table
                )

                # Store decomposition diagnostics
                st.session_state.decomp_diagnostics = decomp_diagnostics

                # Use alpha-only investments for simulation
                investments_for_alpha_sim = alpha_investments

                st.success(f"✓ Stage 0: Decomposed {len(alpha_investments)} investments (Mean historical beta IRR: {decomp_diagnostics['mean_beta_irr']:.2%})")

            # Stage 1: Alpha Simulation
            progress_bar.progress(0)
            status_text.text("Stage 1/4: Running alpha simulation (excess returns)...")
            with st.spinner("Stage 1/4: Running alpha simulation (excess returns)..."):
                alpha_results = run_monte_carlo_simulation(
                    investments_for_alpha_sim,
                    config,
                    progress_callback=update_progress,
                    beta_index=st.session_state.beta_index,
                    export_details=True,  # Required for reconstruction (forced regardless of checkbox)
                    apply_costs=False,  # No costs for alpha
                    use_alpha=True  # Calculate alpha (excess) returns
                )
            alpha_summary = calculate_summary_statistics(alpha_results, config)

            # Stage 2: Beta Forward Simulation
            progress_bar.progress(0)
            status_text.text("Stage 2/4: Running beta forward simulation...")

            with st.spinner("Stage 2/4: Running beta forward simulation (constant-growth method)..."):
                try:
                    beta_paths, beta_diagnostics = simulate_beta_forward(
                        st.session_state.beta_index,
                        config.beta_horizon_days,
                        config.beta_n_paths,
                        seed=42,
                        outlook=config.beta_outlook,
                        confidence=config.beta_confidence
                    )
                    progress_bar.progress(1.0)
                    st.session_state.beta_paths = beta_paths
                    st.session_state.beta_diagnostics = beta_diagnostics

                    st.success(f"✓ Stage 2: Generated {config.beta_n_paths} beta paths over {config.beta_horizon_days} trading days")
                except Exception as e:
                    st.error(f"⚠️ Beta simulation failed: {str(e)}")
                    st.session_state.beta_paths = None
                    st.session_state.beta_diagnostics = None

            # Stage 3: Gross Performance Reconstruction
            if st.session_state.beta_paths is not None:
                progress_bar.progress(0)
                status_text.text("Stage 3/4: Reconstructing gross performance...")
                with st.spinner("Stage 3/4: Reconstructing gross performance (alpha × beta)..."):
                    try:
                        # Need a random state for selecting beta paths
                        random_state_recon = np.random.RandomState(seed=42)

                        # Get original returns lookup from decomposition diagnostics
                        original_returns_lookup = None
                        if st.session_state.decomp_diagnostics:
                            original_returns_lookup = st.session_state.decomp_diagnostics.get('original_returns_lookup')

                        reconstructed_gross_results, beta_recon_diagnostics = reconstruct_gross_performance(
                            alpha_results,
                            st.session_state.beta_paths,
                            st.session_state.beta_paths.index[0],
                            config,
                            random_state_recon,
                            original_returns_lookup
                        )

                        reconstructed_gross_summary = calculate_summary_statistics(reconstructed_gross_results, config)

                        progress_bar.progress(1.0)
                        st.session_state.reconstructed_gross_results = reconstructed_gross_results
                        st.session_state.reconstructed_gross_summary = reconstructed_gross_summary
                        st.session_state.beta_recon_diagnostics = beta_recon_diagnostics
                        st.success(f"✓ Stage 3: Reconstructed {len(reconstructed_gross_results):,} gross performance simulations")

                    except Exception as e:
                        st.error(f"⚠️ Gross reconstruction failed: {str(e)}")
                        st.session_state.reconstructed_gross_results = None
                        st.session_state.reconstructed_gross_summary = None
            else:
                st.warning("⚠️ Stage 3 skipped: Beta simulation failed")
                st.session_state.reconstructed_gross_results = None
                st.session_state.reconstructed_gross_summary = None

            # Stage 4: Net Performance Reconstruction
            if st.session_state.reconstructed_gross_results is not None:
                progress_bar.progress(0)
                status_text.text("Stage 4/4: Reconstructing net performance...")
                with st.spinner("Stage 4/4: Reconstructing net performance (applying costs)..."):
                    try:
                        reconstructed_net_results = reconstruct_net_performance(
                            st.session_state.reconstructed_gross_results,
                            config
                        )

                        reconstructed_net_summary = calculate_summary_statistics(reconstructed_net_results, config)

                        progress_bar.progress(1.0)
                        st.session_state.reconstructed_net_results = reconstructed_net_results
                        st.session_state.reconstructed_net_summary = reconstructed_net_summary
                        st.success(f"✓ Stage 4: Reconstructed {len(reconstructed_net_results):,} net performance simulations")

                    except Exception as e:
                        st.error(f"⚠️ Net reconstruction failed: {str(e)}")
                        st.session_state.reconstructed_net_results = None
                        st.session_state.reconstructed_net_summary = None
            else:
                st.warning("⚠️ Stage 4 skipped: Gross reconstruction failed")
                st.session_state.reconstructed_net_results = None
                st.session_state.reconstructed_net_summary = None

            # Store alpha results
            st.session_state.alpha_results = alpha_results
            st.session_state.alpha_summary = alpha_summary

            # Clear past performance results
            st.session_state.gross_results = None
            st.session_state.gross_summary = None
            st.session_state.net_results = None
            st.session_state.net_summary = None

            progress_bar.progress(1.0)
            status_text.text("✓ Completed all 5 stages")
            st.success(f"✓ Completed all 5 stages of deconstructed performance analysis")

        progress_bar.empty()
        status_text.empty()


def render_results():
    st.header("Simulation Results")

    # Determine which mode results are available
    has_past_performance = (st.session_state.gross_summary is not None)
    has_deconstructed = (st.session_state.alpha_summary is not None)

    if not has_past_performance and not has_deconstructed:
        st.warning("⚠️ Please run simulation first")
        return

    # Render results based on available mode
    if has_past_performance:
        render_past_performance_results()
    elif has_deconstructed:
        render_deconstructed_performance_results()


def render_past_performance_results():
    """Render results for Past Performance mode (Gross vs Net)."""
    st.subheader("📊 Past Performance Analysis")
    st.caption("Comparison of Gross (no costs) vs Net (with fees/carry) returns")

    gross_summary = st.session_state.gross_summary
    gross_results = st.session_state.gross_results
    net_summary = st.session_state.net_summary
    net_results = st.session_state.net_results

    # CSV Export Section (if enabled)
    if st.session_state.export_details and gross_results and gross_results[0].investment_details is not None:
        st.subheader("📥 Export Detailed Data")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Generate Investment Details CSV"):
                output_path = "investment_details.csv"
                rows = export_investment_details(gross_results, output_path)
                st.success(f"✓ Exported {rows:,} investment records to {output_path}")

                with open(output_path, 'r', encoding='utf-8') as f:
                    csv_data = f.read()

                st.download_button(
                    label="Download Investment Details CSV",
                    data=csv_data,
                    file_name="investment_details.csv",
                    mime="text/csv"
                )

        with col2:
            if st.button("Generate Cash Flow Schedule CSV"):
                output_path = "cash_flow_schedule.csv"
                rows = export_cash_flow_schedules(gross_results, output_path)
                st.success(f"✓ Exported {rows:,} cash flow records to {output_path}")

                with open(output_path, 'r', encoding='utf-8') as f:
                    csv_data = f.read()

                st.download_button(
                    label="Download Cash Flow Schedule CSV",
                    data=csv_data,
                    file_name="cash_flow_schedule.csv",
                    mime="text/csv"
                )

        st.markdown("---")

    # Side-by-side comparison
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💵 Gross Returns")
        st.caption("No fees, carry, or leverage")

        st.markdown("**MOIC Statistics**")
        st.metric("Mean", f"{gross_summary.mean_moic:.2f}x")
        st.metric("Median", f"{gross_summary.median_moic:.2f}x")
        st.metric("5th / 95th Percentile", f"{gross_summary.percentile_5_moic:.2f}x / {gross_summary.percentile_95_moic:.2f}x")

        st.markdown("**IRR Statistics**")
        st.metric("Mean", f"{gross_summary.mean_irr:.2%}")
        st.metric("Median", f"{gross_summary.median_irr:.2%}")
        st.metric("5th / 95th Percentile", f"{gross_summary.percentile_5_irr:.2%} / {gross_summary.percentile_95_irr:.2%}")

    with col2:
        st.markdown("### 💰 Net Returns")
        st.caption("After fees, carry, and leverage")

        st.markdown("**MOIC Statistics**")
        st.metric("Mean", f"{net_summary.mean_moic:.2f}x")
        st.metric("Median", f"{net_summary.median_moic:.2f}x")
        st.metric("5th / 95th Percentile", f"{net_summary.percentile_5_moic:.2f}x / {net_summary.percentile_95_moic:.2f}x")

        st.markdown("**IRR Statistics**")
        st.metric("Mean", f"{net_summary.mean_irr:.2%}")
        st.metric("Median", f"{net_summary.median_irr:.2%}")
        st.metric("5th / 95th Percentile", f"{net_summary.percentile_5_irr:.2%} / {net_summary.percentile_95_irr:.2%}")

    # Distribution Plots
    st.markdown("---")
    st.subheader("Gross Returns Distribution")
    col1, col2 = st.columns(2)

    with col1:
        moics = [r.moic for r in gross_results]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=moics, nbinsx=50, name="Gross MOIC"))
        fig.add_vline(x=gross_summary.mean_moic, line_dash="dash", line_color="red", annotation_text="Mean")
        fig.add_vline(x=gross_summary.median_moic, line_dash="dash", line_color="green", annotation_text="Median")
        fig.update_layout(title="Gross MOIC Distribution", xaxis_title="MOIC", yaxis_title="Frequency", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        irrs = [r.irr * 100 for r in gross_results]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=irrs, nbinsx=50, name="Gross IRR"))
        fig.add_vline(x=gross_summary.mean_irr * 100, line_dash="dash", line_color="red", annotation_text="Mean")
        fig.add_vline(x=gross_summary.median_irr * 100, line_dash="dash", line_color="green", annotation_text="Median")
        fig.update_layout(title="Gross IRR Distribution", xaxis_title="IRR (%)", yaxis_title="Frequency", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Net Returns Distribution")
    col1, col2 = st.columns(2)

    with col1:
        moics = [r.moic for r in net_results]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=moics, nbinsx=50, name="Net MOIC"))
        fig.add_vline(x=net_summary.mean_moic, line_dash="dash", line_color="red", annotation_text="Mean")
        fig.add_vline(x=net_summary.median_moic, line_dash="dash", line_color="green", annotation_text="Median")
        fig.update_layout(title="Net MOIC Distribution", xaxis_title="MOIC", yaxis_title="Frequency", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        irrs = [r.irr * 100 for r in net_results]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=irrs, nbinsx=50, name="Net IRR"))
        fig.add_vline(x=net_summary.mean_irr * 100, line_dash="dash", line_color="red", annotation_text="Mean")
        fig.add_vline(x=net_summary.median_irr * 100, line_dash="dash", line_color="green", annotation_text="Median")
        fig.update_layout(title="Net IRR Distribution", xaxis_title="IRR (%)", yaxis_title="Frequency", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def render_deconstructed_performance_results():
    """Render results for Deconstructed Performance mode (4 stages)."""
    st.subheader("🔬 Deconstructed Performance Analysis")
    st.caption("Alpha decomposition with forward beta simulation and reconstruction")

    alpha_summary = st.session_state.alpha_summary
    alpha_results = st.session_state.alpha_results

    # CSV Export Section (if enabled)
    if st.session_state.export_details and alpha_results and alpha_results[0].investment_details is not None:
        st.subheader("📥 Export Detailed Data")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Generate Investment Details CSV"):
                output_path = "investment_details.csv"
                rows = export_investment_details(alpha_results, output_path)
                st.success(f"✓ Exported {rows:,} investment records to {output_path}")

                with open(output_path, 'r', encoding='utf-8') as f:
                    csv_data = f.read()

                st.download_button(
                    label="Download Investment Details CSV",
                    data=csv_data,
                    file_name="investment_details.csv",
                    mime="text/csv"
                )

        with col2:
            if st.button("Generate Cash Flow Schedule CSV"):
                output_path = "cash_flow_schedule.csv"
                rows = export_cash_flow_schedules(alpha_results, output_path)
                st.success(f"✓ Exported {rows:,} cash flow records to {output_path}")

                with open(output_path, 'r', encoding='utf-8') as f:
                    csv_data = f.read()

                st.download_button(
                    label="Download Cash Flow Schedule CSV",
                    data=csv_data,
                    file_name="cash_flow_schedule.csv",
                    mime="text/csv"
                )

        st.markdown("---")

    # Diagnostic warnings for alpha
    problematic_irr = sum(1 for r in alpha_results if not r.irr_converged)
    negative_cash_flows = sum(1 for r in alpha_results if r.has_negative_cash_flows)
    negative_returns = sum(1 for r in alpha_results if r.negative_total_returned)

    if problematic_irr > 0:
        pct = problematic_irr / len(alpha_results) * 100
        st.warning(f"⚠️ **IRR Convergence Issues:** {problematic_irr:,} simulations ({pct:.1f}%) had IRR calculation difficulties.")

    if negative_cash_flows > 0:
        pct = negative_cash_flows / len(alpha_results) * 100
        st.info(f"ℹ️ **Negative Cash Flows:** {negative_cash_flows:,} simulations ({pct:.1f}%) had negative exit cash flows (alpha underperformance).")

    if negative_returns > 0:
        pct = negative_returns / len(alpha_results) * 100
        st.info(f"ℹ️ **Negative Total Returns:** {negative_returns:,} simulations ({pct:.1f}%) significantly underperformed beta.")

    # Stage 1: Alpha Results
    st.markdown("### Stage 1: Alpha (Excess Returns)")
    st.caption("Returns above beta benchmark using geometric attribution")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**MOIC Statistics**")
        st.metric("Mean", f"{alpha_summary.mean_moic:.2f}x")
        st.metric("Median", f"{alpha_summary.median_moic:.2f}x")
        st.metric("Std Dev", f"{alpha_summary.std_moic:.2f}x")

    with col2:
        st.markdown("**IRR Statistics**")
        st.metric("Mean", f"{alpha_summary.mean_irr:.2%}")
        st.metric("Median", f"{alpha_summary.median_irr:.2%}")
        st.metric("Std Dev", f"{alpha_summary.std_irr:.2%}")

    with col3:
        st.markdown("**Percentiles**")
        st.metric("5th", f"{alpha_summary.percentile_5_moic:.2f}x / {alpha_summary.percentile_5_irr:.2%}")
        st.metric("95th", f"{alpha_summary.percentile_95_moic:.2f}x / {alpha_summary.percentile_95_irr:.2%}")

    # Alpha distribution plots
    st.markdown("#### Alpha Distribution Plots")
    col1, col2 = st.columns(2)

    with col1:
        moics = [r.moic for r in alpha_results]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=moics, nbinsx=50, name="Alpha MOIC"))
        fig.add_vline(x=alpha_summary.mean_moic, line_dash="dash", line_color="red", annotation_text="Mean")
        fig.add_vline(x=alpha_summary.median_moic, line_dash="dash", line_color="green", annotation_text="Median")
        fig.update_layout(title="Alpha MOIC Distribution", xaxis_title="Alpha MOIC", yaxis_title="Frequency", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        irrs = [r.irr * 100 for r in alpha_results]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=irrs, nbinsx=50, name="Alpha IRR"))
        fig.add_vline(x=alpha_summary.mean_irr * 100, line_dash="dash", line_color="red", annotation_text="Mean")
        fig.add_vline(x=alpha_summary.median_irr * 100, line_dash="dash", line_color="green", annotation_text="Median")
        fig.update_layout(title="Alpha IRR Distribution", xaxis_title="Alpha IRR (%)", yaxis_title="Frequency", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Stage 2: Beta Forward Simulation Results
    st.markdown("---")
    if st.session_state.beta_paths is not None and st.session_state.beta_diagnostics is not None:
        st.markdown("### Stage 2: Beta Forward Simulation")
        st.caption("Constant-growth price paths with exact mean, median, and standard deviation. Each path compounds at a single constant rate drawn from N(μ_target, σ_target).")

        beta_paths = st.session_state.beta_paths
        beta_diag = st.session_state.beta_diagnostics

        # Display diagnostics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Historical Data**")
            st.metric("Data Frequency", beta_diag['frequency'].capitalize())
            st.metric("Observations", f"{beta_diag['n_observations']:,}")
            st.metric("Annual Return", f"{beta_diag['mu_hist_annual']:.2%}")

        with col2:
            st.markdown("**Historical Volatility**")
            st.metric("Annual Vol", f"{beta_diag['sigma_hist_annual']:.2%}")
            st.metric("Daily Return", f"{beta_diag['mu_hist_daily']:.4%}")
            st.metric("Paths Generated", f"{beta_diag['n_paths']:,}")

        with col3:
            st.markdown("**Forward View**")
            st.metric("Outlook", beta_diag['outlook'].capitalize())
            st.metric("Confidence", beta_diag['confidence'].capitalize())
            st.metric("Target Return", f"{beta_diag['R_view']:.2%}")

        # Beta path visualization
        st.markdown("#### Beta Path Visualization")

        # Select sample of paths to plot (max 100 for readability)
        n_plot_paths = min(100, len(beta_paths.columns))
        sample_cols = np.random.choice(beta_paths.columns, n_plot_paths, replace=False)

        fig = go.Figure()

        # Plot sample paths (thin lines)
        for col in sample_cols:
            fig.add_trace(go.Scatter(
                x=beta_paths.index,
                y=beta_paths[col],
                mode='lines',
                line=dict(width=0.5, color='lightblue'),
                opacity=0.3,
                showlegend=False,
                hoverinfo='skip'
            ))

        # Calculate and plot median path
        median_path = beta_paths.median(axis=1)
        fig.add_trace(go.Scatter(
            x=beta_paths.index,
            y=median_path,
            mode='lines',
            name='Median',
            line=dict(width=3, color='darkblue')
        ))

        # Calculate and plot percentile bands
        p5 = beta_paths.quantile(0.05, axis=1)
        p95 = beta_paths.quantile(0.95, axis=1)

        fig.add_trace(go.Scatter(
            x=beta_paths.index,
            y=p5,
            mode='lines',
            name='5th Percentile',
            line=dict(width=2, color='red', dash='dash')
        ))

        fig.add_trace(go.Scatter(
            x=beta_paths.index,
            y=p95,
            mode='lines',
            name='95th Percentile',
            line=dict(width=2, color='green', dash='dash')
        ))

        fig.update_layout(
            title=f"Beta Forward Simulation - Constant-Growth Paths ({len(beta_paths.columns)} paths with exact moments)",
            xaxis_title="Date",
            yaxis_title="Price Level (Start: $65.50, Terminal Median: $255.24 = 14.57% annualized)",
            hovermode='x unified',
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Terminal value statistics with consistency check
        terminal_values = beta_paths.iloc[-1, :]
        start_price = beta_diag['start_price']

        # Use TRADING YEARS for consistency with path generation
        # Paths were generated using: years = horizon_days / 252
        trading_years = beta_diag['horizon_days'] / 252

        # Also show calendar info for context
        first_date = beta_paths.index[0]
        last_date = beta_paths.index[-1]
        calendar_years = (last_date - first_date).days / 365.25

        # Convert terminal values to annualized returns using TRADING YEARS
        terminal_moics = terminal_values / start_price
        terminal_returns_annualized = (terminal_moics ** (1 / trading_years)) - 1

        st.markdown("#### Terminal Value Statistics (Annualized Returns)")
        st.caption(f"Over {trading_years:.1f} trading years ({calendar_years:.1f} calendar years) from {first_date.date()} to {last_date.date()}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean Return", f"{terminal_returns_annualized.mean():.2%}")
        with col2:
            st.metric("Median Return", f"{terminal_returns_annualized.median():.2%}")
        with col3:
            st.metric("5th Percentile", f"{terminal_returns_annualized.quantile(0.05):.2%}")
        with col4:
            st.metric("95th Percentile", f"{terminal_returns_annualized.quantile(0.95):.2%}")

        # CONSISTENCY CHECK: Compare terminal statistics with target and actual beta returns
        terminal_median_return = terminal_returns_annualized.median()
        target_return = beta_diag['R_view']

        # Calculate difference
        terminal_vs_target_diff = terminal_median_return - target_return

        # Warning threshold: if difference > 1%, flag it
        if abs(terminal_vs_target_diff) > 0.01:
            st.warning(f"⚠️ **Consistency Check:** Terminal median return ({terminal_median_return:.2%}) differs from target return ({target_return:.2%}) by {terminal_vs_target_diff:.2%}. Expected difference < 1%.")
        else:
            st.success(f"✓ **Consistency Check:** Terminal median return ({terminal_median_return:.2%}) aligns with target return ({target_return:.2%}) within 1%.")

    else:
        st.markdown("### Stage 2: Beta Forward Simulation")
        st.info("⏭️ Beta simulation not run or failed.")

    # Stage 3: Reconstructed Gross Performance
    st.markdown("---")
    if (st.session_state.reconstructed_gross_results is not None and
        st.session_state.reconstructed_gross_summary is not None):
        st.markdown("### Stage 3: Gross Performance (Alpha × Beta)")
        st.caption("Total returns reconstructed by combining alpha with simulated beta paths")

        gross_summary = st.session_state.reconstructed_gross_summary
        gross_results = st.session_state.reconstructed_gross_results

        # Display actual beta returns used in reconstruction
        if st.session_state.beta_recon_diagnostics and st.session_state.beta_diagnostics:
            beta_recon = st.session_state.beta_recon_diagnostics
            beta_target = st.session_state.beta_diagnostics['R_view']

            if beta_recon.get('mean_beta_irr') is not None:
                actual_beta_irr = beta_recon['mean_beta_irr']
                diff = actual_beta_irr - beta_target

                st.markdown("#### Beta Attribution Analysis")
                st.caption(f"Based on {beta_recon['n_investments']:,} investments with ≥30 day holding periods")

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.metric("Target Beta Return", f"{beta_target:.2%}")
                with col_b:
                    st.metric("Actual Mean Beta Return", f"{actual_beta_irr:.2%}",
                              delta=f"{diff:.2%}" if diff != 0 else None)
                with col_c:
                    st.metric("Beta IRR Range",
                              f"{beta_recon['p5_beta_irr']:.2%} to {beta_recon['p95_beta_irr']:.2%}")

                # CROSS-CHECK with Terminal Value Statistics
                if st.session_state.beta_paths is not None:
                    terminal_values = st.session_state.beta_paths.iloc[-1, :]
                    start_price = st.session_state.beta_diagnostics['start_price']
                    # Use TRADING YEARS for consistency
                    trading_years = st.session_state.beta_diagnostics['horizon_days'] / 252
                    terminal_moics = terminal_values / start_price
                    terminal_median_return = ((terminal_moics.median()) ** (1 / trading_years)) - 1

                    # Compare actual beta IRR with terminal median
                    recon_vs_terminal_diff = actual_beta_irr - terminal_median_return

                    if abs(recon_vs_terminal_diff) > 0.02:
                        st.caption(f"⚠️ **Cross-Check:** Terminal median = {terminal_median_return:.2%}, "
                                   f"Reconstruction beta = {actual_beta_irr:.2%}, "
                                   f"Difference = {recon_vs_terminal_diff:+.2%}. "
                                   f"Note: These may differ due to varying investment holding periods.")
                    else:
                        st.caption(f"✓ **Cross-Check:** Terminal median ({terminal_median_return:.2%}) and "
                                   f"reconstruction beta ({actual_beta_irr:.2%}) align within 2%.")

                st.markdown("---")

        # Diagnostic buttons
        diag_col1, diag_col2 = st.columns(2)

        with diag_col1:
            if st.button("📊 Check Reporting Accuracy", help="Compare calculated statistics vs displayed values"):
                with st.spinner("Running diagnostics..."):
                    from fund_simulation.diagnose_reporting import diagnose_statistics_reporting

                    diagnostics = diagnose_statistics_reporting(
                        st.session_state.alpha_results,
                        st.session_state.alpha_summary,
                        st.session_state.reconstructed_gross_results,
                        st.session_state.reconstructed_gross_summary,
                        st.session_state.beta_recon_diagnostics
                    )

                    st.success("✓ Reporting diagnostic complete! Check terminal output for detailed results.")

        with diag_col2:
            if st.button("🔍 Run Beta Sampling Diagnostics", help="Analyze temporal sampling patterns to check for early-period bias"):
                with st.spinner("Running diagnostics..."):
                    from fund_simulation.diagnose_beta_sampling import analyze_beta_temporal_bias

                    diagnostics = analyze_beta_temporal_bias(
                        st.session_state.reconstructed_gross_results,
                        st.session_state.beta_paths,
                        st.session_state.beta_paths.index[0]
                    )

                    st.success("✓ Beta sampling diagnostic complete! Check terminal output for detailed results.")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**MOIC Statistics**")
            st.metric("Mean", f"{gross_summary.mean_moic:.2f}x")
            st.metric("Median", f"{gross_summary.median_moic:.2f}x")
            st.metric("Std Dev", f"{gross_summary.std_moic:.2f}x")

        with col2:
            st.markdown("**IRR Statistics**")
            st.metric("Mean", f"{gross_summary.mean_irr:.2%}")
            st.metric("Median", f"{gross_summary.median_irr:.2%}")
            st.metric("Std Dev", f"{gross_summary.std_irr:.2%}")

        with col3:
            st.markdown("**Percentiles**")
            st.metric("5th", f"{gross_summary.percentile_5_moic:.2f}x / {gross_summary.percentile_5_irr:.2%}")
            st.metric("95th", f"{gross_summary.percentile_95_moic:.2f}x / {gross_summary.percentile_95_irr:.2%}")

        # Gross distribution plots
        st.markdown("#### Reconstructed Gross Distribution Plots")
        col1, col2 = st.columns(2)

        with col1:
            moics = [r.moic for r in gross_results]
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=moics, nbinsx=50, name="Gross MOIC"))
            fig.add_vline(x=gross_summary.mean_moic, line_dash="dash", line_color="red", annotation_text="Mean")
            fig.add_vline(x=gross_summary.median_moic, line_dash="dash", line_color="green", annotation_text="Median")
            fig.update_layout(title="Reconstructed Gross MOIC Distribution", xaxis_title="MOIC", yaxis_title="Frequency", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            irrs = [r.irr * 100 for r in gross_results]
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=irrs, nbinsx=50, name="Gross IRR"))
            fig.add_vline(x=gross_summary.mean_irr * 100, line_dash="dash", line_color="red", annotation_text="Mean")
            fig.add_vline(x=gross_summary.median_irr * 100, line_dash="dash", line_color="green", annotation_text="Median")
            fig.update_layout(title="Reconstructed Gross IRR Distribution", xaxis_title="IRR (%)", yaxis_title="Frequency", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("### Stage 3: Gross Performance Reconstruction")
        st.info("⏭️ Gross reconstruction not available (beta simulation may have failed)")

    # Stage 4: Reconstructed Net Performance
    st.markdown("---")
    if (st.session_state.reconstructed_net_results is not None and
        st.session_state.reconstructed_net_summary is not None):
        st.markdown("### Stage 4: Net Performance (After Costs)")
        st.caption("Final returns after applying fees, carry, and leverage")

        net_summary = st.session_state.reconstructed_net_summary
        net_results = st.session_state.reconstructed_net_results

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**MOIC Statistics**")
            st.metric("Mean", f"{net_summary.mean_moic:.2f}x")
            st.metric("Median", f"{net_summary.median_moic:.2f}x")
            st.metric("Std Dev", f"{net_summary.std_moic:.2f}x")

        with col2:
            st.markdown("**IRR Statistics**")
            st.metric("Mean", f"{net_summary.mean_irr:.2%}")
            st.metric("Median", f"{net_summary.median_irr:.2%}")
            st.metric("Std Dev", f"{net_summary.std_irr:.2%}")

        with col3:
            st.markdown("**Percentiles**")
            st.metric("5th", f"{net_summary.percentile_5_moic:.2f}x / {net_summary.percentile_5_irr:.2%}")
            st.metric("95th", f"{net_summary.percentile_95_moic:.2f}x / {net_summary.percentile_95_irr:.2%}")

        # Cost breakdown
        st.markdown("#### Cost Breakdown")
        col1, col2, col3, col4 = st.columns(4)

        avg_fees = sum(r.fees_paid for r in net_results) / len(net_results)
        avg_carry = sum(r.carry_paid for r in net_results) / len(net_results)
        avg_leverage = sum(r.leverage_cost for r in net_results) / len(net_results)
        avg_gross_profit = sum(r.gross_profit for r in net_results) / len(net_results)

        with col1:
            st.metric("Avg Gross Profit", f"${avg_gross_profit:,.0f}")
        with col2:
            st.metric("Avg Mgmt Fees", f"${avg_fees:,.0f}")
        with col3:
            st.metric("Avg Carry", f"${avg_carry:,.0f}")
        with col4:
            st.metric("Avg Leverage Cost", f"${avg_leverage:,.0f}")

        # Net distribution plots
        st.markdown("#### Reconstructed Net Distribution Plots")
        col1, col2 = st.columns(2)

        with col1:
            moics = [r.moic for r in net_results]
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=moics, nbinsx=50, name="Net MOIC"))
            fig.add_vline(x=net_summary.mean_moic, line_dash="dash", line_color="red", annotation_text="Mean")
            fig.add_vline(x=net_summary.median_moic, line_dash="dash", line_color="green", annotation_text="Median")
            fig.update_layout(title="Reconstructed Net MOIC Distribution", xaxis_title="MOIC", yaxis_title="Frequency", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            irrs = [r.irr * 100 for r in net_results]
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=irrs, nbinsx=50, name="Net IRR"))
            fig.add_vline(x=net_summary.mean_irr * 100, line_dash="dash", line_color="red", annotation_text="Mean")
            fig.add_vline(x=net_summary.median_irr * 100, line_dash="dash", line_color="green", annotation_text="Median")
            fig.update_layout(title="Reconstructed Net IRR Distribution", xaxis_title="IRR (%)", yaxis_title="Frequency", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("### Stage 4: Net Performance Reconstruction")
        st.info("⏭️ Net reconstruction not available (gross reconstruction may have failed)")


if __name__ == "__main__":
    main()
