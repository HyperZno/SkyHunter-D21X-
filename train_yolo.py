import os
from ultralytics import YOLO

"""
D21X - YOLOv8 EĞİTİM MODÜLÜ
TEKNOFEST Savaşan İHA Avcı Drone Yarışması standartlarında İHA tespiti için özelleştirilmiştir.
Bu kod, Roboflow veya yerel olarak etiketlenmiş bir veri setini kullanarak YOLOv8 eğitimi yapar.
"""

def train_model():
    """
    YOLOv8 modelini eğitmek için ana fonksiyon.
    Parametreler:
    - epochs: 100 (Iterasyon sayısı)
    - imgsz: 640 (Girdi görüntü boyutu)
    - batch: 16 (Yığın boyutu)
    - device: 0 (GPU kullanımı, CPU için 'cpu' yazın)
    """
    try:
        # 1. Model Seçimi (Pre-trained YOLOv8 Nano önerilir - Hız için)
        model = YOLO('yolov8n.pt') 

        print("--- Eğitim Başlatılıyor ---")
        
        # 2. Eğitim Parametreleri
        # data.yaml dosyanızın yolunu belirtin
        results = model.train(
            data='data.yaml', 
            epochs=100, 
            imgsz=640, 
            batch=16, 
            device=0,   # NVIDIA GPU varsa 0, yoksa 'cpu'
            name='d21x_uav_detector',
            optimizer='SGD', # Veya 'Adam'
            lr0=0.01,        # Başlangıç öğrenme oranı
            patience=50,     # Erken durdurma sabrı
            augment=True     # Augmentasyon kullanımı
        )

        print("--- Eğitim Tamamlandı ---")
        print(f"Model şuraya kaydedildi: {model.export(format='onnx')}")

    except Exception as e:
        print(f"Eğitim sırasında bir hata oluştu: {str(e)}")

def test_model(model_path, source_path):
    """
    Eğitilen modeli test etmek için fonksiyon.
    """
    try:
        model = YOLO(model_path)
        results = model.predict(source=source_path, save=True, conf=0.5)
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                print(f"Tespit Edilen Sınıf: {box.cls}, Güven: {box.conf}")
                
    except Exception as e:
        print(f"Test sırasında bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    # Roboflow Entegrasyon Notu:
    # Roboflow'dan veri setinizi indirdikten sonra kök dizine 'data.yaml' dosyasını koyun.
    # Örnek Roboflow indirme komutu (terminalde çalıştırın):
    # pip install roboflow
    # roboflow.login()
    # project = rf.workspace("workspace-adı").project("project-adı")
    # dataset = project.version(1).download("yolov8")

    train_model()
    
    # Eğitim sonrası test için (yol modelin kaydedildiği yere göre güncellenmelidir)
    # test_model('runs/detect/d21x_uav_detector/weights/best.pt', 'test_video.mp4')
