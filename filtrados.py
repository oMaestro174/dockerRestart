from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import docker
import logging
import pandas as pd  # Certifique-se de que pandas está instalado

# Inicialização do cliente Docker e da aplicação FastAPI
app = FastAPI()
client = docker.from_env()

# Configuração do logging em arquivo
log_file_path = "container_manager.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()]
)

# Carregar contêineres a partir de um arquivo CSV
def load_containers_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df['container_name'].tolist()  # Certifique-se que a coluna correta é referenciada
    except Exception as e:
        logging.error(f"Erro ao carregar contêineres do CSV: {e}")
        return []

# Lista de contêineres a serem gerenciados
containers_to_manage = load_containers_from_csv('containers.csv')

# Página inicial para listar e controlar contêineres
@app.get("/", response_class=HTMLResponse)
async def home():
    return generate_html_content()

# Função para gerar o HTML com a lista de contêineres
def generate_html_content():
    containers = client.containers.list(all=True)
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gerenciador de Contêineres</title>
        <script src="https://unpkg.com/htmx.org@1.7.0"></script>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f4f4f4;
                color: #333;
                margin: 0;
                padding: 20px;
            }
            h1 {
                color: #4CAF50;
                text-align: center;
            }
            ul {
                list-style-type: none;
                padding: 0;
                max-width: 600px;
                margin: auto;
            }
            li {
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin: 10px 0;
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            button {
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            button.running {
                background-color: #4CAF50; /* Verde para em execução */
            }
            button.stopped {
                background-color: #FF5722; /* Vermelho para contêiner em execução */
            }
            button.stop {
                background-color: #B0BEC5; /* Cinza para contêiner parado */
                cursor: not-allowed; /* Muda o cursor para indicar que não é clicável */
            }
            button:hover {
                opacity: 0.9; /* Leve efeito ao passar o mouse */
            }
            span {
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>Gerenciador de Contêineres</h1>
        <ul>
    """

    # Gerar a lista de contêineres para gerenciar
    for container_name in containers_to_manage:
        try:
            container = client.containers.get(container_name)  # Obtém o contêiner pelo nome
            status_span_id = f"status-{container.id}"
            html_content += f"""
                <li>
                    {container.name} - Status: <span id="{status_span_id}">{container.status}</span>
                    <div>
                        <button class="running" hx-post="/containers/{container.id}/restart" hx-target="#{status_span_id}">
                            Reiniciar
                        </button>
                        <button class="{'stopped' if container.status == 'running' else 'stop'}" 
                                hx-post="/containers/{container.id}/stop" 
                                hx-target="#{status_span_id}"
                                {'disabled' if container.status != 'running' else ''}>
                            Parar
                        </button>
                    </div>
                </li>
            """
        except docker.errors.NotFound:
            logging.error(f"Contêiner {container_name} não encontrado.")
            html_content += f"<li>{container_name} - Não encontrado</li>"
        except Exception as e:
            logging.error(f"Erro ao acessar contêiner {container_name}: {e}")
            html_content += f"<li>{container_name} - Erro: {e}</li>"

    html_content += """
        </ul>
    </body>
    </html>
    """
    return html_content.strip()  # Remove espaços em branco do início e do fim

# Endpoint para reiniciar o contêiner
@app.post("/containers/{container_id}/restart")
async def restart_container(request: Request, container_id: str):
    ip_address = request.client.host  # Obtém o IP do cliente
    logging.info(f"Recebendo pedido para reiniciar contêiner: {container_id} de IP: {ip_address}")
    try:
        container = client.containers.get(container_id)
        container.restart()
        container.reload()  # Atualiza o status do contêiner
        logging.info(f"Contêiner {container_id} reiniciado com sucesso por IP: {ip_address}.")
        return container.status  # Retorna apenas o status atualizado do contêiner
    except docker.errors.NotFound:
        logging.error(f"Contêiner {container_id} não encontrado para reiniciar.")
        raise HTTPException(status_code=404, detail="Contêiner não encontrado")
    except Exception as e:
        logging.error(f"Erro ao reiniciar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")

# Endpoint para parar o contêiner
@app.post("/containers/{container_id}/stop")
async def stop_container(request: Request, container_id: str):
    ip_address = request.client.host  # Obtém o IP do cliente
    logging.info(f"Recebendo pedido para parar contêiner: {container_id} de IP: {ip_address}")
    try:
        container = client.containers.get(container_id)
        container.stop()
        container.reload()  # Atualiza o status do contêiner
        logging.info(f"Contêiner {container_id} parado com sucesso por IP: {ip_address}.")
        return container.status  # Retorna apenas o status atualizado do contêiner
    except docker.errors.NotFound:
        logging.error(f"Contêiner {container_id} não encontrado para parar.")
        raise HTTPException(status_code=404, detail="Contêiner não encontrado")
    except Exception as e:
        logging.error(f"Erro ao parar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")
