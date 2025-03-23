use rppal::gpio::{Gpio, OutputPin, InputPin, Level};
use rppal::pwm::{Pwm, Channel};
use std::time::{Duration, Instant};
use std::thread;
use std::error::Error;
use plotters::prelude::*;
use std::f64::consts::PI;

// GPIO Pin definitions
const TRIG: u8 = 23;
const ECHO: u8 = 24;
const PIR: u8 = 4;
const SERVO_PIN: u8 = 18;

fn main() -> Result<(), Box<dyn Error>> {
    // Initialize GPIO
    let gpio = Gpio::new()?;
    let mut trig_pin = gpio.get(TRIG)?.into_output();
    let echo_pin = gpio.get(ECHO)?.into_input();
    let pir_pin = gpio.get(PIR)?.into_input();
    
    // Initialize PWM for servo
    let mut servo = Pwm::with_frequency(
        Channel::Pwm0,
        50.0,
        0.0,
        rppal::pwm::Polarity::Normal,
        true,
    )?;
    
    // Run radar scan
    radar_scan(&mut trig_pin, &echo_pin, &pir_pin, &mut servo)?;
    
    Ok(())
}

fn measure_distance(trig_pin: &mut OutputPin, echo_pin: &InputPin) -> f64 {
    // Trigger pulse
    trig_pin.set_high();
    thread::sleep(Duration::from_micros(10));
    trig_pin.set_low();
    
    // Wait for echo start
    let mut start = Instant::now();
    while echo_pin.read() == Level::Low {
        start = Instant::now();
        // Add timeout check in production code
    }
    
    // Wait for echo end
    let mut end = start;
    while echo_pin.read() == Level::High {
        end = Instant::now();
        // Add timeout check in production code
    }
    
    // Calculate distance
    let duration = end.duration_since(start);
    let seconds = duration.as_secs_f64();
    seconds * 34300.0 / 2.0 // Speed of sound / 2 (roundtrip)
}

fn set_angle(servo: &mut Pwm, angle: f64) -> Result<(), Box<dyn Error>> {
    // Convert angle to duty cycle (same formula as Python version)
    let duty = 2.0 + (angle / 18.0);
    servo.set_duty_cycle(duty / 100.0)?;
    thread::sleep(Duration::from_millis(200));
    Ok(())
}

fn radar_scan(
    trig_pin: &mut OutputPin,
    echo_pin: &InputPin,
    pir_pin: &InputPin,
    servo: &mut Pwm,
) -> Result<(), Box<dyn Error>> {
    // Setup for polar plot
    let root = BitMapBackend::new("radar_scan.png", (800, 600)).into_drawing_area();
    
    // Run scan loop
    let mut angles: Vec<f64> = Vec::new();
    let mut distances: Vec<f64> = Vec::new();
    
    println!("Starting radar scan (press Ctrl+C to stop)...");
    
    loop {
        angles.clear();
        distances.clear();
        root.fill(&RGBColor(0, 69, 69))?;
        
        // Scan from 0 to 180 degrees
        for angle in (0..=180).step_by(5) {
            set_angle(servo, angle as f64)?;
            let distance = measure_distance(trig_pin, echo_pin);
            let pir_signal = pir_pin.read() == Level::High;
            
            if pir_signal {
                println!("Живой объект! Угол: {}°, Расстояние: {:.2} см", angle, distance);
                angles.push((angle as f64) * PI / 180.0); // Convert to radians
                distances.push(distance);
            }
        }
        
        // Plot the results
        let max_distance = if distances.is_empty() { 100.0 } else { 
            *distances.iter().max_by(|a, b| a.partial_cmp(b).unwrap()).unwrap() * 1.2
        };
        
        let mut chart = ChartBuilder::on(&root)
            .margin(10)
            .build_cartesian_2d(-PI..PI, 0.0..max_distance)?
            .set_polar();
            
        chart.configure_mesh().draw()?;
        
        chart.draw_series(
            angles.iter().zip(distances.iter()).map(|(&angle, &distance)| {
                Circle::new((angle, distance), 5, &RED)
            }),
        )?;
        
        root.present()?;
        thread::sleep(Duration::from_millis(10));
    }
    
    // This code would handle cleanup in a real scenario
    // (We won't reach here because of the infinite loop, but in a real app we'd catch Ctrl+C)
    // servo.set_duty_cycle(0.0)?;
    
    #[allow(unreachable_code)]
    Ok(())
}
