from flask import Flask, send_from_directory, request
import os
import time
import json

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

def get_last_photo_time():
    try:
        with open("last_photo.json", "r") as json_file:
            data = json.load(json_file)
            return data.get("last_photo_time", "Nenhuma foto tirada ainda.")
    except FileNotFoundError:
        return "Nenhuma foto tirada ainda."
    
@app.route('/')
def index():
    # Obtém o horário local do Raspberry
    local_time = time.strftime("%Y-%m-%d %H:%M:%S")
    last_photo_time = get_last_photo_time()  # Obtém o horário da última foto

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
        <p><strong>Última foto tirada:</strong> {last_photo_time}</p>
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