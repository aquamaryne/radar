#include <iostream>
#include <fstream>
#include <cmath>
#include <vector>
#include <chrono>
#include <thread>
#include <wiringPi.h>
#include <softPwm.h>
#include <unistd.h>
#include <cstdlib>
#include <string>

// Constants for GPIO pins
#define TRIG 23
#define ECHO 24
#define PIR 4
#define SERVO_PIN 18

// Function prototypes
double measureDistance();
void setAngle(int angle);
void radarScan();
void saveDataForPlotting(const std::vector<int>& angles, const std::vector<double>& distances);

int main() {
    // Initialize wiringPi
    if (wiringPiSetupGpio() == -1) {
        std::cerr << "Failed to initialize wiringPi." << std::endl;
        return 1;
    }

    // Setup GPIO pins
    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);
    pinMode(PIR, INPUT);
    
    // Initialize servo using softPwm
    softPwmCreate(SERVO_PIN, 0, 200);
    
    std::cout << "Starting radar system..." << std::endl;
    radarScan();
    
    return 0;
}

// Measure distance using ultrasonic sensor
double measureDistance() {
    // Send trigger pulse
    digitalWrite(TRIG, HIGH);
    usleep(10); // 10 microseconds
    digitalWrite(TRIG, LOW);
    
    // Wait for echo to start
    auto startTime = std::chrono::high_resolution_clock::now();
    auto endTime = startTime;
    
    // Wait for echo pin to go HIGH (pulse start)
    while (digitalRead(ECHO) == LOW) {
        startTime = std::chrono::high_resolution_clock::now();
        // Add timeout to prevent infinite loop
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::high_resolution_clock::now() - endTime).count();
        if (duration > 100) return -1; // Timeout after 100ms
    }
    
    // Wait for echo pin to go LOW (pulse end)
    while (digitalRead(ECHO) == HIGH) {
        endTime = std::chrono::high_resolution_clock::now();
        // Add timeout to prevent infinite loop
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::high_resolution_clock::now() - startTime).count();
        if (duration > 100) return -1; // Timeout after 100ms
    }
    
    // Calculate duration in seconds
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
        endTime - startTime).count() / 1000000.0;
    
    // Calculate distance (speed of sound = 34300 cm/s, divide by 2 for two-way trip)
    return duration * 34300.0 / 2.0;
}

// Set servo angle
void setAngle(int angle) {
    // Convert angle to pulse width
    // Map 0-180 degrees to 5-25 (0.5ms to 2.5ms pulse width)
    int pulseWidth = 5 + (angle * 20) / 180;
    softPwmWrite(SERVO_PIN, pulseWidth);
    
    // Give servo time to move
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
}

// Main radar scanning function
void radarScan() {
    std::vector<int> angles;
    std::vector<double> distances;
    
    try {
        while (true) {
            angles.clear();
            distances.clear();
            
            // Scan from 0 to 180 degrees
            for (int angle = 0; angle <= 180; angle += 5) {
                setAngle(angle);
                double distance = measureDistance();
                bool pirSignal = digitalRead(PIR);
                
                if (pirSignal) {
                    std::cout << "Live object! Angle: " << angle 
                              << "°, Distance: " << distance << " cm" << std::endl;
                    angles.push_back(angle);
                    distances.push_back(distance);
                }
            }
            
            // Save data for external plotting
            saveDataForPlotting(angles, distances);
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
    
    // Cleanup
    std::cout << "Shutting down radar..." << std::endl;
    softPwmStop(SERVO_PIN);
}

// Save radar data to file for external plotting
void saveDataForPlotting(const std::vector<int>& angles, const std::vector<double>& distances) {
    std::ofstream dataFile("radar_data.txt");
    if (dataFile.is_open()) {
        dataFile << "Angle,Distance\n";
        for (size_t i = 0; i < angles.size(); ++i) {
            dataFile << angles[i] << "," << distances[i] << "\n";
        }
        dataFile.close();
        std::cout << "Data saved for plotting" << std::endl;
        
        // Generate plotting script
        std::ofstream scriptFile("plot_radar.py");
        if (scriptFile.is_open()) {
            scriptFile << "import numpy as np\n";
            scriptFile << "import matplotlib.pyplot as plt\n";
            scriptFile << "import pandas as pd\n\n";
            scriptFile << "data = pd.read_csv('radar_data.txt')\n";
            scriptFile << "angles = np.radians(data['Angle'])\n";
            scriptFile << "distances = data['Distance']\n\n";
            scriptFile << "fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})\n";
            scriptFile << "ax.set_theta_zero_location('N')\n";
            scriptFile << "ax.set_theta_direction(-1)\n";
            scriptFile << "ax.set_thetamin(0)\n";
            scriptFile << "ax.set_thetamax(180)\n";
            scriptFile << "ax.scatter(angles, distances, color='red', s=30)\n";
            scriptFile << "ax.set_facecolor('#004545')\n";
            scriptFile << "plt.savefig('radar_plot.png')\n";
            scriptFile << "plt.show()\n";
            scriptFile.close();
            
            // Attempt to run the plot script
            system("python3 plot_radar.py &");
        }
    } else {
        std::cerr << "Unable to open file for data saving" << std::endl;
    }
}
