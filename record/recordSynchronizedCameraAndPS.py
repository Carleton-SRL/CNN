import dv_processing as dv
import argparse
import socket
import struct
import time
import numpy as np
import threading
import csv
import os
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='Record synchronized data from camera and UDP stream.')
    parser.add_argument("-c",
                        "--camera_name",
                        dest='camera_name',
                        default="",
                        type=str,
                        help="Camera name (e.g. DVXplorer_DXA00093).")
    parser.add_argument("-o",
                        "--output_path",
                        dest='output_path',
                        type=str,
                        required=True,
                        help="Path to output directory (will save .aedat4 and .csv files).")
    parser.add_argument("-p",
                        "--port",
                        dest='port',
                        type=int,
                        default=31534,
                        help="UDP port to listen on (default: 31534)")
    parser.add_argument("--trigger-channel",
                        dest='trigger_channel',
                        type=int,
                        default=0,
                        help="Trigger channel to use for synchronization markers (default: 0)")
    return parser.parse_args()

class UdpReceiver:
    def __init__(self, port):
        self.port = port
        self.running = False
        self.sock = None
        self.latest_data = None
        self.data_lock = threading.Lock()
        self.callbacks = []
        
    def start(self):
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.settimeout(0.1)  # Set a timeout for non-blocking operation
        
        # Start receiving thread
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        print(f"UDP receiver started on port {self.port}")
        
    def add_callback(self, callback):
        """Add a callback function that will be called when new data arrives"""
        self.callbacks.append(callback)
        
    def _receive_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)  # Buffer size is 1024 bytes
                
                # Parse 19 double values from binary data
                if len(data) == 19 * 8:  # 19 doubles * 8 bytes
                    values = struct.unpack('19d', data)
                    
                    # Get current system time in microseconds for precise synchronization
                    current_time_us = int(time.time() * 1000000)
                    
                    packet_data = {
                        'system_time_us': current_time_us,
                        'phasespace_time': values[0],
                        'red_pose': values[1:4],      # x, y, angle
                        'black_pose': values[4:7],    # x, y, angle
                        'blue_pose': values[7:10],    # x, y, angle
                        'red_vel': values[10:13],     # vx, vy, vangle
                        'black_vel': values[13:16],   # vx, vy, vangle
                        'blue_vel': values[16:19]     # vx, vy, vangle
                    }
                    
                    with self.data_lock:
                        self.latest_data = packet_data
                    
                    # Call all registered callbacks with the new data
                    for callback in self.callbacks:
                        callback(packet_data)
                        
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error receiving UDP data: {e}")
                
    def get_latest_data(self):
        with self.data_lock:
            return self.latest_data
            
    def stop(self):
        self.running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)
        if self.sock:
            self.sock.close()

class CsvLogger:
    def __init__(self, filename):
        self.filename = filename
        self.file = None
        self.writer = None
        
    def open(self):
        # Create file and write header
        self.file = open(self.filename, 'w', newline='')
        fieldnames = [
            'system_time_us', 'phasespace_time', 
            'red_x', 'red_y', 'red_angle', 
            'black_x', 'black_y', 'black_angle',
            'blue_x', 'blue_y', 'blue_angle',
            'red_vx', 'red_vy', 'red_vangle',
            'black_vx', 'black_vy', 'black_vangle',
            'blue_vx', 'blue_vy', 'blue_vangle'
        ]
        self.writer = csv.DictWriter(self.file, fieldnames=fieldnames)
        self.writer.writeheader()
        
    def log_data(self, data):
        """Log UDP data to CSV file"""
        if self.writer:
            self.writer.writerow({
                'system_time_us': data['system_time_us'],
                'phasespace_time': data['phasespace_time'],
                'red_x': data['red_pose'][0],
                'red_y': data['red_pose'][1],
                'red_angle': data['red_pose'][2],
                'black_x': data['black_pose'][0],
                'black_y': data['black_pose'][1],
                'black_angle': data['black_pose'][2],
                'blue_x': data['blue_pose'][0],
                'blue_y': data['blue_pose'][1],
                'blue_angle': data['blue_pose'][2],
                'red_vx': data['red_vel'][0],
                'red_vy': data['red_vel'][1],
                'red_vangle': data['red_vel'][2],
                'black_vx': data['black_vel'][0],
                'black_vy': data['black_vel'][1],
                'black_vangle': data['black_vel'][2],
                'blue_vx': data['blue_vel'][0],
                'blue_vy': data['blue_vel'][1],
                'blue_vangle': data['blue_vel'][2]
            })
            self.file.flush()  # Make sure data is written to disk
            
    def close(self):
        if self.file:
            self.file.close()

