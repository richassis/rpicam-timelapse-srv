from picamera2 import Picamera2
import time
import os

class Camera():

    def __init__(self):
        self.picam2 = Picamera2()
        self.photo_size = (3280, 2464)
        self.still_config = self.picam2.create_still_configuration(main={"size": self.photo_size})
        self.picam2.configure(self.still_config)
        self.timelapse_interval = 5 * 60  # Intervalo de 5 minutos

    def timelapse(self):
        print("Timelapse iniciado. Pressione Ctrl+C para finalizar.")
        try:
            while True:
                self.capture_photo()  # Captura a foto
                time.sleep(self.timelapse_interval)  # Aguarda o intervalo
        except KeyboardInterrupt:
            print("Timelapse finalizado.")

    def capture_photo(self):
        # Formato para o nome do arquivo
        timestamp_filename = time.strftime("%Y%m%d_%H%M%S")  # Para o nome do arquivo
        timestamp_readable = time.strftime("%Y-%m-%d %H:%M:%S")  # Para salvar no JSON

        photos_dir = "photos"
        os.makedirs(photos_dir, exist_ok=True)
        filename = os.path.join(photos_dir, f"{timestamp_filename}.jpg")

        try:
            # Captura a foto diretamente e salva no arquivo
            self.picam2.start()
            self.picam2.capture_file(filename)
            self.picam2.stop()

            print(f"Foto capturada: {filename}")
        except Exception as e:
            print(f"Erro ao capturar foto: {e}")


if __name__ == "__main__":
    camera = Camera()
    camera.timelapse()