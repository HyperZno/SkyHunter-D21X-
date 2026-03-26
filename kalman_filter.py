import numpy as np
import time

"""
D21X - KALMAN FILTRESI MODÜLÜ
Bozuk GNSS verilerini düzeltmek ve hedef konum tahmini yapmak için 4 durumlu (x, y, vx, vy) Kalman filtresi.
TEKNOFEST şartnamesine uygun olarak veri kaybı durumunda tahmin yapmaya devam eder.
"""

class TargetKalmanFilter:
    def __init__(self, dt=0.1):
        """
        Kalman filtresini ilklendirme.
        dt: Zaman adımı (saniye)
        """
        # Durum vektörü [x, y, vx, vy]
        self.X = np.zeros((4, 1))
        
        # Durum geçiş matrisi (A)
        self.A = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # Ölçüm matrisi (H) - Sadece konumları ölçüyoruz (GNSS'den)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Hata kovaryans matrisi (P)
        self.P = np.eye(4) * 100
        
        # Ölçüm gürültü matrisi (R)
        self.R = np.eye(2) * 2.0  # GNSS hassasiyeti (metre bazında)
        
        # Süreç gürültü matrisi (Q)
        self.Q = np.eye(4) * 0.1
        
        self.is_initialized = False

    def predict(self):
        """
        Bir sonraki durumu tahmin et. Veri kaybı anlarında bu metot kullanılır.
        """
        self.X = np.dot(self.A, self.X)
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q
        return self.X[:2]

    def update(self, z):
        """
        Yeni gelen GNSS verisi ile durumu güncelle.
        z: Ölçülen konum [x, y]
        """
        if not self.is_initialized:
            self.X[:2] = np.array(z).reshape(2, 1)
            self.is_initialized = True
            return self.X[:2]

        z = np.array(z).reshape(2, 1)
        
        # Sıçrama (Spike) Filtreleme
        # Tahmin edilen konum ile ölçüm arasındaki fark büyükse güncelleme yapma (veya kısıtla)
        innovation = z - np.dot(self.H, self.X)
        if np.linalg.norm(innovation) > 10.0:  # 10 metrelik ani sıçrama kontrolü
            print("[Warning] Kalman: Ani sıçrama tespit edildi, ölçüm yok sayılıyor.")
            return self.predict()

        # Kalman Kazancı (K)
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))

        # Durum Güncelleme
        self.X = self.X + np.dot(K, innovation)
        
        # Hata Kovaryans Güncelleme
        self.P = np.dot((np.eye(4) - np.dot(K, self.H)), self.P)
        
        return self.X[:2]

    def get_velocity(self):
        """Tahmin edilen hızı döndür."""
        return self.X[2:]

def simulation_test():
    """
    Simülasyon verisi ile Kalman filtresi testi.
    """
    kf = TargetKalmanFilter(dt=0.1)
    
    # Gerçek yol: Sabit hızla hareket eden bir hedef
    true_x, true_y = 0.0, 0.0
    vx, vy = 1.0, 0.5
    
    print("--- Kalman Filtresi Simülasyonu Başlatılıyor ---")
    for i in range(20):
        # 1. Gerçek konum güncelleme
        true_x += vx * 0.1
        true_y += vy * 0.1
        
        # 2. Gürültülü GNSS verisi oluşturma
        noise_x = true_x + np.random.normal(0, 0.5)
        noise_y = true_y + np.random.normal(0, 0.5)
        
        # 3. Veri kaybı simülasyonu (Örn: 10. frame'de veri yok)
        if i == 10:
            pred = kf.predict()
            print(f"Frame {i}: [VERI KAYBI] Tahmin edilen konum: {pred.flatten()}")
        else:
            updated = kf.update([noise_x, noise_y])
            print(f"Frame {i}: Ölçülen: {[noise_x, noise_y]}, Filtrelenen: {updated.flatten()}")
        
        time.sleep(0.05)

if __name__ == "__main__":
    simulation_test()
