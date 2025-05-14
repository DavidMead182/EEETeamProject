use std::{f32::consts::PI, fs::File, io::{stdin, stdout, Read, Write}, sync::mpsc, thread};
use std::str;


static CALIBRATION_FILE: &str = "calibration";

pub fn parse_line(file: &mut File) -> Option<(Vec<f32>, f32, f32, f32)> {
    let mut buf = [0u8; 1024];
    
    let _ = file.read(&mut buf).unwrap_or(0);
    let line = match str::from_utf8(&buf) {
        Ok(s) => s,
        Err(_) => return None,
    };

    let parts: Vec<&str> = line.trim_matches(['\0', '\n']).split(",").collect();
    if parts.len() != 13 { return None }

    let distances = parts[4..].iter().map(|s| s.parse::<f32>().unwrap_or(f32::MAX) / 1000.0).collect();
    
    let mag_x = parts[0].parse::<f32>().unwrap_or(0.0);
    let mag_y = parts[1].parse::<f32>().unwrap_or(0.0);
    let mag_z = parts[2].parse::<f32>().unwrap_or(0.0);

    Some((distances, mag_x, mag_y, mag_z))
}

pub fn reuse_calibration() -> (f32, f32, f32, f32) {
    let mut file = File::open(CALIBRATION_FILE).unwrap();
    let mut buf: Vec::<u8> = Vec::new();
    file.read_to_end(&mut buf).unwrap();

    let content = match str::from_utf8(&buf) {
        Ok(s) => s,
        Err(_) => return (0.0, 0.0, 0.0, 0.0),
    };

    let parts: Vec<f32> = content.split(" ").map(|s| {s.parse::<f32>().unwrap()}).collect();

    (parts[0], parts[1], parts[2], parts[3])
}

pub fn calibrate(file: &mut File) -> (f32, f32, f32, f32) {
    let mut readings: Vec<(Vec<f32>, f32, f32, f32)> = Vec::new();

    let (tx, rx) = mpsc::channel();

    let listener = thread::spawn(move || {
        let mut input = String::new();
        eprint!("Press enter to stop calibration: ");
        let _ = stdout().flush();
        let _ = stdin().read_line(&mut input);
        let _ = tx.send(true);
    });

    while !(rx.try_recv().unwrap_or_else(|_| false)) {
        match parse_line(file) {
            Some(r) => readings.push(r),
            None => continue,
        };
    }
    let _ = listener.join();

    // (max x, min x, max y, min y)
    let mut calibration = (f32::MIN, f32::MAX, f32::MIN, f32::MAX);
    for reading in readings {
        if reading.1 > calibration.0 { calibration.0 = reading.1 }
        if reading.1 < calibration.1 { calibration.1 = reading.1 }
        if reading.2 > calibration.2 { calibration.2 = reading.2 }
        if reading.2 < calibration.3 { calibration.3 = reading.2 }
    }

    let mut out_file = File::create(CALIBRATION_FILE).unwrap();
    out_file.write(format!("{} {} {} {}", calibration.0, calibration.1, calibration.2,
                           calibration.3).as_bytes()).unwrap();

    calibration
}

pub fn normalise_mag(reading: f32, max: f32, min: f32) -> f32 {
    (reading - min) / (max - min) - 0.5
}

pub fn calculate_heading(mag_x: f32, mag_y: f32, calibration: (f32, f32, f32, f32)) -> f32 {
    let norm_x = normalise_mag(mag_x, calibration.0, calibration.1);
    let norm_y = normalise_mag(mag_y, calibration.2, calibration.3);

    norm_y.atan2(norm_x) + PI
}
