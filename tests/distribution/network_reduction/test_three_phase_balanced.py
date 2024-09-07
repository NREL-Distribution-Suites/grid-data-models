from pathlib import Path


from gdm.distribution.model_reduction.three_phase_balanced import ThreePhaseBalancedReduction


def test_three_phase_balanced_reduction():
    mdoel_path = Path(
        "C:/Users/alatif/Desktop/P3U__2018__AUS__oedi-data-lake_opendss_no_loadshapes/p3uhs9_1247.json"
    )
    reducer = ThreePhaseBalancedReduction.from_json(mdoel_path)
    primary_model = reducer.build()
    primary_model.info()
