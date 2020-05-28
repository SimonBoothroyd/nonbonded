_property_abbreviations = {
    "Density": r"\rho",
    "DielectricConstant": r"$\epsilon$",
    "EnthalpyOfMixing": r"$H_{mix}$",
    "EnthalpyOfVaporization": r"$H_{vap}$",
    "ExcessMolarVolume": r"$V_{ex}$",
    "SolvationFreeEnergy": r"$G_{solv}$",
}


def property_type_to_title(property_type: str, n_components: int):

    abbreviation = _property_abbreviations.get(property_type, property_type)

    if "FreeEnergy" not in property_type and n_components > 1:

        abbreviation = f"{abbreviation} (x)"

    return abbreviation


def plot_categories_with_custom_ci(x, y, hue, lower_bound, upper_bound, **kwargs):

    import numpy
    from matplotlib import pyplot

    data = kwargs.pop("data")

    lower_ci = data.pivot(index=x, columns=hue, values=lower_bound)
    upper_ci = data.pivot(index=x, columns=hue, values=upper_bound)

    values = data.pivot(index=x, columns=hue, values=y)

    lower_ci = values - lower_ci
    upper_ci = upper_ci - values

    ci = []

    for column in lower_ci:
        ci.append([lower_ci[column].values, upper_ci[column].values])

    ci = numpy.abs(ci)

    plot_data = data.pivot(index=x, columns=hue, values=y)
    plot_data.plot(kind="bar", yerr=ci, ax=pyplot.gca(), **kwargs)


def plot_categories(x, y, hue, **kwargs):

    from matplotlib import pyplot

    data = kwargs.pop("data")

    plot_data = data.pivot(index=x, columns=hue, values=y)
    plot_data.plot(kind="bar", ax=pyplot.gca(), **kwargs)


def plot_bar_with_custom_ci(x, y, lower_bound, upper_bound, **kwargs):

    import numpy
    from matplotlib import pyplot

    data = kwargs.pop("data")
    colors = kwargs.pop("color")

    for row_index, (_, row) in enumerate(data.iterrows()):

        ci = numpy.abs([[row[y] - row[lower_bound]], [row[upper_bound] - row[y]]])

        pyplot.bar(
            x=row[x], height=row[y], yerr=ci, label=row[x], color=colors[row_index]
        )


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


def plot_gradient(x, y, hue, hue_order, **kwargs):

    import numpy
    from matplotlib import pyplot

    data = kwargs.pop("data")
    colors = kwargs.pop("color")

    for hue_value, color in zip(hue_order, colors):

        hue_data = data[data[hue] == hue_value]

        if len(hue_data) == 0:
            continue

        x_value = hue_data[x].values[0]
        y_value = hue_data[y].values[0]

        norm = numpy.sqrt(x_value * x_value + y_value * y_value)

        x_normalized = x_value / norm
        y_normalized = y_value / norm

        pyplot.plot(
            [0.0, x_normalized], [0.0, y_normalized], color=color, linestyle="--"
        )
        pyplot.plot([0.0, x_value], [0.0, y_value], label=hue_value, color=color)

    axis = pyplot.gca()

    # Move left y-axis and bottim x-axis to centre, passing through (0,0)
    axis.spines["left"].set_position("center")
    axis.spines["bottom"].set_position("center")

    # Eliminate upper and right axes
    axis.spines["right"].set_color("none")
    axis.spines["top"].set_color("none")

    # Show ticks in the left and lower axes only
    # axis.xaxis.set_ticks_position('bottom')
    # axis.yaxis.set_ticks_position('left')
