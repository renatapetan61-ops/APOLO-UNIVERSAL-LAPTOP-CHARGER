//! Rust client for the local APOLO AMIS host agent.
//! This controls software endpoints; it is not camera firmware or a hardware driver.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let agent = "http://127.0.0.1:8765";
    let discovery: serde_json::Value = ureq::get(&format!("{agent}/v1/camera")).call()?.into_json()?;
    println!("Camera discovery: {discovery:#}");
    let capture: serde_json::Value = ureq::post(&format!("{agent}/v1/camera/capture")).call()?.into_json()?;
    println!("Capture and OCR: {capture:#}");
    Ok(())
}
