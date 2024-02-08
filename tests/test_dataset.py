import pytest


from gdm.dataset.sql_interface import SQLiteCostDB


@pytest.fixture
def sqlite_instance(tmp_path):
    sqlite_file_name = tmp_path / "test.sqlite"
    with SQLiteCostDB(sqlite_file_name) as db_instance:
        yield db_instance


DATASET_CLASSES = []


@pytest.mark.parametrize("dataset_type", DATASET_CLASSES)
def test_catalog_examples(dataset_type):
    dataset_type.example()


@pytest.mark.parametrize("dataset_type", DATASET_CLASSES)
def test_cost_classes(sqlite_instance, dataset_type):
    sample = dataset_type.example()
    sqlite_instance.add_cost(sample)
    datasets = sqlite_instance.get_costs(dataset_type)

    assert isinstance(datasets, list), f"{datasets=} must be of type list."
    assert len(datasets) == 1, f"{datasets} must have one element."

    item = sqlite_instance.get_cost(dataset_type, datasets[0].id)

    assert isinstance(item, dataset_type), f"{item=} must of type {dataset_type.__class__}"
