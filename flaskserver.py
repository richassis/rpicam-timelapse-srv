from picamera2.encoders import JpegEncoder, H264Encoder
from flask import Flask, Response, send_from_directory
from picamera2.outputs import FileOutput
from libcamera import ColorSpace
from picamera2 import Picamera2
from threading import Condition, Thread
from PIL import Image
import time
import io
import os
import pwd

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class Camera():

    def __init__(self):
        
        try:
            self.picam2 = Picamera2()
        except:
            self.picam2 = None

        self.live_size = (640,480)
        self.photo_size = (3280,2464)

        self.time = 

        self.locked = False

        self.buffer = None
        self.output = StreamingOutput()

        if self.picam2:

            self.video_config = self.picam2.create_video_configuration(main={"size": self.live_size}, encode="main", controls={"FrameDurationLimits": (40000, 40000)}, colour_space=ColorSpace.Sycc())
            self.still_config = self.picam2.create_still_configuration(main={"size": self.photo_size})

            self.picam2.configure(self.video_config)

        self.timelapse_interval = 30*60
        self.timelapse_thread = None  # Armazena a thread de timelapse
        self.timelapse_running = False  # Indica se o timelapse está ativo
        
    def generate_frames(self):
        if not self.timelapse_running:  # Garante que o timelapse seja iniciado apenas uma vez
            self.start_timelapse()

        self.picam2.start_recording(JpegEncoder(), FileOutput(self.output))

        while True:

            if self.locked: 
                print("camera live locked")
                time.sleep(.5)
                continue

            with self.output.condition:
                self.output.condition.wait()
                self.buffer = io.BytesIO(self.output.frame)

            # Verifica se o buffer contém dados
            if self.buffer.getbuffer().nbytes == 0:
                print("Buffer vazio, aguardando dados...")
                time.sleep(0.1)
                continue

            try:
                frame = Image.open(self.buffer).convert('RGB')
            except Exception as e:
                print(f"Erro ao abrir a imagem: {e}")
                self.buffer.seek(0)
                self.buffer.truncate()
                continue
            
            stream = io.BytesIO()
            frame.save(stream, format='JPEG')
            stream.seek(0)

            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n'

            self.buffer.seek(0)
            self.buffer.truncate()
            # time.sleep(1/23)

    def start_timelapse(self):
        if not self.timelapse_running:  # Verifica se o timelapse já está ativo
            self.timelapse_running = True
            self.timelapse_thread = Thread(target=self.timelapse, daemon=True)
            self.timelapse_thread.start()

    def timelapse(self):
        while self.timelapse_running:
            time.sleep(self.timelapse_interval)
            self.capture_photo()

    def stop_timelapse(self):
        self.timelapse_running = False
        if self.timelapse_thread:
            self.timelapse_thread.join()

    def capture_photo(self):

        if self.locked: return

        self.locked = True
        self.picam2.stop_recording()

        try:
            self.picam2.switch_mode(self.still_config)
            request = self.picam2.capture_request()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}.jpg"

            photos_dir = "photos"  # Diretório onde as fotos serão salvas
            os.makedirs(photos_dir, exist_ok=True)  # Garante que o diretório existe
            filename = os.path.join(photos_dir, f"{timestamp}.jpg")  # Caminho completo do arquivo
            request.save("main", filename)
            request.release()

            print("Foto capturada!")  # Apenas para demonstração
        finally:
            self.picam2.switch_mode(self.video_config)
            self.picam2.start_recording(JpegEncoder(), FileOutput(self.output))
            self.locked = False



picam2 = Camera() 

app = Flask(__name__)

# Obter o nome do usuário de forma robusta
try:
    current_user = os.getenv("USER") or os.getenv("LOGNAME") or pwd.getpwuid(os.getuid()).pw_name
except Exception as e:
    current_user = "STIHL"  # Valor padrão em caso de erro
    print(f"Erro ao obter o nome do usuário: {e}")

def get_list_of_photos(pathname):
    photos_path = os.path.abspath(pathname)
    if not os.path.exists(photos_path) or not os.path.isdir(photos_path):
        raise FileNotFoundError(f"O diretório '{pathname}' não existe ou não é um diretório válido.")
    
    return sorted(
        [f for f in os.listdir(photos_path) if os.path.isfile(os.path.join(photos_path, f))],
        reverse=True  # Ordena de forma decrescente
    )



