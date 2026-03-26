import cv2
import threading
import time
from vision_pipeline import VisionPipeline
from mavlink_comm import DroneCommunicator
from gcs_ui import GCSInterface

"""
D21X - ANA PROGRAM (MAIN.PY) - İLK VERSİYON (OpenCV Loop)
"""

class D21XSystem:
    def __init__(self, video_src=0, connection_str='udp:127.0.0.1:14550'):
        # Alt Sistemler
        self.vision = VisionPipeline()
        self.drone = DroneCommunicator(connection_str)
        self.ui = GCSInterface()
        
        # Video
        self.cap = cv2.VideoCapture(video_src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Video Kaydı
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter('mission_log.mp4', fourcc, 20.0, (640, 480))
        
        self.running = False

    def start(self):
        print("[System] D21X Baslatiliyor...")
        if not self.drone.connect():
            print("[Warning] Drone baglantisi kurulamadi.")
            
        self.running = True
        self.run_loop()

    def run_loop(self):
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret: break
                
                # 1. Görüntü İşleme
                processed_frame, is_locked, ready_to_fire = self.vision.process_frame(frame)
                
                # 2. Otonom Komutlar
                if is_locked and not self.ui.manual_override:
                    lock_data = self.vision.get_lock_data()
                    bbox = lock_data['bbox']
                    target_x = bbox[0] + bbox[2]//2
                    target_y = bbox[1] + bbox[3]//2
                    err_x = (target_x - 320) / 320.0
                    err_y = (target_y - 240) / 240.0
                    self.drone.send_velocity_cmd(0, err_x * 2.0, err_y * 1.5)
                
                # 3. UI Güncelleme
                lock_info = self.vision.get_lock_data()
                if not self.ui.show(processed_frame, self.drone.telemetry, lock_info):
                    self.running = False
                
                # 4. Kayıt
                self.out.write(processed_frame)

        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        self.running = False
        self.cap.release()
        self.out.release()
        self.ui.close()

if __name__ == "__main__":
    d21x = D21XSystem(video_src=0)
    d21x.start()
