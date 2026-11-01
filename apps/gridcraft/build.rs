//! Windows only: embed the app icon and version info (VERSIONINFO) into `omagrid.exe`, so it
//! shows in Explorer, the taskbar, the Start menu and Alt-Tab.
//!
//! On every other target this does nothing. A missing resource compiler is a warning, so a
//! cross-compile from macOS or Linux still links, unless `GRIDCRAFT_REQUIRE_WINRES=1` turns it
//! into an error (for release builds).

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=../../assets/omagrid-icon/omagrid.ico");
    println!("cargo:rerun-if-env-changed=GRIDCRAFT_REQUIRE_WINRES");
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() != Ok("windows") {
        return;
    }
    let mut res = winresource::WindowsResource::new();
    res.set_icon("../../assets/omagrid-icon/omagrid.ico")
        .set("ProductName", "OmaGrid")
        .set("FileDescription", "OmaGrid spreadsheet")
        .set("CompanyName", "OmaGrid contributors")
        .set("LegalCopyright", "Copyright (c) the GridCraft authors. MIT OR Apache-2.0.")
        .set("OriginalFilename", "omagrid.exe")
        .set("InternalName", "omagrid");
    if let Err(e) = res.compile() {
        if std::env::var_os("GRIDCRAFT_REQUIRE_WINRES").is_some() {
            eprintln!("embedding Windows resources failed: {e}");
            std::process::exit(1);
        }
        println!("cargo:warning=omagrid.exe built without icon/version resources: {e}");
    }
}
