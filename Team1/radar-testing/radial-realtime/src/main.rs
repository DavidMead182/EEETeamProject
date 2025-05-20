use std::{collections::VecDeque, env::{self}, fs::File, marker::PhantomData, sync::mpsc::{self, Receiver}, thread};
use std::io::{stdin, stdout, Write};
use nannou::{color::{encoding, Alpha}, prelude::*};

mod device;

#[derive(Debug)]
pub struct Ping {
    pub distances: Vec<f32>,
    pub heading: f32
}

static MAX_PINGS: usize = 500;
static MAX_DIST:  usize = 7;
static ZOOM_INCREMENT: f32 = 0.5;

struct Model {
    rx: Receiver<Ping>,
    pings: VecDeque<Ping>,
    zoom: f32,
}

fn polar_to_cartesian(theta: f32, r: f32) -> Vec2 {
    vec2(theta.cos() * r, theta.sin() * r)
}

fn main() {
    let args: Vec<String> = env::args().collect();

    if File::open(args[1].as_str()).is_err() {
        eprintln!("Failed to open {}. Check that the path is correct and the device is plugged in.",
                 args[1]);
        return;
    }

    let app = nannou::app(model)
        .event(event)
        .update(update)
        .simple_window(view)
        .size(1000, 1000);

    app.run();
        
}

fn model(_app: &App) -> Model {
    let args: Vec<String> = env::args().collect();

    let fp = args[1].clone();
    let mut file = File::open(fp).unwrap();

    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        loop {
            let (distances, strengths, heading, timestamp) = match device::parse_line(&mut file) {
                Some(r) => r,
                None =>  { continue; }
            };

            // log pattern: 
            // distance0 distance1 ... distance8 strength0 strength1 ... strength8 heading timestamp
            println!("{}\t{}\t{heading}\t{timestamp}", distances.iter().map(|f| f.to_string()).collect::<Vec<String>>().join("\t"), strengths.iter().map(|f| f.to_string()).collect::<Vec<String>>().join("\t"));
            
            let ping = Ping{ distances, heading };
            if ping.heading.is_nan() { continue; }
            let _ = tx.send(ping);
        }
    });

    Model { rx, pings: VecDeque::new(), zoom: MAX_DIST as f32 + ZOOM_INCREMENT }
}

fn event(_app: &App, _model: &mut Model, _event: Event) {
    match _event {
        Event::WindowEvent{ id: _, simple } => {simple.inspect(|e| {
            match e {
                KeyPressed(k) => match k {
                    Key::Return => _model.pings.clear(),
                    Key::Up => _model.zoom -= ZOOM_INCREMENT,
                    Key::Down => _model.zoom += ZOOM_INCREMENT,
                    _ => (),    
                },
                _ => ()
            }
        }); ()},
        _ => ()
    }

    if _model.zoom < ZOOM_INCREMENT { _model.zoom = ZOOM_INCREMENT }
}

fn update(_app: &App, _model: &mut Model, _update: Update) {
    let mut ping = _model.rx.try_recv();
    
    while ping.is_ok() {
        let good_point = ping.unwrap();
        _model.pings.push_back(good_point);
        ping = _model.rx.try_recv();
        if _model.pings.len() > MAX_PINGS { _model.pings.pop_front(); }
    }
}

fn view(app: &App, _model: &Model, frame: Frame) {
    let draw = app.draw();
    let width = app.window_rect().right().min(app.window_rect().top());
    let scale = width / _model.zoom;

    draw.background().color(BLACK);

    for d in 1..=MAX_DIST {
        draw.ellipse().no_fill().radius((d as f32) * scale).stroke(WHITE).stroke_weight(1.0);
        draw.text(d.to_string().as_str()).color(WHITE).x((d as f32) * scale + 10.0);
    }

    for d in 1..=(MAX_DIST*2) {
        draw.ellipse().no_fill().radius((d as f32) * 0.5 * scale).stroke(GREY).stroke_weight(0.5);
    }

    if !_model.pings.is_empty() {
        let alpha_scale = 1.0 / _model.pings.len() as f32;
        let mut points = Vec::new();

        for (i, pv) in _model.pings.iter().enumerate() {
            for d in &pv.distances {
                let v = polar_to_cartesian(pv.heading, *d) * scale;
                points.push((vec2(v.x, v.y), Alpha { color: Rgb { red: alpha_scale * i as f32, blue: alpha_scale
                    * (_model.pings.len() - i) as f32, green: 0.0, standard:
                   PhantomData::<encoding::Srgb> }, alpha: alpha_scale * i as f32 }));
            }
        }
        
        if points.len() != 0 {
            draw.point_mode().polyline().points_colored(points);
        }
    }

    _model.pings.iter().last().inspect(|ping| {
        draw.arrow().color(BLUE)
            .start(vec2(0.0, 0.0))
            .end(polar_to_cartesian(ping.heading, width))
            .head_length(7.0)
            .head_width(7.0);
    });


    draw.to_frame(app, &frame).unwrap();
}