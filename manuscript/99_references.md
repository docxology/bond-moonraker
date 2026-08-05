# References

Sources for the models implemented in `src/moonraker/`. Every entry is a real,
checkable publication; the trailing key matches `manuscript/references.bib`.

1. Kelley, J. E. & Walker, M. R. (1959). Critical-Path Planning and Scheduling.
   *Proceedings of the Eastern Joint Computer Conference*, 160–173. — the CPM
   solver in ``shuttle_ops.py`` and the time-cost crash in
   ``schedule_crashing.py``. `kelley1959critical`
2. Vallado, D. A. (2013). *Fundamentals of Astrodynamics and Applications*
   (4th ed.). Microcosm Press. — the two-body orbital mechanics and pass
   geometry of ``orbital_logistics.py``. `vallado2013astrodynamics`
3. Hohmann, W. (1925). *Die Erreichbarkeit der Himmelskörper*. R. Oldenbourg. —
   the minimum-energy two-impulse transfer in ``orbital_transfer.py``.
   `hohmann1925`
4. Tsiolkovsky, K. E. (1903). Exploration of Cosmic Space by Means of Reaction
   Devices. *Nauchnoye Obozreniye*. — the rocket equation sizing the resupply
   propellant in ``orbital_transfer.py``. `tsiolkovsky1903`
5. Clohessy, W. H. & Wiltshire, R. S. (1960). Terminal Guidance System for
   Satellite Rendezvous. *Journal of the Aerospace Sciences*, 27(9), 653–658. —
   the linearised relative-motion model in ``rendezvous.py``. `clohessy1960`
6. Stoll, A. M. (1956). Human Tolerance to Positive G as Determined by the
   Physiological End Points. *Journal of Aviation Medicine*, 27(4), 356–367. —
   the shape of the +Gz tolerance envelope fitted in
   ``centrifuge.max_sustained_duration``. `stoll1956human`
7. Burton, R. R. (1988). G-Induced Loss of Consciousness: Definition, History,
   Current Status. *Aviation, Space, and Environmental Medicine*, 59(1), 2–5. —
   the +Gz exposure and gradual-onset-rate basis for
   ``centrifuge_training.py``. `burton1988`
8. Gilbert, L. (dir.) (1979). *Moonraker* [Motion picture]. Eon Productions /
   United Artists. Screenplay by Christopher Wood. — the source concept for the
   DRAX mission. `moonraker1979`

The tolerance envelope in ``centrifuge.max_sustained_duration`` is a
deterministic power-law *fit* in the shape of the published +Gz curves, not a
reproduction of tabulated values from any single source. Treat it as a
modelling choice documented at its point of use rather than as measured
physiology — which is why §Results reports the certification verdict it
produces rather than asserting a physiological fact.
