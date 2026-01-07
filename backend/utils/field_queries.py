def build_prompt(field: str, context: str, valid_values: list = None):
    base = f"From the following SOW context, extract the {field}.\nContext:\n{context}\n\nAnswer only with the {field}."
    if valid_values:
        base += f"\nChoose one from the following valid values:\n{valid_values}"
    return base
