#[cfg(not(target_arch = "wasm32"))]
use super::updates_ui;
use super::{SheetApp, desktop_theme};
use crate::{omarchy, theme};

impl SheetApp {
    /// Follow the desktop's light/dark choice while the app runs (Linux; the desktop app calls
    /// this once — tests and embedders don't start the watcher thread).
    pub fn watch_desktop_theme(&mut self) {
        self.desktop_theme = desktop_theme::DesktopTheme::start();
        self.omarchy = omarchy::Watcher::start();
    }

    /// Poll only cached worker state. Manual Light/Dark keeps the original palette and fonts.
    pub(super) fn sync_omarchy(&mut self, ctx: &egui::Context) {
        self.omarchy_snapshot = self.omarchy.current(ctx);
        let palette = self.ui.system_theme.then_some(self.omarchy_snapshot.palette).flatten();
        theme::set_omarchy_palette(ctx, palette);
        let fonts = palette.and(self.omarchy_snapshot.fonts.clone());
        // egui activates a font set on the next pass. Only spend that blank paint gate on an
        // idle frame: physical text/IME, paste, held drags and active editors must not lose input.
        if self.chrome_font_reload_is_idle(ctx) && theme::refresh_omarchy_fonts(ctx, fonts) {
            self.fonts_rebind = true;
            ctx.request_repaint();
        }
    }

    fn chrome_font_reload_is_idle(&self, ctx: &egui::Context) -> bool {
        self.fonts_ready
            && !self.fonts_rebind
            && !self.synthetic_pending
            && self.synthetic.is_empty()
            && self.editor.is_none()
            && self.text_box_editor.is_none()
            && self.name_box.is_none()
            && self.dialog.is_none()
            && !ctx.text_edit_focused()
            && ctx.input(|input| input.events.is_empty() && !input.pointer.any_down())
    }

    /// Follows the desktop/system theme preference and records the effective theme.
    pub(super) fn sync_theme_preference(&mut self, ctx: &egui::Context) {
        let preference = match (
            self.ui.system_theme,
            self.omarchy_snapshot
                .palette
                .map(|p| if p.dark { egui::Theme::Dark } else { egui::Theme::Light })
                .or_else(|| ctx.system_theme())
                .or_else(|| self.desktop_dark.map(|d| if d { egui::Theme::Dark } else { egui::Theme::Light })),
        ) {
            (true, Some(egui::Theme::Dark)) => egui::ThemePreference::Dark,
            (true, Some(egui::Theme::Light)) => egui::ThemePreference::Light,
            _ => self.ui.theme_preference(),
        };
        if ctx.options(|o| o.theme_preference) != preference {
            ctx.set_theme(preference);
            ctx.request_repaint();
        }
        self.effective_dark = ctx.theme() == egui::Theme::Dark;
    }

    /// Keeps egui's own keyboard zoom and quit shortcuts off and applies GridCraft's zoom factor.
    pub(super) fn sync_input_options(&mut self, ctx: &egui::Context) {
        // Interface size: the preference owns the zoom factor, so egui's own Ctrl/Cmd +/-/0 zoom
        // keys stay off (they would also swallow GridCraft's shortcuts).
        if ctx.options(|o| o.zoom_with_keyboard) {
            ctx.options_mut(|o| o.zoom_with_keyboard = false);
        }
        // egui closes the window on Ctrl+Q (and with Shift or Alt held too) without asking to save
        // (#1443). Excel for Windows has no such key (Ctrl+Q is Quick Analysis). With a native
        // window per workbook egui's Cmd+Q would close only the window it was typed in: the menu
        // bar's Quit item has the key instead (it asks about unsaved workbooks first).
        if (ctx.os() != egui::os::OperatingSystem::Mac || self.native_windows) && ctx.options(|o| !o.quit_shortcuts.is_empty()) {
            ctx.options_mut(|o| o.quit_shortcuts.clear());
        }
        let zoom = self.ui.zoom_factor();
        if (ctx.zoom_factor() - zoom).abs() > 0.001 {
            ctx.set_zoom_factor(zoom);
            ctx.request_repaint();
        }
    }

    /// Compatibility entry point; OmaGrid updates are installation-managed, so this is a no-op.
    pub fn start_update_check(&mut self) {
        #[cfg(not(target_arch = "wasm32"))]
        updates_ui::start(self, false);
    }

