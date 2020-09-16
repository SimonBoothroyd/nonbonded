def property_type_to_title(property_type: str, n_components: int):

    from openff.evaluator import properties, unit

    abbreviations = {
        "Density": r"\rho",
        "DielectricConstant": r"\epsilon",
        "EnthalpyOfMixing": r"H_{mix}",
        "EnthalpyOfVaporization": r"H_{vap}",
        "ExcessMolarVolume": r"V_{ex}",
        "SolvationFreeEnergy": r"G_{solv}",
    }

    property_class = getattr(properties, property_type)
    property_unit = property_class.default_unit()

    unit_string = (
        "" if property_unit == unit.dimensionless else f" ({property_unit:~P})"
    )

    abbreviation = abbreviations.get(property_type, property_type)

    if "FreeEnergy" not in property_type and n_components > 1:
        abbreviation = f"{abbreviation} (x)"

    return f"${abbreviation}$ {unit_string}"


def plot_categories(x, y, hue, **kwargs):

    from matplotlib import pyplot

    data = kwargs.pop("data")

    plot_data = data.pivot(index=x, columns=hue, values=y)
    plot_data.plot(kind="bar", ax=pyplot.gca(), **kwargs)


def plot_scatter(x, y, x_err, y_err, hue, hue_order, **kwargs):

    from matplotlib import pyplot

    data = kwargs.pop("data")
    colors = kwargs.pop("color")

    for hue_value, color in zip(hue_order, colors):

        hue_data = data[data[hue] == hue_value]

        if len(hue_data) == 0:
            continue

        pyplot.errorbar(
            hue_data[x],
            hue_data[y],
            xerr=hue_data[x_err],
            yerr=hue_data[y_err],
            label=hue_value,
            color=color,
            **kwargs,
        )

    pyplot.gca().plot(
        [0, 1], [0, 1], transform=pyplot.gca().transAxes, color="darkgrey"
    )
