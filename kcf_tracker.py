import cv2
import time

"""
D21X - KCF TAKİP MODÜLÜ
YOLOv8 tarafından tespit edilen hedeflerin yüksek frekansta (FPS) takibi için OpenCV KCF Tracker kullanımı.
TEKNOFEST Savaşan İHA şartnamesine uygun olarak görsel bildirimler eklenmiştir.
"""

class TargetTrackerKCF:
    def __init__(self):
        """
        KCF takipçisini ilklendirme.
        """
        self.tracker = None
        self.is_tracking = False
        self.bbox = None  # (x, y, w, h)
        self.lock_color = (0, 0, 255) # Kırmızı (#FF0000)
        self.thickness = 2
        
    def start_tracking(self, frame, bbox):
        """
        Takibi belirtilen çerçeve (bbox) ile başlatır.
        """
        try:
            self.tracker = cv2.TrackerKCF_create()
            self.is_tracking = self.tracker.init(frame, bbox)
            self.bbox = bbox
            return self.is_tracking
        except Exception as e:
            print(f"[Error] KCF Start: {str(e)}")
            return False

    def update(self, frame):
        """
        Takipçiyi günceller ve yeni konumu döndürür.
        """
        if not self.is_tracking:
            return False, None
            
        try:
            success, bbox = self.tracker.update(frame)
            if success:
                self.bbox = tuple(map(int, bbox))
                return True, self.bbox
            else:
                self.is_tracking = False
                return False, None
        except Exception as e:
            print(f"[Error] KCF Update: {str(e)}")
            self.is_tracking = False
            return False, None

    def draw(self, frame, bbox=None):
        """
        Ekrana kilitlenme dörtgenini ve ilgili bilgileri çizer.
        """
        draw_bbox = bbox if bbox else self.bbox
        if draw_bbox:
            x, y, w, h = draw_bbox
            # KCF Takip Dörtgeni (Kırmızı, 2px)
            cv2.rectangle(frame, (x, y), (x + w, y + h), self.lock_color, self.thickness)
            
            # Hedef Alanı Hesaplama (Piksel Cinsinden)
            area = w * h
            cv2.putText(frame, f"Area: {area} px", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.lock_color, 1)
            
            # Merkez Noktası
            cx, cy = x + w // 2, y + h // 2
            cv2.circle(frame, (cx, cy), 3, self.lock_color, -1)
            
        return frame

    def calculate_area(self, bbox=None):
        """
        Hedefin kapladığı alanı döndürür.
        """
        active_bbox = bbox if bbox else self.bbox
        if active_bbox:
            return active_bbox[2] * active_bbox[3]
        return 0

if __name__ == "__main__":
    # Test için dummy video akışı (veya kamera)
    cap = cv2.VideoCapture(0)
    tracker = TargetTrackerKCF()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        if not tracker.is_tracking:
            # Örnek: Manuel seçim (Gerçekte YOLO'dan gelecek)
            cv2.putText(frame, "Cizim yapmak icin 's' tusuna basin", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            if cv2.waitKey(1) & 0xFF == ord('s'):
                roi = cv2.selectROI("Tracking Test", frame, False)
                if roi[2] > 0 and roi[3] > 0:
                    tracker.start_tracking(frame, roi)
        else:
            success, bbox = tracker.update(frame)
            if success:
                tracker.draw(frame, bbox)
                
        cv2.imshow("Tracking Test", frame)
        if cv2.waitKey(1) & 0xFF == 27: # ESC to exit
            break
            
    cap.release()
    cv2.destroyAllWindows()
