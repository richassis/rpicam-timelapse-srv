from flask import Flask, send_from_directory, request
import os
import time

app = Flask(__name__)

# Obter o nome do usuário de forma robusta
try:
    current_user = os.getenv("USER") or os.getenv("LOGNAME") or os.getlogin()
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

def get_last_photo_time(most_recent_photo):
    """
    Recebe o nome da foto mais recente no formato 'YYYYMMDD_hhmmss.jpg' e retorna o horário formatado.
    """
    try:
        # Verifica se o nome da foto está no formato esperado
        if not most_recent_photo or len(most_recent_photo) < 15:
            return "Formato inválido ou nenhuma foto disponível."

        # Remove a extensão do arquivo, se existir
        most_recent_photo = os.path.splitext(most_recent_photo)[0]

        # Extrai a data e hora do nome da foto
        date_str = most_recent_photo.split('_')[0]  # Parte 'YYYYMMDD'
        time_str = most_recent_photo.split('_')[1]  # Parte 'hhmmss'

        # Concatena e converte para o formato desejado
        datetime_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
        return datetime_str
    except Exception as e:
        print(f"Erro ao processar o horário da foto: {e}")
        return "Erro ao processar o horário da foto."

def get_most_recent_photo(pathname):
    try:
        photos = get_list_of_photos(pathname)
        if photos:
            return photos[0]  # Retorna a foto mais recente
        return None
    except Exception as e:
        print(f"Erro ao obter a foto mais recente: {e}")
        return None
    
@app.route('/')
def index():
    # Obtém o horário local do Raspberry
    local_time = time.strftime("%Y-%m-%d %H:%M:%S")
    most_recent_photo = get_most_recent_photo('photos')  # Obtém a foto mais recente
    last_photo_time = get_last_photo_time(most_recent_photo)  # Obtém o horário da última foto

    photo_html = ""
    if most_recent_photo:
        photo_html = f"""
        <div>
            <h2>Última foto tirada:</strong> {last_photo_time}</h2>
            <img src="/photos_raw/{most_recent_photo}" alt="Última Foto" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        </div>
        """
    else:
        photo_html = "<p><strong>Nenhuma foto disponível no momento.</strong></p>"


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
            form {{
                margin-top: 20px;
            }}
            input[type="datetime-local"] {{
                padding: 10px;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <h1>Setup de captura {current_user}</h1>
        {photo_html}
        <button onclick="window.location.href='/photos_list'">Visualizar Lista de Fotos</button>
        <br><br>
        <p><strong>Horário local do Raspberry:</strong> {local_time}</p>
        <div>
            <label for="datetime">Ajustar horário:</label>
            <input type="datetime-local" id="datetime" name="datetime" required>
            <button onclick="setTime()">Ajustar</button>
        </div>
        <script>
            function setTime() {{
                const datetime = document.getElementById('datetime').value;
                if (!datetime) {{
                    alert('Por favor, insira uma data e hora válidas.');
                    return;
                }}
                fetch('/set_time', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }},
                    body: `datetime=${{encodeURIComponent(datetime)}}`
                }})
                .then(response => {{
                    if (response.ok) {{
                        alert('Horário ajustado com sucesso!');
                        location.reload(); // Recarrega a página após o sucesso
                    }} else {{
                        alert('Erro ao ajustar o horário.');
                    }}
                }})
                .catch(error => {{
                    console.error('Erro:', error);
                    alert('Erro ao ajustar o horário.');
                }});
            }}
        </script>
    </body>
    </html>
    """

@app.route('/set_time', methods=['POST'])
def set_time():
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

@app.route('/photos_raw/<filename>')
def serve_photo_raw(filename):
    # Serve os arquivos do diretório "photos" diretamente
    photos_path = os.path.abspath('photos')  # Caminho absoluto para o diretório "photos"
    return send_from_directory(photos_path, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)