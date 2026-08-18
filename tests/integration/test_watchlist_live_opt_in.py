from __future__ import annotations

import os

import pytest

from app.watchlist.services import fetch_public_page


@pytest.mark.skipif(
    os.getenv("CAREEROS_RUN_LIVE_WATCHLIST_TESTS") != "1",
    reason="Live careers-page checks are opt-in only.",
)
def test_live_careers_page_fetch_opt_in() -> None:
    html = fetch_public_page("https://www.catl.com/en/careers/", timeout=20)

    assert html.strip()