    /// Help ▸ Check for Updates… explains installation-managed updates without making a network request.
    pub fn check_for_updates(&mut self) {
        #[cfg(not(target_arch = "wasm32"))]
        updates_ui::start(self, true);
        #[cfg(target_arch = "wasm32")]
        {
            self.message = Some(("OmaGrid".into(), "Updates are managed by your OmaGrid installation.".into()));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn physical_text_is_not_lost_when_a_chrome_font_refresh_is_pending() {
        let _guard = crate::fonts::TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        let ctx = egui::Context::default();
        let base = theme::pinned_font_definitions();
        let data = base.font_data.values().next().unwrap();
        let face = omarchy::FontFace { bytes: std::sync::Arc::new(data.bytes().to_vec()), index: data.index };
        ctx.set_fonts(theme::with_omarchy_fonts(&ctx, base));
        assert!(theme::refresh_omarchy_fonts(&ctx, Some((face.clone(), face))));
        let mut session = gridcraft_engine::Session::new();
        session.new_workbook();
        let mut app = SheetApp::new(session, crate::Services::default());
        app.use_prepared_fonts();
        let bound = app.fonts_bound.clone();
        let seen = app.fonts_seen;
        // The inactive watcher requests removal of that font override on the same frame the
        // physical keyboard starts editing. Neither the paint gate nor the event may be lost.
        let raw = egui::RawInput {
            screen_rect: Some(egui::Rect::from_min_size(egui::Pos2::ZERO, egui::vec2(1100.0, 800.0))),
            events: vec![egui::Event::Text("hello".into())],
            ..Default::default()
        };
        let mut out = ctx.run_ui(raw, |ui| {
            app.logic(ui.ctx());
            assert!(app.fonts_ready);
            assert!(!app.fonts_rebind);
            app.ui(ui);
        });
        out.textures_delta.clear();
        assert_eq!(app.editor.as_ref().map(|ed| ed.text.as_str()), Some("hello"));
        assert_eq!(app.fonts_bound, bound);
        assert_eq!(app.fonts_seen, seen);
    }

    #[test]
    fn chrome_font_reload_waits_for_physical_input_and_an_idle_editor() {
        let ctx = egui::Context::default();
        let mut app = SheetApp::new(gridcraft_engine::Session::new(), crate::Services::default());
        app.use_prepared_fonts();
        for event in [
            egui::Event::Text("x".into()),
            egui::Event::Paste("pasted".into()),
            egui::Event::Ime(egui::ImeEvent::Commit("文".into())),
            egui::Event::Key { key: egui::Key::Enter, physical_key: None, pressed: true, repeat: false, modifiers: egui::Modifiers::NONE },
        ] {
            let mut out = ctx.run_ui(egui::RawInput { events: vec![event], ..Default::default() }, |ui| {
                assert!(!app.chrome_font_reload_is_idle(ui.ctx()));
            });
            out.textures_delta.clear();
        }
        let mut out = ctx.run_ui(egui::RawInput::default(), |ui| {
            assert!(app.chrome_font_reload_is_idle(ui.ctx()));
            app.fonts_rebind = true;
            assert!(!app.chrome_font_reload_is_idle(ui.ctx()));
        });
        out.textures_delta.clear();
    }

    #[test]
    fn manual_modes_ignore_the_cached_omarchy_palette_and_system_restores_it() {
        let ctx = egui::Context::default();
        let palette = omarchy::Palette::parse("background='#101020'\nforeground='#eeeeff'\nmode='dark'", false).unwrap();
        let mut app = SheetApp::new(gridcraft_engine::Session::new(), crate::Services::default());
        app.omarchy = omarchy::Watcher::fixed(palette);
        for (system, dark) in [(true, false), (false, false), (false, true), (true, false)] {
            app.ui.system_theme = system;
            app.ui.dark = dark;
            app.sync_omarchy(&ctx);
            app.sync_theme_preference(&ctx);
            let tokens = theme::Tokens::get(&ctx);
            if system {
                assert_eq!(tokens.window, palette.background);
                assert_eq!(tokens.dark, palette.dark);
            } else {
                assert_eq!(tokens, if dark { theme::Tokens::dark() } else { theme::Tokens::light() });
            }
        }
    }
}
