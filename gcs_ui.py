import cv2
import numpy as np
import time

"""
D21X - YER İSTASYONU ARAYÜZ MODÜLÜ (GCS) - İLK VERSİYON (OpenCV)
OpenCV HighGUI tabanlı, düşük gecikmeli takip arayüzü.
"""

class GCSInterface:
    def __init__(self, window_name="D21X - AVCI IHA GCS"):
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        self.manual_override = False
        
    def _draw_hud(self, frame, telemetry, lock_info):
        """
        Heads-Up Display (HUD) katmanını frame üzerine çizer.
        """
        h, w, _ = frame.shape
        overlay = frame.copy()
        
        # Üst Panel (Siyah Şeffaf Bant)
        cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
        
        # Sunucu Saati (Milisaniye ile)
        server_time = time.strftime("%H:%M:%S", time.localtime()) + f".{int(time.time()*1000)%1000:03d}"
        cv2.putText(overlay, f"SERVER TIME: {server_time}", (20, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Mod Bilgisi
        mode_text = telemetry.get('mode', 'NA') if not self.manual_override else "MANUAL OVERRIDE"
        mode_color = (0, 255, 0) if not self.manual_override else (0, 0, 255)
        cv2.putText(overlay, f"MODE: {mode_text}", (w - 300, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        
        # Sol Alt Telemetri Paneli
        cv2.rectangle(overlay, (10, h - 150), (250, h - 10), (0, 0, 0), -1)
        telem_lines = [
            f"ALT: {telemetry.get('alt', 0):.1f} m",
            f"VX:  {telemetry.get('vx', 0):.2f} m/s",
            f"VY:  {telemetry.get('vy', 0):.2f} m/s",
            f"YAW: {telemetry.get('yaw', 0):.1f} deg"
        ]
        for i, line in enumerate(telem_lines):
            cv2.putText(overlay, line, (20, h - 120 + i*30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Sağ Alt Kilitlenme Paneli
        cv2.rectangle(overlay, (w - 260, h - 110), (w - 10, h - 10), (0, 0, 0), -1)
        lock_status = "LOCKED" if lock_info['is_locked'] else "SEARCHING"
        lock_color = (0, 0, 255) if lock_info['is_locked'] else (100, 100, 100)
        
        cv2.putText(overlay, f"STATUS: {lock_status}", (w - 250, h - 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, lock_color, 2)
        cv2.putText(overlay, f"LOCK TIME: {lock_info['duration']:.2f}s", (w - 250, h - 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Şeffaflığı Uygula
        alpha = 0.6
        return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    def show(self, frame, telemetry, lock_info):
        try:
            display_frame = self._draw_hud(frame, telemetry, lock_info)
            cv2.imshow(self.window_name, display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('m'):
                self.manual_override = not self.manual_override
            elif key == ord('q') or key == 27:
                return False
            return True
        except Exception as e:
            return False

    def close(self):
        cv2.destroyAllWindows()