@app.route('/')
def index():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Setup de captura {current_user}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f4f4f9;
                text-align: center;
            }}
            h1 {{
                color: #333;
            }}
            button {{
                margin: 10px;
                padding: 10px 20px;
                font-size: 16px;
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #0056b3;
            }}
            img {{
                width: 100%;
                max-width: 640px;
                height: auto;
                border: 1px solid black;
                object-fit: contain;
            }}
            form {{
                margin-top: 20px;
            }}
            input[type="datetime-local"] {{
                padding: 10px;
                font-size: 16px;
            }}
        </style>
        <script>
            function takePhoto() {{
                fetch('/take_photo', {{ method: 'POST' }})
                    .then(response => {{
                        if (response.ok) {{
                            alert('Foto capturada com sucesso!');
                        }} else {{
                            alert('Erro ao capturar a foto.');
                        }}
                    }})
                    .catch(error => {{
                        console.error('Erro:', error);
                        alert('Erro ao capturar a foto.');
                    }});
            }}
        </script>
    </head>
    <body>
        <h1>Setup de captura {current_user}</h1>
        <p>Visualização da câmera:</p>
        <img src="/video_feed" alt="Video Feed">
        <br><br>
        <button onclick="takePhoto()">Capturar Foto</button>
        <button onclick="window.location.href='/photos_list'">Visualizar Lista de Fotos</button>
        <br><br>
        <form action="/set_time" method="POST">
            <label for="datetime">Ajustar horário:</label>
            <input type="datetime-local" id="datetime" name="datetime" required>
            <button type="submit">Ajustar</button>
        </form>
    </body>
    </html>
    """

@app.route('/take_photo', methods=['POST'])
def take_photo():
    picam2.capture_photo()

    return "Foto capturada com sucesso!", 200

@app.route('/video_feed')
def video_feed():
    if picam2.picam2 is None:
        # Retorna uma mensagem de erro em texto simples se a câmera não estiver disponível
        return Response("Erro: Nenhuma câmera encontrada.", mimetype='text/plain')
    else:
        # Retorna o stream de imagens gerado pela função generate_frames
        return Response(picam2.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
@app.route('/photos_list')
def photos_list():
    # Retorna a lista de fotos no diretório "photos"
    try:
        list = get_list_of_photos('photos')
    except Exception as e:
        print(str(e))
        list = None

    # Gera uma página HTML com a lista de arquivos
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lista de Fotos</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f4f4f9;
            }
            h1 {
                color: #333;
                text-align: center;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background: #fff;
                margin: 10px 0;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            a {
                text-decoration: none;
                color: #007BFF;
            }
            a:hover {
                text-decoration: underline;
            }
            button {
                margin: 10px;
                padding: 10px 20px;
                font-size: 16px;
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <h1>Lista de Fotos</h1>
        <ul>
    """
    for photo in list:
        html_content += f'<li><a href="/photos/{photo}">{photo}</a></li>'
    
    html_content += """
        </ul>
        <button onclick="window.location.href='/'">Voltar para a Página Inicial</button>
    </body>
    </html>
    """
    return html_content

@app.route('/photos_raw/<filename>')
def serve_photo_raw(filename):
    # Serve os arquivos do diretório "photos" diretamente
    photos_path = os.path.abspath('photos')  # Caminho absoluto para o diretório "photos"
    return send_from_directory(photos_path, filename)


@app.route('/photos/<filename>')
def serve_photo(filename):
    # Serve uma página HTML que exibe a foto e inclui um botão para voltar
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visualizar Foto</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f4f4f9;
                text-align: center;
            }}
            img {{
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            button {{
                margin-top: 20px;
                padding: 10px 20px;
                font-size: 16px;
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #0056b3;
            }}
        </style>
    </head>
    <body>
        <h1>Visualizar Foto</h1>
        <img src="/photos_raw/{filename}" alt="{filename}">
        <br>
        <button onclick="window.location.href='/photos_list'">Voltar para a Lista</button>
    </body>
    </html>
    """

@app.route('/set_time', methods=['POST'])
def set_time():
    from flask import request
    datetime_str = request.form.get('datetime')  # Obtém o valor do formulário
    try:
        # Converte o valor recebido para o formato esperado pelo comando `date`
        datetime_obj = time.strptime(datetime_str, "%Y-%m-%dT%H:%M")
        formatted_time = time.strftime("%m%d%H%M%Y.%S", datetime_obj)

        # Ajusta o horário do sistema
        os.system(f"sudo date {formatted_time}")
        return "Horário ajustado com sucesso!", 200
    except Exception as e:
        print(f"Erro ao ajustar o horário: {e}")
        return "Erro ao ajustar o horário.", 500
    

#sudo visudo
#pi ALL=(ALL) NOPASSWD: /bin/date


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)