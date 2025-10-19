"""Monte Carlo Fund Simulation - Streamlit Application"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

from fund_simulation.data_import import parse_csv_file
from fund_simulation.models import SimulationConfiguration
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.statistics import calculate_summary_statistics


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
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None

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
    - Column 4: Latest Date (same formats)
    - Column 5: MOIC (Multiple on Invested Capital, e.g., 2.5 for 2.5x)
    - Column 6: IRR (as decimal, e.g., 0.25 for 25%)
    """)

    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=['csv'],
        help="CSV format: investment_name, fund_name, entry_date, latest_date, MOIC, IRR"
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
                    'Latest Date': inv.latest_date.date(),
                    'MOIC': f"{inv.moic:.2f}x",
                    'IRR': f"{inv.irr:.2%}"
                }
                for inv in investments
            ])
            st.dataframe(df, use_container_width=True, height=400)

            # Store in session state
            st.session_state.investments = investments


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
        investment_count_std=investment_count_std
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

    if st.button("▶️ Run Simulation", type="primary"):
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(fraction):
            progress_bar.progress(fraction)
            status_text.text(f"Progress: {fraction*100:.1f}%")

        # Run simulation
        with st.spinner("Running simulation..."):
            results = run_monte_carlo_simulation(
                investments,
                config,
                progress_callback=update_progress
            )

        # Calculate statistics
        summary = calculate_summary_statistics(results, config)

        # Store results
        st.session_state.results = results
        st.session_state.summary = summary

        st.success(f"✓ Completed {len(results):,} simulations")
        progress_bar.empty()
        status_text.empty()


def render_results():
    st.header("Simulation Results")

    if st.session_state.summary is None:
        st.warning("⚠️ Please run simulation first")
        return

    summary = st.session_state.summary
    results = st.session_state.results

    # Summary statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("MOIC Statistics")
        st.metric("Mean", f"{summary.mean_moic:.2f}x")
        st.metric("Median", f"{summary.median_moic:.2f}x")
        st.metric("Std Dev", f"{summary.std_moic:.2f}x")
        st.metric("5th Percentile", f"{summary.percentile_5_moic:.2f}x")
        st.metric("95th Percentile", f"{summary.percentile_95_moic:.2f}x")

    with col2:
        st.subheader("IRR Statistics")
        st.metric("Mean", f"{summary.mean_irr:.2%}")
        st.metric("Median", f"{summary.median_irr:.2%}")
        st.metric("Std Dev", f"{summary.std_irr:.2%}")
        st.metric("5th Percentile", f"{summary.percentile_5_irr:.2%}")
        st.metric("95th Percentile", f"{summary.percentile_95_irr:.2%}")

    with col3:
        st.subheader("Simulation Info")
        st.metric("Total Runs", f"{summary.total_runs:,}")
        st.metric("Fund", summary.config.fund_name)
        st.metric("Manager", summary.config.fund_manager)
        st.text(f"Completed: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Percentile table
    st.subheader("Percentile Distribution")
    percentile_df = pd.DataFrame({
        'Percentile': ['5th', '25th', '50th (Median)', '75th', '95th'],
        'MOIC': [
            f"{summary.percentile_5_moic:.2f}x",
            f"{summary.percentile_25_moic:.2f}x",
            f"{summary.median_moic:.2f}x",
            f"{summary.percentile_75_moic:.2f}x",
            f"{summary.percentile_95_moic:.2f}x"
        ],
        'IRR': [
            f"{summary.percentile_5_irr:.2%}",
            f"{summary.percentile_25_irr:.2%}",
            f"{summary.median_irr:.2%}",
            f"{summary.percentile_75_irr:.2%}",
            f"{summary.percentile_95_irr:.2%}"
        ]
    })
    st.dataframe(percentile_df, use_container_width=True, hide_index=True)

    # Histograms
    st.subheader("Distribution Plots")

    col1, col2 = st.columns(2)

    with col1:
        # MOIC histogram
        moics = [r.moic for r in results]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=moics, nbinsx=50, name="MOIC"))
        fig.add_vline(
            x=summary.mean_moic,
            line_dash="dash",
            line_color="red",
            annotation_text="Mean",
            annotation_position="top right"
        )
        fig.add_vline(
            x=summary.median_moic,
            line_dash="dash",
            line_color="green",
            annotation_text="Median",
            annotation_position="top left"
        )
        fig.update_layout(
            title="MOIC Distribution",
            xaxis_title="MOIC",
            yaxis_title="Frequency",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # IRR histogram
        irrs = [r.irr * 100 for r in results]  # Convert to percentage
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=irrs, nbinsx=50, name="IRR"))
        fig.add_vline(
            x=summary.mean_irr * 100,
            line_dash="dash",
            line_color="red",
            annotation_text="Mean",
            annotation_position="top right"
        )
        fig.add_vline(
            x=summary.median_irr * 100,
            line_dash="dash",
            line_color="green",
            annotation_text="Median",
            annotation_position="top left"
        )
        fig.update_layout(
            title="IRR Distribution",
            xaxis_title="IRR (%)",
            yaxis_title="Frequency",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
