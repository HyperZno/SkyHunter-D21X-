from pymavlink import mavutil
import time
import threading

"""
D21X - MAVLINK HABERLEŞME MODÜLÜ
Drone ile yer istasyonu/companion computer arasındaki iletişimi yönetir.
Telemetri okuma ve NED (North-East-Down) hız komutları gönderme yeteneklerine sahiptir.
"""

class DroneCommunicator:
    def __init__(self, connection_string='udp:127.0.0.1:14550'):
        """
        Drone ile bağlantı kurar. 
        Varsayılan: Simülasyon (SITL) için UDP:14550
        """
        self.master = None
        self.connection_string = connection_string
        self.telemetry = {
            "lat": 0.0, "lon": 0.0, "alt": 0.0,
            "roll": 0.0, "pitch": 0.0, "yaw": 0.0,
            "vx": 0.0, "vy": 0.0, "vz": 0.0,
            "heading": 0,
            "battery": 0, # Yüzde
            "gps_satellites": 0,
            "gps_fix": 0, # 3 = 3D Fix
            "mode": "UNKNOWN"
        }
        self.is_connected = False
        self.manual_override = False
        
        # Arka planda telemetri okuma thread'i
        self.telemetry_thread = threading.Thread(target=self._update_telemetry, daemon=True)

    def connect(self):
        """Bağlantıyı başlatır."""
        try:
            print(f"[MAVLink] Baglanti kuruluyor: {self.connection_string}")
            self.master = mavutil.mavlink_connection(self.connection_string)
            self.master.wait_heartbeat()
            print("[MAVLink] Heartbeat alindi, baglanti basarili.")
            self.is_connected = True
            self.telemetry_thread.start()
            return True
        except Exception as e:
            print(f"[MAVLink] Baglanti hatasi: {str(e)}")
            return False

    def _update_telemetry(self):
        """Sürekli telemetri verisi çeker."""
        while self.is_connected:
            try:
                # GLOBAL_POSITION_INT, ATTITUDE, SYS_STATUS, HEARTBEAT mesajlarını bekle
                msg = self.master.recv_match(type=['GLOBAL_POSITION_INT', 'ATTITUDE', 'SYS_STATUS', 'GPS_RAW_INT', 'HEARTBEAT'], blocking=True, timeout=1.0)
                if not msg: continue
                
                msg_type = msg.get_type()
                if msg_type == 'GLOBAL_POSITION_INT':
                    self.telemetry["lat"] = msg.lat / 1e7
                    self.telemetry["lon"] = msg.lon / 1e7
                    self.telemetry["alt"] = msg.relative_alt / 1000.0 # Metre
                    self.telemetry["vx"] = msg.vx / 100.0
                    self.telemetry["vy"] = msg.vy / 100.0
                    self.telemetry["vz"] = msg.vz / 100.0
                elif msg_type == 'ATTITUDE':
                    self.telemetry["roll"] = msg.roll
                    self.telemetry["pitch"] = msg.pitch
                    self.telemetry["yaw"] = msg.yaw
                elif msg_type == 'SYS_STATUS':
                    self.telemetry["battery"] = msg.battery_remaining # 0-100
                elif msg_type == 'GPS_RAW_INT':
                    self.telemetry["gps_satellites"] = msg.satellites_visible
                    self.telemetry["gps_fix"] = msg.fix_type # 3 = 3D Fix
                elif msg_type == 'HEARTBEAT':
                    # Uçuş modunu al
                    self.telemetry["mode"] = mavutil.mode_string_v10(msg)
                    
            except Exception as e:
                print(f"[MAVLink] Veri okuma hatasi: {str(e)}")
                time.sleep(1)

    def send_velocity_cmd(self, vx, vy, vz, yaw_rate=0):
        """
        Drone'a SET_POSITION_TARGET_LOCAL_NED mesajı ile hız komutu gönderir.
        """
        if not self.is_connected or self.manual_override:
            return

        try:
            self.master.mav.set_position_target_local_ned_send(
                0, # Zaman damgası
                self.master.target_system, self.master.target_component,
                mavutil.mavlink.MAV_FRAME_BODY_NED, # İHA gövde koordinat sistemi
                0b0000111111000111, # Sadece hızları kullanacağımızı belirten maske
                0, 0, 0, # Pozisyon (Boş)
                vx, vy, vz, # Hedef hızlar (m/s)
                0, 0, 0, # İvme (Boş)
                0, yaw_rate # Hedef Yaw (Radyan)
            )
        except Exception as e:
            print(f"[MAVLink] Hiz komutu hatasi: {str(e)}")

    def set_mode(self, mode):
        """Uçuş modunu değiştirir (GUIDED, AUTO, LOITER vb.)"""
        mode_id = self.master.mode_mapping()[mode]
        self.master.mav.set_mode_send(
            self.master.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )

if __name__ == "__main__":
    # Test
    drone = DroneCommunicator()
    if drone.connect():
        print(f"Konum: {drone.telemetry['lat']}, {drone.telemetry['lon']}")
        time.sleep(2)
        print("Test amacli GUIDED moduna geciliyor...")
        drone.set_mode('GUIDED')
        time.sleep(1)
        # Sağa doğru 1m/s hız komutu
        print("Hiz komutu gonderiliyor...")
        drone.send_velocity_cmd(0, 1.0, 0)
        time.sleep(3)
        # Durdur
        drone.send_velocity_cmd(0, 0, 0)
        print("Test bitti.")
