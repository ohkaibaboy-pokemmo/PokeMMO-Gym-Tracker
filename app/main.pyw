import tracker.ui as ui_module

from tracker.app_icon import install_app_icon
from tracker.async_replay import install_async_replay
from tracker.character_export import install_character_export
from tracker.compact_priority import install_compact_priority
from tracker.compact_row_snap import install_compact_row_snap
from tracker.compact_type_icons import install_compact_type_icons
from tracker.compact_ui import CompactWindow
from tracker.dashboard_action_grouping import install_dashboard_action_grouping
from tracker.dashboard_center_chrome import install_dashboard_center_chrome
from tracker.dashboard_compact_button import install_dashboard_compact_button
from tracker.dashboard_detector import install_dashboard_detector
from tracker.dashboard_detector_polish import install_dashboard_detector_polish
from tracker.dashboard_earnings_split import install_dashboard_earnings_split
from tracker.dashboard_earnings_window import install_dashboard_earnings_window
from tracker.dashboard_final_polish import install_dashboard_final_polish
from tracker.dashboard_full_refresh import install_full_view_refresh
from tracker.dashboard_gym_list import install_dashboard_gym_list
from tracker.dashboard_header_responsive import install_dashboard_header_responsive
from tracker.dashboard_kpi_alignment import install_dashboard_kpi_alignment
from tracker.dashboard_legacy_guard import install_legacy_dashboard_guard
from tracker.dashboard_resize_smoothing import install_dashboard_resize_smoothing
from tracker.dashboard_scaling import install_dashboard_scaling
from tracker.dashboard_scrollbar_integration import install_dashboard_scrollbars
from tracker.dashboard_table_alignment import install_dashboard_table_alignment
from tracker.dashboard_ui import install_dashboard
from tracker.earnings_ui import install_earnings
from tracker.leader_art_integration import install_leader_art
from tracker.money_style import install_game_money_style
from tracker.presentation import install_presentation
from tracker.type_icon_overrides import install_type_icon_overrides
from tracker.window_minimize import install_compact_minimize


# App methods resolve CompactWindow from tracker.ui at runtime. Replacing that
# class here keeps the compact presentation isolated from the full-view logic.
install_compact_priority(CompactWindow)
install_compact_type_icons(CompactWindow)
install_compact_minimize(CompactWindow)
# Compact remains small, but its initial height is nudged only enough to end on
# a complete route row so the bottom gym is never shown as an awkward half-row.
install_compact_row_snap(CompactWindow)
ui_module.CompactWindow = CompactWindow
App = ui_module.App


if __name__ == "__main__":
    app = App()
    # Replace the default Tk feather for the root window and future Toplevels.
    # The Windows executable receives the same project-owned artwork at build time.
    install_app_icon(app)
    install_presentation(app)
    install_leader_art(app)
    install_earnings(app)
    # Historical log replay used to run synchronously on Tk's UI thread. Install
    # the batched controller before visible dashboard buttons are created so large
    # replays stay responsive and do not interleave with the live tailer.
    install_async_replay(app)
    # v0.6 is being developed as a presentation layer over the proven tracker
    # engine. Build dashboard-owned widgets before scaling so every component
    # participates in the existing explicit 0.85x-2.0x scale controller.
    install_dashboard(app)
    install_dashboard_compact_button(app)
    # Full-view refresh is presentation-only. It replaces the visible header with
    # the approved muted Poké Ball / compact KPI treatment while leaving Compact
    # and Detector untouched.
    install_full_view_refresh(app)
    install_legacy_dashboard_guard(app)
    install_game_money_style(app)
    # Type-icon PNG overrides are shared by Full and Compact. Missing/invalid
    # files fall back to project-owned local symbols/mini markers.
    install_type_icon_overrides(app)
    # Alignment is now geometry consumed directly by the lightweight Canvas Gym
    # Route; keep the compatibility installer so older startup assumptions remain
    # harmless while the helper stays independently regression-tested.
    install_dashboard_table_alignment()
    # Full route rows are drawn directly on a Canvas over the proven hidden
    # Treeview model. This avoids hundreds of child widgets repainting during
    # native Windows resizing while preserving selection, portraits and semantics.
    install_dashboard_gym_list(app)
    # The route card keeps its context header, but v0.6 intentionally exposes no
    # manual state mutation controls. Tracker state is derived from PokeMMO logs.
    install_dashboard_center_chrome(app)
    install_dashboard_detector(app)
    # Replaying an already-seen log should replace its previous Detector session,
    # not append duplicate presentation noise. Short histories are bottom-anchored
    # so the newest event never leaves a misleading blank slot below it.
    install_dashboard_detector_polish(app)
    # Replace the bright native Windows scrollbars only after both scrollable Full
    # dashboard surfaces exist; behaviour remains normal wheel/drag/page scrolling.
    install_dashboard_scrollbars(app)
    install_dashboard_earnings_window(app)
    install_character_export(app)

    # TrackerEngine captured App.add_event as a bound callback during App()
    # construction. DashboardDetector wraps app.add_event later, so explicitly
    # rebind the engine callback to that wrapped method; otherwise live events
    # continue to land only in the hidden legacy Detector.
    app.engine.on_event = app.add_event

    install_dashboard_scaling(app)
    # Final release-pass chrome changes depend on the scaling controller being
    # present: restore focus after scale changes, keep combobox arrows visible,
    # clarify current-run payout gold, add region accents and tighten action groups.
    install_dashboard_final_polish(app)
    # Live build-22 feedback showed the concept icons were still a little floaty.
    # Make them span the two-line title/value block and centre live status beneath
    # the hero subtitle without changing the already-approved KPI artwork itself.
    install_dashboard_kpi_alignment(app)
    # Run Earnings is now a true fourth headline KPI; Route Base / Actual Run /
    # Route Gyms / Other Payouts live in a separate wider Run Details card.
    install_dashboard_earnings_split(app)
    # Keep the approved one-line KPI composition on wide windows, but move Run
    # Details onto a second full-width row when Full is narrowed so it never clips.
    install_dashboard_header_responsive(app)
    # Keep route/view controls together and place Export with the adjacent file/log
    # utility cluster so the action row no longer reads Button/Checkbutton/Button.
    install_dashboard_action_grouping(app)
    # Full remains resizable, with a scale-aware safe minimum. With Canvas rows,
    # vertical resize reveals more route content instead of reflowing a large child tree.
    install_dashboard_resize_smoothing(app)
    app.mainloop()
