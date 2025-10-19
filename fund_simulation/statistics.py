"""Statistical analysis of simulation results"""

import numpy as np
from datetime import datetime
from typing import List

from .models import SimulationResult, SimulationSummary, SimulationConfiguration


def calculate_summary_statistics(
    results: List[SimulationResult],
    config: SimulationConfiguration
) -> SimulationSummary:
    """
    Calculate summary statistics from simulation results.

    Args:
        results: List of simulation results
        config: Configuration used for simulation

    Returns:
        SimulationSummary object with all statistics
    """
    # Extract MOIC and IRR arrays
    moics = np.array([r.moic for r in results])
    irrs = np.array([r.irr for r in results])

    # Calculate MOIC statistics
    mean_moic = float(np.mean(moics))
    median_moic = float(np.median(moics))
    std_moic = float(np.std(moics))
    min_moic = float(np.min(moics))
    max_moic = float(np.max(moics))
    p5_moic = float(np.percentile(moics, 5))
    p25_moic = float(np.percentile(moics, 25))
    p75_moic = float(np.percentile(moics, 75))
    p95_moic = float(np.percentile(moics, 95))

    # Calculate IRR statistics
    mean_irr = float(np.mean(irrs))
    median_irr = float(np.median(irrs))
    std_irr = float(np.std(irrs))
    min_irr = float(np.min(irrs))
    max_irr = float(np.max(irrs))
    p5_irr = float(np.percentile(irrs, 5))
    p25_irr = float(np.percentile(irrs, 25))
    p75_irr = float(np.percentile(irrs, 75))
    p95_irr = float(np.percentile(irrs, 95))

    return SimulationSummary(
        config=config,
        total_runs=len(results),
        timestamp=datetime.now(),
        mean_moic=mean_moic,
        median_moic=median_moic,
        std_moic=std_moic,
        min_moic=min_moic,
        max_moic=max_moic,
        percentile_5_moic=p5_moic,
        percentile_25_moic=p25_moic,
        percentile_75_moic=p75_moic,
        percentile_95_moic=p95_moic,
        mean_irr=mean_irr,
        median_irr=median_irr,
        std_irr=std_irr,
        min_irr=min_irr,
        max_irr=max_irr,
        percentile_5_irr=p5_irr,
        percentile_25_irr=p25_irr,
        percentile_75_irr=p75_irr,
        percentile_95_irr=p95_irr
    )
