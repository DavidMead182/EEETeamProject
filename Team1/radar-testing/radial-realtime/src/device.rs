use std::{f32::consts::PI, fs::File, io::{stdin, stdout, Read, Write}, sync::mpsc, thread};
use std::str;


static CALIBRATION_FILE: &str = "calibration";

pub fn parse_line(file: &mut File) -> Option<(Vec<f32>, Vec<f32>, f32, u32)> {
    let mut buf = [0u8; 1024];
    
    let _ = file.read(&mut buf).unwrap_or(0);
    let line = match str::from_utf8(&buf) {
        Ok(s) => s,
        Err(_) => { return None },
    };

    let parts: Vec<&str> = line.trim_matches(['\0', '\n']).split(",").collect();
    if parts.len() != 20 { return None; }

    let distances = parts[2..11].iter().map(|s| s.parse::<f32>().unwrap_or(f32::MAX) / 1000.0).collect();
    let strengths = parts[11..19].iter().map(|s| s.parse::<f32>().unwrap_or(f32::MAX) / 1000.0).collect();
    
    let heading = parts[0].parse::<f32>().unwrap_or(0.0);
    let timestamp = parts[1].parse::<u32>().unwrap_or(0);

    Some((distances, strengths, heading, timestamp))
}