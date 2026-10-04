"""Exercise app.py without Streamlit installed, using a minimal stub.

This validates the UI's data plumbing (attribute names, dict keys, imports)
so that ``streamlit run app.py`` will not fail on first launch.
"""

from __future__ import annotations

import sys
import types
from contextlib import contextmanager


class _Stub:
    """Records calls and returns itself for any unknown attribute."""

    def __init__(self, name="stub"):
        self._name = name
        self.calls = []

    def __getattr__(self, item):
        if item.startswith("_"):
            raise AttributeError(item)

        def _call(*args, **kwargs):
            self.calls.append((item, args, kwargs))
            return _Stub(f"{self._name}.{item}")

        return _call

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return iter(())

    def __contains__(self, item):
        return False

    def __getitem__(self, item):
        return _Stub(f"{self._name}[{item!r}]")

    def __call__(self, *args, **kwargs):
        self.calls.append(("__call__", args, kwargs))
        return _Stub(self._name)


def _columns(count):
    """Match Streamlit: st.columns(4) or st.columns([3, 2])."""
    n = count if isinstance(count, int) else len(count)
    return [_Stub("col") for _ in range(n)]


class _State(dict):
    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value


def install_stub() -> types.ModuleType:
    """Register a fake ``streamlit`` module in ``sys.modules``."""
    module = types.ModuleType("streamlit")

    module.set_page_config = lambda *a, **k: None
    module.cache_resource = lambda func=None, **k: (
        func if func is not None else (lambda f: f)
    )
    module.title = lambda *a, **k: None
    module.header = lambda *a, **k: None
    module.subheader = lambda *a, **k: None
    module.caption = lambda *a, **k: None
    module.markdown = lambda *a, **k: None
    module.info = lambda *a, **k: None
    module.warning = lambda *a, **k: None
    module.write = lambda *a, **k: None
    module.divider = lambda *a, **k: None
    module.expander = lambda *a, **k: _Stub("expander")
    module.container = lambda *a, **k: _Stub("container")
    module.tabs = lambda labels: [_Stub("tab") for _ in labels]
    module.table = lambda data: _Stub("table")
    module.metric = lambda *a, **k: _Stub("metric")
    module.columns = lambda count: _columns(count)
    module.text_input = lambda label, value="": value
    module.date_input = lambda label, value=None, **k: value
    module.number_input = lambda label, min_value=0, value=0, step=1: value
    module.slider = lambda label, min_value=0, max_value=100, value=50, step=1: value
    module.selectbox = lambda label, options, **k: options[0]
    module.button = lambda *a, **k: False

    session_state = _State()
    module.session_state = session_state
    module.sidebar = _Stub("sidebar")

    sys.modules["streamlit"] = module
    return module


def main() -> None:
    install_stub()

    import app
    from predictor import Predictor

    # 1. The prediction path with real objects.
    predictor = Predictor()
    prediction = predictor.predict("Arsenal", "Chelsea", "2026-10-04")
    app.render_prediction(prediction)
    print("OK  render_prediction")

    # 2. Every card dict shape reaches the renderer.
    for reading in (prediction.reading_a, prediction.reading_b):
        app.team_panel(reading.to_dict(), "x")
    print("OK  team_panel")

    # 3. Match card + single card row.
    app.card_row(prediction.match_card.to_dict(), 1)
    print("OK  card_row")

    # 4. Deck browser iterates all 78 cards.
    app.deck_browser()
    print("OK  deck_browser")

    # 5. Sidebar returns the expected 6-tuple.
    controls = app.sidebar()
    assert len(controls) == 6, controls
    print("OK  sidebar ->", controls)

    # 6. Full entry point renders without raising.
    app.main()
    print("OK  main")

    print("\napp.py plumbing verified (no Streamlit required)")


if __name__ == "__main__":
    main()