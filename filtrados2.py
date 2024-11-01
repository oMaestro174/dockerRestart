from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import docker
import logging
import pandas as pd

app = FastAPI()
client = docker.from_env()

log_file_path = "container_manager.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()]
)

def load_containers_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df['container_name'].tolist()
    except Exception as e:
        logging.error(f"Erro ao carregar contêineres do CSV: {e}")
        return []

containers_to_manage = load_containers_from_csv('containers.csv')

@app.get("/", response_class=HTMLResponse)
async def home():
    return generate_html_content()

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
        <script>
            function reloadPage() {
                location.reload();
            }
        </script>
        <style>
            body { font-family: 'Arial', sans-serif; background-color: #f4f4f4; color: #333; padding: 20px; }
            h1 { color: #4CAF50; text-align: center; }
            ul { list-style-type: none; padding: 0; max-width: 600px; margin: auto; }
            li { background: white; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
            button { color: white; border: none; border-radius: 5px; padding: 10px 15px; cursor: pointer; }
            button.running { background-color: #4CAF50; }
            button.stopped { background-color: #FF5722; }
            button.stop { background-color: #B0BEC5; cursor: not-allowed; }
            span { font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Gerenciador de Contêineres</h1>
        <ul>
    """
    for container_name in containers_to_manage:
        try:
            container = client.containers.get(container_name)
            status_span_id = f"status-{container.id}"
            html_content += f"""
                <li>
                    {container.name} - Status: <span id="{status_span_id}">{container.status}</span>
                    <div>
                        <button class="running" hx-post="/containers/{container.id}/restart" hx-target="#{status_span_id}" hx-swap="outerHTML" hx-on="htmx:afterRequest: reloadPage()">
                            Reiniciar
                        </button>
                        <button class="{'stopped' if container.status == 'running' else 'stop'}" 
                                hx-post="/containers/{container.id}/stop" 
                                hx-target="#{status_span_id}"
                                hx-swap="outerHTML"
                                hx-on="htmx:afterRequest: reloadPage()"
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
    return html_content.strip()

@app.post("/containers/{container_id}/restart")
async def restart_container(request: Request, container_id: str):
    ip_address = request.client.host
    logging.info(f"Recebendo pedido para reiniciar contêiner: {container_id} de IP: {ip_address}")
    try:
        container = client.containers.get(container_id)
        container.restart()
        container.reload()
        logging.info(f"Contêiner {container_id} reiniciado com sucesso por IP: {ip_address}.")
        return f"<span id='status-{container.id}'>{container.status}</span>"
    except docker.errors.NotFound:
        logging.error(f"Contêiner {container_id} não encontrado para reiniciar.")
        raise HTTPException(status_code=404, detail="Contêiner não encontrado")
    except Exception as e:
        logging.error(f"Erro ao reiniciar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")

@app.post("/containers/{container_id}/stop")
async def stop_container(request: Request, container_id: str):
    ip_address = request.client.host
    logging.info(f"Recebendo pedido para parar contêiner: {container_id} de IP: {ip_address}")
    try:
        container = client.containers.get(container_id)
        container.stop()
        container.reload()
        logging.info(f"Contêiner {container_id} parado com sucesso por IP: {ip_address}.")
        return f"<span id='status-{container.id}'>{container.status}</span>"
    except docker.errors.NotFound:
        logging.error(f"Contêiner {container_id} não encontrado para parar.")
        raise HTTPException(status_code=404, detail="Contêiner não encontrado")
    except Exception as e:
        logging.error(f"Erro ao parar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")