def main():
    args = parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_path, exist_ok=True)
    
    # Generate filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    aedat_filename = os.path.join(args.output_path, f"recording_{timestamp}.aedat4")
    csv_filename = os.path.join(args.output_path, f"tracker_data_{timestamp}.csv")
    
    print(f"Recording event data to: {aedat_filename}")
    print(f"Recording tracker data to: {csv_filename}")
    
    # Initialize UDP receiver
    udp_receiver = UdpReceiver(args.port)
    
    # Initialize CSV logger
    csv_logger = CsvLogger(csv_filename)
    csv_logger.open()
    
    # Register callback to log UDP data
    udp_receiver.add_callback(csv_logger.log_data)
    
    try:
        # Open camera
        camera = dv.io.CameraCapture(args.camera_name)
        
        # Check available streams
        eventsAvailable = camera.isEventStreamAvailable()
        framesAvailable = camera.isFrameStreamAvailable()
        imuAvailable = camera.isImuStreamAvailable()
        triggersAvailable = camera.isTriggerStreamAvailable()
        
        # Open file writer
        writer = dv.io.MonoCameraWriter(aedat_filename, camera)
        
        # Create synthetic trigger generator
        triggerGenerator = None
        if triggersAvailable:
            # Create a trigger generator if the camera supports triggers
            triggerGenerator = dv.processing.TriggerGenerator()
            
            # Define callback for UDP data to generate trigger
            def generate_trigger(data):
                if triggerGenerator:
                    # Create a trigger event at the current timestamp
                    timestamp = data['system_time_us']
                    # Use a specific channel for synchronization markers
                    trigger = dv.processing.Trigger(timestamp, args.trigger_channel, True)
                    writer.writeTriggerPacket([trigger], streamName='triggers')
                    
            # Register callback to generate trigger on UDP data arrival
            udp_receiver.add_callback(generate_trigger)
        
        # Start UDP receiver
        udp_receiver.start()
        
        print("Start recording")
        
        # Main recording loop
        while camera.isConnected():
            if eventsAvailable:
                # Get and write events
                events = camera.getNextEventBatch()
                if events is not None:
                    writer.writeEvents(events, streamName='events')

            if framesAvailable:
                # Get and write frame
                frame = camera.getNextFrame()
                if frame is not None:
                    writer.writeFrame(frame, streamName='frames')

            if imuAvailable:
                # Get and write IMU data
                imus = camera.getNextImuBatch()
                if imus is not None:
                    writer.writeImuPacket(imus, streamName='imu')

            if triggersAvailable:
                # Get and write camera triggers (not our synthetic ones)
                triggers = camera.getNextTriggerBatch()
                if triggers is not None:
                    writer.writeTriggerPacket(triggers, streamName='triggers')
                    
            # Small delay to prevent CPU hogging
            time.sleep(0.001)
                
    except KeyboardInterrupt:
        print("Ending recording")
    except Exception as e:
        print(f"Error during recording: {e}")
    finally:
        # Cleanup
        udp_receiver.stop()
        csv_logger.close()
        print("Recording complete")

if __name__ == "__main__":
    main()