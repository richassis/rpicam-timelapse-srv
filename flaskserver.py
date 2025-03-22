import io
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from flask import Flask, Response, send_from_directory
import time
import os

# import io
# from flask import Flask, Response, send_from_directory
# from PIL import Image, ImageDraw
# import time
# import random
# import os

buffer = io.BytesIO()
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}, controls={"FrameDurationLimits": (40000, 40000)}))
output = FileOutput(buffer)


app = Flask(__name__)

import time

def generate_frames2():
    picam2.start_recording(JpegEncoder(), FileOutput(output))
    
    while True:
        buffer.seek(0)

        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.read() + b'\r\n'

        buffer.seek(0)
        buffer.truncate()
        time.sleep(1/23)


from PIL import Image

def generate_frames():
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            frame = picam2.capture_array()
            stream = io.BytesIO()
            img = Image.fromarray(frame)

            # Converte para RGB se necessário
            if img.mode != 'RGB':
                img = img.convert('RGB')

            img.save(stream, format='JPEG')
            stream.seek(0)

            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n'

            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time > 5:  # Calcula o FPS a cada 5 segundos
                print(f"FPS: {frame_count / elapsed_time:.2f}")
                frame_count = 0
                start_time = time.time()
    finally:
        picam2.stop()

# def generate_frames():
#     with picamera.PiCamera() as camera:
#         camera.resolution = (640, 480)
#         camera.framerate = 24
#         stream = io.BytesIO()

#         for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
#             stream.seek(0)
#             yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n'
#             stream.seek(0)
#             stream.truncate()


# def generate_frames():
#     while True:
#         # Cria uma imagem simulada com cor de fundo aleatória
#         bg_color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
#         img = Image.new('RGB', (640, 480), color=bg_color)
#         draw = ImageDraw.Draw(img)

#         # Adiciona um timestamp
#         timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
#         draw.text((10, 10), f"Simulated Frame - {timestamp}", fill=(255, 255, 255))

#         # Salva a imagem em um buffer
#         stream = io.BytesIO()
#         img.save(stream, format='JPEG')
#         stream.seek(0)

#         # Gera o frame no formato esperado
#         yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n'
#         time.sleep(1 / 24)  # Simula 24 FPS



def get_list_of_photos(pathname):
    photos_path = os.path.abspath(pathname)
    if not os.path.exists(photos_path) or not os.path.isdir(photos_path):
        return None
    
    return [f for f in os.listdir(photos_path) if os.path.isfile(os.path.join(photos_path, f))]



@app.route('/')
def index():
    # Página HTML que inclui o stream de vídeo, botão para capturar foto e botão para visualizar lista de fotos
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simulação de Câmera</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f4f4f9;
                text-align: center;
            }
            h1 {
                color: #333;
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
            img {
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
        </style>
        <script>
            function takePhoto() {
                fetch('/take_photo', { method: 'POST' })
                    .then(response => {
                        if (response.ok) {
                            alert('Foto capturada com sucesso!');
                        } else {
                            alert('Erro ao capturar a foto.');
                        }
                    })
                    .catch(error => {
                        console.error('Erro:', error);
                        alert('Erro ao capturar a foto.');
                    });
            }
        </script>
    </head>
    <body>
        <h1>Simulação de Câmera</h1>
        <p>O feed de vídeo está abaixo:</p>
        <img src="/video_feed" alt="Video Feed" style="width: 640px; height: 480px; border: 1px solid black;">
        <br><br>
        <button onclick="takePhoto()">Capturar Foto</button>
        <button onclick="window.location.href='/photos_list'">Visualizar Lista de Fotos</button>
    </body>
    </html>
    """

@app.route('/take_photo', methods=['POST'])
def take_photo():
    # Aqui você pode adicionar a lógica para salvar uma imagem ou executar outra ação
    print("Foto capturada!")  # Apenas para demonstração
    return "Foto capturada com sucesso!", 200

@app.route('/video_feed')
def video_feed():
    # Retorna o stream de imagens gerado pela função generate_frames
    return Response(generate_frames2(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/photos_list')
def photos_list():
    # Retorna a lista de fotos no diretório "photos"
    list = get_list_of_photos('photos')

    if not list: 
        print("ERROR: Photos directory not found")
        return "ERROR: Photos directory not found!", 300

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
        html_content += f'<li><a href="/photos/{photo}" target="_blank">{photo}</a></li>'
    
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
    photos_path = os.path.abspath('photos')
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






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)