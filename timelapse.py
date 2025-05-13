from picamera2 import Picamera2
import time
import os
import json  # Para salvar o horário da última foto

class Camera():

    def __init__(self):
        self.picam2 = Picamera2()
        self.photo_size = (3280, 2464)
        self.still_config = self.picam2.create_still_configuration(main={"size": self.photo_size})
        self.picam2.configure(self.still_config)
        self.timelapse_interval = 30 * 60  # Intervalo de 30 minutos

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

            # Salva o horário da última foto no JSON
            self.save_last_photo_time(timestamp_readable)
        except Exception as e:
            print(f"Erro ao capturar foto: {e}")

    def save_last_photo_time(self, timestamp):
        data = {"last_photo_time": timestamp}
        with open("last_photo.json", "w") as json_file:
            json.dump(data, json_file, indent=4)

if __name__ == "__main__":
    camera = Camera()
    camera.timelapse()