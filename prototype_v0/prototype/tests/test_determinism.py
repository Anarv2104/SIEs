"""Run the simulation twice and assert the event logs are byte-identical."""

from sie.main import build_simulation, run_simulation


def test_deterministic_logs():
    # Run 1
    kernel1, agents1 = build_simulation()
    run_simulation(kernel1, agents1)
    log1 = kernel1.log.to_json()

    # Run 2
    kernel2, agents2 = build_simulation()
    run_simulation(kernel2, agents2)
    log2 = kernel2.log.to_json()

    assert log1 == log2, "Event logs differ between runs — simulation is non-deterministic"
    assert len(kernel1.log.events) > 0, "No events produced"
