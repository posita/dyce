# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================


def fig_callback(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_great_weapon_fighting.py
    # --8<-- [start:core]
    from dyce import H, HResult, expand

    single_attack = 2 @ H(6) + 5

    def gwf_2014(result: HResult[int]) -> H[int] | int:
        # Re-roll either die if it is a one or two
        return result.h if result.outcome in (1, 2) else result.outcome

    def gwf_2024(result: HResult[int]) -> H[int] | int:
        # Ones and twos are promoted to 3s
        return 3 if result.outcome in (1, 2) else result.outcome

    h_gwf_2014 = 2 @ expand(gwf_2014, H(6)) + 5
    h_gwf_2024 = 2 @ expand(gwf_2024, H(6)) + 5
    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_great_weapon_fighting.py
    # --8<-- [start:table]
    import pandas as pd

    data = [
        {outcome: float(prob) for outcome, prob in h.probability_items()}
        for h in (single_attack, h_gwf_2014, h_gwf_2024)
    ]
    label_sa = "Normal attack"
    label_gwf_2014 = "\u201cGWF\u201d (2014)"
    label_gwf_2024 = "\u201cGWF\u201d (2024)"
    df = pd.DataFrame(data, index=[label_sa, label_gwf_2014, label_gwf_2024])
    # --8<-- [end:table]

    # Display df as table
    import jinja2  # ruff: ignore[unused-import]

    # NOTE: Translates to df.style.format("{:.0%}") in docs/assets/nb_great_weapon_fighting.py
    print(df.style.format("{:.0%}").to_html())

    # NOTE: Changes to this section should be propagated to docs/assets/nb_great_weapon_fighting.py
    # --8<-- [start:viz]

    from dyce.viz.matplotlib import plot_ridge

    ax = plot_ridge(
        single_attack,
        h_gwf_2014,
        h_gwf_2024,
        labels=[label_sa, label_gwf_2014, label_gwf_2024],
        overlap=2.0,
    )
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    ax.tick_params(colors=line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)
