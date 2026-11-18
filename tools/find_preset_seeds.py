"""Prüft für jedes Preset, ob sein Zufalls-Seed (ab 500000, nie 1000 bis 1029 der Abstimmung und 100000 bis 100029 der Messung) die Geschichte des Presets auf dem Lauf zeigt,
und sucht sonst den nächsten Seed ab 500000, bei dem das Kriterium aus hld_stories.py erfüllt ist.

Aufruf:  python tools/find_preset_seeds.py            (gibt je Preset Seed, Kosten auf dem Lauf und im Zellmittel aus)
         python tools/find_preset_seeds.py --suche    (sucht für Presets, deren Seed die Geschichte nicht zeigt, den nächsten passenden Seed)
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import hld_constants as C  # noqa: E402
import hld_evaluation as E  # noqa: E402
import hld_results as R  # noqa: E402
import hld_stories as S  # noqa: E402


def settings(name, seed=None):
    p = C.PRESETS[name]
    return E.Settings(p["lam"], p["ca2"], p["span"], p["cap"], p["wissen"], p["seed"] if seed is None else seed)


def main():
    suche = "--suche" in sys.argv
    for name in C.PRESETS:
        st = settings(name)
        an = E.analyse(st)
        cell = R.cell_of(st.lam, st.ca2, st.span, st.cap)
        ok = S.STORIES[name](an)
        line = (f"{name}: Seed {st.seed}, Geschichte {'ja' if ok else 'NEIN'}; Lauf Q {an['rules']['Q']['cost']:.3f} T {an['rules']['T']['cost']:.3f} F {an['rules']['F']['cost']:.3f} "
                f"Stufe {an['stage']['cost']:.3f} Optimum {an['opt']['cost']:.3f}; Zellmittel Q {cell['cost']['Q']:.3f} T {cell['cost']['T']:.3f} F {cell['cost']['F']:.3f} Optimum {cell['opt']['cost']:.3f}")
        print(line)
        if not ok and suche:
            for seed in range(500000, 500200):
                if S.STORIES[name](E.analyse(settings(name, seed))):
                    print(f"   -> passender Seed: {seed}")
                    break


if __name__ == "__main__":
    main()
