import csv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import docker
import logging

# Configurações de log com diferentes níveis (INFO, ERROR, WARNING, etc.)
logging.basicConfig(
    filename="container_manager.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Inicialização do cliente Docker e da aplicação FastAPI
app = FastAPI()
client = docker.from_env()

# Carregar IDs ou nomes de contêineres permitidos a partir de um arquivo CSV
def load_allowed_containers():
    allowed_containers = set()
    with open("containers.csv", newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            allowed_containers.add(row[0].strip())
    logging.info("Lista de contêineres permitidos carregada com sucesso.")
    return allowed_containers

allowed_containers = load_allowed_containers()

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
                background-color: #FFC107;
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
            let bot;

            function botaoClicado(e) {
                bot = e;
                e.style.backgroundColor = 'red';
                e.disabled = true;
            }

            function setLoadingState(button, message) {
                button.classList.add('loading');
                button.disabled = true;
                button.innerText = message;
                document.getElementById('feedback').innerText = message;
                document.getElementById('feedback').style.display = 'block';
            }

            function updateContainerStatus(id, newStatus, isRunning) {
                const statusSpan = document.getElementById(`status-${id}`);
                const buttonRestart = document.getElementById(`restart-${id}`);
                const buttonStop = document.getElementById(`stop-${id}`);
                
                statusSpan.innerText = newStatus;

                if (isRunning) {
                    buttonStop.classList.remove('stopped');
                    buttonStop.classList.add('stop-running');
                    buttonStop.disabled = false;
                    buttonRestart.disabled = false;
                } else {
                    buttonStop.classList.add('stopped');
                    buttonStop.classList.remove('stop-running');
                    buttonStop.disabled = true;
                    buttonRestart.disabled = false;
                }

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
        if container.id in allowed_containers or container.name in allowed_containers:
            status_span_id = f"status-{container.id}"
            restart_button_id = f"restart-{container.id}"
            stop_button_id = f"stop-{container.id}"
            status_class = "running" if container.status == "running" else "stopped"
            stop_button_class = "stop-running" if container.status == "running" else "stopped"
            html_content += f"""
                <li>
                    {container.name} - Status: <span id="{status_span_id}">{container.status}</span>
                    <div>
                        <button id="{restart_button_id}" class="running" 
                                hx-post="/containers/{container.id}/restart" 
                                hx-target="#{status_span_id}" 
                                hx-swap="outerHTML"
                                hx-on="htmx:beforeRequest=setLoadingState(this, 'Reiniciando...');botaoClicado(this)"
                                hx-on="htmx:afterRequest=updateContainerStatus('{container.id}', 'Em execução', true)">
                            Reiniciar
                        </button>
                        <button id="{stop_button_id}" class="{stop_button_class}" 
                                hx-post="/containers/{container.id}/stop" 
                                hx-target="#{status_span_id}"  
                                hx-swap="outerHTML" 
                                hx-on="htmx:beforeRequest=setLoadingState(this, 'Parando...');botaoClicado(this)"
                                hx-on="htmx:afterRequest=updateContainerStatus('{container.id}', 'Parado', false)">
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
        return HTMLResponse(content='<span style="color: green;">Em execução</span>', status_code=200)
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
        return HTMLResponse(content='<span style="color: gray;">Parado</span>', status_code=200)
    except docker.errors.NotFound:
        logging.warning(f"Tentativa de parar contêiner não encontrado: {container_id}")
        raise HTTPException(status_code=404, detail="Contêiner não encontrado")
    except Exception as e:
        logging.error(f"Erro ao parar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")
