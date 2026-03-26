import time
from collections import deque

"""
D21X - KİLİTLENME SÜRESİ YÖNETİCİSİ
TEKNOFEST Savaşan İHA kuralları: 10 saniyelik pencerede toplam 5 saniye kilitlenme.
Bu modül kilitlenme durumunu takip eder ve angajman (ateşleme/atış) kararını üretir.
"""

class LockManager:
    def __init__(self, window_size=10.0, target_lock_time=5.0):
        """
        window_size: Değerlendirme penceresi (saniye)
        target_lock_time: Atış için gereken toplam kilit süresi (saniye)
        """
        self.window_size = window_size
        self.target_lock_time = target_lock_time
        
        # Kilitlenme geçmişini tutan kuyruk (timestamp, is_locked)
        self.history = deque() 
        self.is_engaged = False
        
    def update(self, is_locked):
        """
        Her frame'de kilit durumunu günceller.
        """
        now = time.time()
        self.history.append((now, is_locked))
        
        # Pencere dışındaki eski verileri temizle
        while self.history and self.history[0][0] < (now - self.window_size):
            self.history.popleft()
            
        # Toplam kilitlenme süresini hesapla
        total_lock_duration = self._calculate_lock_duration()
        
        # Angajman Kararı
        if total_lock_duration >= self.target_lock_time:
            self.is_engaged = True
        else:
            self.is_engaged = False
            
        return self.is_engaged, total_lock_duration

    def _calculate_lock_duration(self):
        """
        Kuyruktaki verilere dayanarak toplam kilitli kalınan süreyi hesaplar.
        Basit yaklaşım: Gelen örnekler arasındaki sürenin toplamı.
        """
        if len(self.history) < 2:
            return 0.0
            
        lock_sum = 0.0
        for i in range(1, len(self.history)):
            prev_time, prev_locked = self.history[i-1]
            curr_time, curr_locked = self.history[i]
            
            # Eğer önceki durumda kilitliydiyse, o geçen süreyi ekle
            if prev_locked:
                lock_sum += (curr_time - prev_time)
                
        return lock_sum

    def reset(self):
        """Kilit geçmişini sıfırla."""
        self.history.clear()
        self.is_engaged = False

if __name__ == "__main__":
    # Test Senaryosu
    lm = LockManager()
    print("--- Lock Manager Testi Başlatılıyor (10 saniye boyunca) ---")
    
    start_test = time.time()
    while (time.time() - start_test) < 12:
        # İlk 3 saniye kilit yok, sonra 6 saniye kilit var
        elapsed = time.time() - start_test
        locked_status = (elapsed > 3.0 and elapsed < 9.0)
        
        engaged, duration = lm.update(locked_status)
        
        print(f"Sure: {elapsed:.1f}s, Kilit: {locked_status}, Toplam Kilit: {duration:.2f}s, Atis: {engaged}")
        time.sleep(0.5)
