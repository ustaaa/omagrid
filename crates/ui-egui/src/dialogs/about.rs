use super::Dialog;

/// Help ▸ About GridCraft: the app, its contributors and the AI models that helped. The credits
/// are compiled in (`crate::credits`, docs/contributors.md).
pub(super) fn about(ui: &mut egui::Ui, d: &mut Dialog) {
    ui.horizontal(|ui| {
        for tab in ["About", "Contributors", "Models"] {
            if ui.selectable_label(d.tab == tab, tab).clicked() {
                d.tab = tab.to_string();
            }
        }
    });
    ui.separator();
    match d.tab.as_str() {
        "Contributors" => crate::credits::contributors_ui(ui),
        "Models" => crate::credits::models_ui(ui),
        _ => {
            ui.heading("OmaGrid");
            ui.label(format!(
                "Version {} • based on GridCraft v{} (43284377)",
                include_str!("../../../oma-version.txt").trim_ascii(),
                env!("CARGO_PKG_VERSION")
            ));
            ui.add_space(4.0);
            ui.label("A native spreadsheet for Omarchy and Linux. An independent fork of GridCraft.");
            ui.hyperlink_to("OmaGrid source", "https://github.com/ustaaa/omagrid");
            ui.hyperlink_to("Upstream GridCraft and contributors", "https://github.com/storytold/gridcraft");
            ui.label("MIT OR Apache-2.0. Upstream copyright and contributor credits are preserved.");
        }
    }
}
