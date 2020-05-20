import numpy


def reorder_data_frame(data_frame):
    """ Re-order the substance columns of a data frame so that the individual
    components are alphabetically sorted.

    Parameters
    ----------
    data_frame: pandas.DataFrame
        The data frame to re-order.

    Returns
    -------
    pandas.DataFrame
        The re-ordered data frame.
    """

    max_n_substances = data_frame["N Components"].max()

    component_headers = [f"Component {i + 1}" for i in range(max_n_substances)]
    component_order = numpy.argsort(data_frame[component_headers], axis=1)

    substance_headers = ["Component", "Role", "Mole Fraction", "Exact Amount"]

    ordered_data_frame = data_frame.copy()

    #
    for component_index in range(max_n_substances):

        indices = component_order[f"Component {component_index + 1}"]

        for substance_header in substance_headers:

            component_header = f"{substance_header} {component_index + 1}"

            for replacement_index in range(max_n_substances):

                if component_index == replacement_index:
                    continue

                replacement_header = f"{substance_header} {replacement_index + 1}"

                ordered_data_frame[component_header] = numpy.where(
                    indices == replacement_index,
                    data_frame[replacement_header],
                    data_frame[component_header],
                )

    return ordered_data_frame
