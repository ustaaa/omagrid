//! Appearance is transient chrome: preserve document rendering roles and command semantics.
use egui::os::OperatingSystem;
use gridcraft_engine::Session;
use gridcraft_ui_egui::{Services, SheetApp, omarchy::Palette, theme};
use serde_json::{Value, json};

const DARK: &str = "background='#18202a'\nforeground='#edf2f7'\naccent='#79b8ff'\nmode='dark'";
const LIGHT: &str = "background='#f2efe8'\nforeground='#24282d'\naccent='#305c9e'\nmode='light'";

#[test]
fn chrome_palette_preserves_sheet_ink_and_removal_restores_all_tokens() {
    for text in [DARK, LIGHT] {
        let palette = Palette::parse(text, false).unwrap();
        let ctx = egui::Context::default();
        theme::apply(&ctx, palette.dark);
        let original = theme::Tokens::get(&ctx);
        theme::set_omarchy_palette(&ctx, Some(palette));
        let themed = theme::Tokens::get(&ctx);
        assert_eq!(themed.window, palette.background);
        assert_ne!(themed.window, original.window);
        assert_eq!(ctx.global_style().visuals.panel_fill, themed.window);
        assert_eq!(themed.grid_bg, original.grid_bg);
        assert_eq!(themed.cell_text, original.cell_text);
        assert_eq!(themed.sheet_ref_colors, original.sheet_ref_colors);
        assert_eq!(themed.sheet_control_bg, original.sheet_control_bg);
        assert_eq!(themed.sheet_control_border, original.sheet_control_border);
        assert_eq!(themed.sheet_control_text, original.sheet_control_text);
        assert_eq!(themed.sheet_track, original.sheet_track);
        assert!(theme::contrast(themed.text, themed.menu_bg) >= 4.5);
        assert!(theme::contrast(themed.sel_border, themed.grid_bg) >= 3.0);
        theme::set_omarchy_palette(&ctx, None);
        assert_eq!(theme::Tokens::get(&ctx), original);
    }
}

type Harness = egui_kittest::Harness<'static, SheetApp>;

fn harness(os: OperatingSystem, palette: Option<Palette>) -> Harness {
    let mut session = Session::new();
    session.new_workbook();
    let mut app = SheetApp::new(session, Services::default());
    app.use_prepared_fonts();
    egui_kittest::Harness::builder()
        .with_os(os)
        .with_size(egui::vec2(1200.0, 800.0))
        .with_context_setup(|ctx| {
            ctx.set_fonts(theme::pinned_font_definitions());
            theme::apply(ctx, false);
        })
        .build_ui_state(
            move |ui, app: &mut SheetApp| {
                let ctx = ui.ctx().clone();
                app.logic(&ctx);
                // Replace the production filesystem watcher with deterministic test data.
                theme::set_omarchy_palette(&ctx, palette);
                app.ui(ui);
            },
            app,
        )
}

fn inspect(app: &mut SheetApp) -> Value {
    json!({
        "document": app.run("document.inspect", json!({})).unwrap(),
        "values": app.run("sheet.read", json!({"range": "A1:C2"})).unwrap(),
        "formula": app.run("cell.get", json!({"cell": "C1"})).unwrap(),
        "history": app.run("history.list", json!({})).unwrap(),
    })
}

#[test]
fn rendered_appearance_keeps_edit_format_undo_and_ribbon_commands_equivalent() {
    for os in [OperatingSystem::Nix, OperatingSystem::Windows] {
        for palette in [DARK, LIGHT] {
            let mut plain = harness(os, None);
            let mut themed = harness(os, Palette::parse(palette, false));
            for (id, params) in [
                ("range.setValues", json!({"range": "A1", "values": [[2, 3], [4, 5]]})),
                ("cell.set", json!({"cell": "C1", "input": "=SUM(A1:B2)"})),
                ("home.bold", json!({"range": "C1", "on": true})),
                ("view.freezePanes", json!({"cell": "B2"})),
                ("ui.ribbonTab", json!({"tab": "View"})),
                ("cell.set", json!({"cell": "A1", "input": "10"})),
                ("edit.undo", json!({})),
                ("edit.redo", json!({})),
            ] {
                let a = plain.state_mut().run(id, params.clone()).unwrap();
                let b = themed.state_mut().run(id, params).unwrap();
                assert_eq!(a, b, "command {id}");
                plain.run_steps(2);
                themed.run_steps(2);
                assert_eq!(inspect(plain.state_mut()), inspect(themed.state_mut()), "after {id}");
                assert_eq!(plain.state().ui.ribbon_tab, themed.state().ui.ribbon_tab);
            }
            let values = themed.state_mut().run("sheet.read", json!({"range": "C1"})).unwrap();
            assert_eq!(values["values"], json!([[22.0]]));
        }
    }
}
