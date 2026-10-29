//! Fork-safe update policy. Development builds never contact or install upstream releases.
//! Keep the existing UI command entrypoints so automation remains compatible.

use crate::SheetApp;

#[derive(Default)]
pub(crate) struct Runtime {
    manual: bool,
}

pub(crate) fn start(app: &mut SheetApp, manual: bool) {
    app.updates_rt.manual |= manual;
}

pub(crate) fn tick(app: &mut SheetApp, _ctx: &egui::Context) {
    if std::mem::take(&mut app.updates_rt.manual) {
        app.message = Some((
            "OmaGrid".into(),
            "Updates are managed by your OmaGrid installation. Automatic updates are disabled in this development build.".into(),
        ));
    }
}

pub(crate) fn show(_app: &mut SheetApp, _ctx: &egui::Context) {}

#[cfg(test)]
mod tests {
    #[test]
    fn legacy_update_commands_only_show_the_installation_policy() {
        let mut app = crate::SheetApp::new(gridcraft_engine::Session::new(), Default::default());
        let ctx = egui::Context::default();
        app.start_update_check();
        super::tick(&mut app, &ctx);
        assert!(app.message.is_none());
        assert!(app.run("app.checkForUpdates", serde_json::json!({})).is_ok());
        super::tick(&mut app, &ctx);
        let notice = app.message.take().expect("manual update policy notice");
        assert_eq!(notice.0, "OmaGrid");
        assert!(notice.1.contains("Automatic updates are disabled"));
        super::tick(&mut app, &ctx);
        assert!(app.message.is_none());
    }
}
