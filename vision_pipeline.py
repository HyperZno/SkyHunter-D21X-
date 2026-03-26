import cv2
import time
from ultralytics import YOLO
from kcf_tracker import TargetTrackerKCF
from lock_manager import LockManager
from kalman_filter import TargetKalmanFilter

"""
D21X - GÖRÜNTÜ İŞLEME PIPELINE (ENREGRASYON)
YOLOv8 ve KCF hibrit yaklaşımını uygular.
YOLO her 15 frame'de bir çalışarak doğrulama yapar, KCF her frame'de takibi sürdürür.
"""

class VisionPipeline:
    def __init__(self, model_path='yolov8n.pt'):
        # Modülleri ilklendir
        self.detector = YOLO(model_path)
        self.tracker = TargetTrackerKCF()
        self.lock_manager = LockManager()
        self.kf = TargetKalmanFilter(dt=0.03) # Yaklaşık 30 FPS için
        
        self.frame_count = 0
        self.yolo_interval = 15 # Kaç frame'de bir YOLO çalışacak
        
        self.target_locked = False
        self.current_bbox = None
        self.engagement_ready = False
        self.lock_duration = 0.0

    def process_frame(self, frame):
        """
        Görüntüyü işleyen ana pipeline döngüsü.
        """
        self.frame_count += 1
        h, w, _ = frame.shape
        
        # 1. YOLOv8 TESPİT (Sadece periyodik olarak veya takip kaybolduğunda)
        if self.frame_count % self.yolo_interval == 0 or not self.tracker.is_tracking:
            results = self.detector.predict(frame, conf=0.4, verbose=False)
            
            # En güvenilir hedefi bul (Örn: Ekran merkezine en yakın veya en büyük box)
            detections = results[0].boxes.xyxy.cpu().numpy()
            if len(detections) > 0:
                # En büyük kutuyu seç (Placeholder mantığı)
                best_box = detections[0]
                x1, y1, x2, y2 = map(int, best_box[:4])
                self.current_bbox = (x1, y1, x2 - x1, y2 - y1)
                
                # Takibi (Yeniden) Başlat
                self.tracker.start_tracking(frame, self.current_bbox)
                self.target_locked = True
            else:
                self.target_locked = False

        # 2. KCF TAKİP (Her frame'de)
        if self.tracker.is_tracking:
            success, bbox = self.tracker.update(frame)
            if success:
                self.current_bbox = bbox
                self.target_locked = True
                
                # 3. KALMAN FILTRESI GÜNCELLEME
                # Hedef merkezini al
                cx, cy = bbox[0] + bbox[2]//2, bbox[1] + bbox[3]//2
                self.kf.update([cx, cy])
            else:
                self.target_locked = False
                # Takip koptuysa Kalman tahminiyle devam et (opsiyonel)
                pred_pos = self.kf.predict()
                # predict edilen yere göre yeni bir ROI arayışı yapılabilir
        
        # 4. KİLİTLENME YÖNETİMİ
        self.engagement_ready, self.lock_duration = self.lock_manager.update(self.target_locked)
        
        # 5. GÖRSELLEŞTİRME (Pipeline düzeyi)
        if self.target_locked:
            frame = self.tracker.draw(frame, self.current_bbox)
            if self.engagement_ready:
                # Angajman Hazır Bildirimi
                cv2.putText(frame, "!!! ENGAGEMENT READY !!!", (w//2 - 150, h - 150), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)

        return frame, self.target_locked, self.engagement_ready

    def get_lock_data(self):
        return {
            "is_locked": self.target_locked,
            "duration": self.lock_duration,
            "bbox": self.current_bbox,
            "ready": self.engagement_ready
        }
