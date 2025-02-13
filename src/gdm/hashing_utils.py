from infrasys import Component


def _remove_keys_from_dict(model_dict: dict, key_names: list[str] = ["name", "uuid"]) -> dict:
    """Method recursively removes keys from the model

    Args:
        model_dict (dict): model in dict representation
        key_names (list[str]): keys to remove from the model

    Returns:
        dict: reduced model dictionary
    """
    for key_name in key_names:
        if key_name in model_dict:
            model_dict.pop(key_name)
        for k, v in model_dict.items():
            if isinstance(v, dict):
                model_dict[k] = _remove_keys_from_dict(v)
            elif isinstance(v, list):
                values = []
                for value in v:
                    if isinstance(value, dict):
                        value = _remove_keys_from_dict(value)
                    values.append(value)
                    model_dict[k] = values
    return model_dict


def hash_model(model: Component, key_names: list[str] = ["name", "uuid"]) -> int:
    """Return hash of the passed model

    Args:
        model (Component): Instance of a derived infrasys Component model
        key_names (list[str], optional): List of keys to be removed from the model. Defaults to ["name", "uuid"].

    Returns:
        int: model hash
    """
    model_dict = (
        model.model_dump()
    )  # TODO: exclude={"name"} seems not to work  well with list of objects
    cleaned_model = _remove_keys_from_dict(model_dict, key_names)
    return hash(str(cleaned_model))
