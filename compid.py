import csv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import docker
import logging
import os

# Configurações de log
logging.basicConfig(
    filename="container_manager.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Logar o PID do processo atual
pid = os.getpid()
logging.info(f"Aplicação iniciada com PID: {pid}")

# Inicialização do cliente Docker e da aplicação FastAPI
app = FastAPI()
client = docker.from_env()

# Função para gerar o HTML com a lista de contêineres permitidos
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
                background-color: #4CAF50;
            }
            button.stopped {
                background-color: #B0BEC5;
                cursor: not-allowed;
            }
            button.stop-running {
                background-color: #FF5722;
            }
            button.loading {
                background-color: #FFC107; /* Amarelo para indicar carregando */
                cursor: wait;
            }
            button:hover {
                opacity: 0.9;
            }
            span {
                font-weight: bold;
            }
            #feedback {
                color: green;
                text-align: center;
                margin-top: 20px;
                display: none;
            }
        </style>
        <script>
            function setLoadingState(button, message) {
                button.classList.add('loading');
                button.disabled = true;
                button.innerText = message;
                document.getElementById('feedback').innerText = message;
                document.getElementById('feedback').style.display = 'block';
            }

            function updateButtonState(button, isRunning) {
                button.classList.remove('loading');
                button.disabled = false;
                button.classList.toggle('stopped', !isRunning);
                button.classList.toggle('running', isRunning);
                button.innerText = isRunning ? 'Parar' : 'Parado';
            }

            function hideFeedback() {
                document.getElementById('feedback').style.display = 'none';
            }
        </script>
    </head>
    <body>
        <h1>Gerenciador de Contêineres</h1>
        <div id="feedback"></div>
        <ul>
    """

    for container in containers:
        status_span_id = f"status-{container.id}"
        status_class = "running" if container.status == "running" else "stopped"
        stop_button_class = "stop-running" if container.status == "running" else "stopped"
        html_content += f"""
            <li>
                {container.name} - Status: <span id="{status_span_id}">{container.status}</span>
                <div>
                    <button class="running" hx-post="/containers/{container.id}/restart" hx-target="#{status_span_id}" hx-on="htmx:response:showFeedback('Contêiner reiniciado com sucesso!')">
                        Reiniciar
                    </button>
                    <button class="{stop_button_class}" 
                            hx-post="/containers/{container.id}/stop" 
                            hx-target="closest li"
                            hx-swap="innerHTML" 
                            hx-trigger="click" 
                            hx-include="this"
                            hx-on="htmx:beforeRequest=setLoadingState(this, 'Parando...');"
                            hx-on="htmx:afterRequest=hideFeedback">
                        Parar
                    </button>
                </div>
            </li>
        """
    
    html_content += """
        </ul>
    </body>
    </html>
    """
    return html_content.strip()

# Rota para a página inicial
@app.get("/", response_class=HTMLResponse)
async def home():
    return generate_html_content()

# Endpoint para reiniciar o contêiner
@app.post("/containers/{container_id}/restart")
async def restart_container(request: Request, container_id: str):
    ip_address = request.client.host
    logging.info(f"Recebendo pedido para reiniciar contêiner: {container_id} de IP: {ip_address}")
    try:
        container = client.containers.get(container_id)
        container.restart()
        container.reload()
        logging.info(f"Contêiner {container_id} reiniciado com sucesso por IP: {ip_address}.")
        return HTMLResponse(content=f'<span style="color: green;">Em execução</span>', status_code=200)
    except docker.errors.NotFound:
        logging.error(f"Contêiner {container_id} não encontrado para reiniciar.")
        raise HTTPException(status_code=404, detail="Contêiner não encontrado")
    except Exception as e:
        logging.error(f"Erro ao reiniciar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")

# Endpoint para parar o contêiner
@app.post("/containers/{container_id}/stop")
async def stop_container(request: Request, container_id: str):
    ip_address = request.client.host
    logging.info(f"Recebendo pedido para parar contêiner: {container_id} de IP: {ip_address}")
    try:
        container = client.containers.get(container_id)
        container.stop()
        container.reload()
        logging.info(f"Contêiner {container_id} parado com sucesso por IP: {ip_address}.")
        # Retorna o HTML atualizado do contêiner após parar
        new_html = f"""
            <li>
                {container.name} - Status: <span id="status-{container.id}" style="color: gray;">Parado</span>
                <div>
                    <button class="running" hx-post="/containers/{container.id}/restart" hx-target="#status-{container.id}" hx-on="htmx:response:showFeedback('Contêiner reiniciado com sucesso!')">
                        Reiniciar
                    </button>
                    <button class="stopped" disabled>
                        Parar
                    </button>
                </div>
            </li>
        """
        return HTMLResponse(content=new_html, status_code=200)
    except docker.errors.NotFound:
        logging.error(f"Contêiner {container_id} não encontrado para parar.")
        raise HTTPException(status_code=404, detail="Contêiner não encontrado")
    except Exception as e:
        logging.error(f"Erro ao parar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")
