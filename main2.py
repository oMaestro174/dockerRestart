from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os
import subprocess
import json
import csv
from logs import log_pid

app = FastAPI()

# Configuração CORS (inalterada)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variável global para armazenar nomes de contêineres filtrados
filtered_container_names = set()

# Função para ler nomes de contêineres do CSV
def read_container_names_from_csv():
    global filtered_container_names
    csv_path = 'containers.csv'  # Certifique-se de que este arquivo está no mesmo diretório do seu script
    try:
        with open(csv_path, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                if 'container_name' in row:
                    filtered_container_names.add(row['container_name'])
        logger.info(f"Carregados {len(filtered_container_names)} nomes de contêineres do CSV")
    except FileNotFoundError:
        logger.error(f"Arquivo CSV não encontrado: {csv_path}")
    except Exception as e:
        logger.error(f"Erro ao ler arquivo CSV: {e}")

# Ler nomes de contêineres quando o app iniciar
read_container_names_from_csv()

@app.get("/")
async def read_root():
    return {"message": "API funcionando!"}

@app.get("/containers")
async def list_containers():
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        containers = [json.loads(line) for line in result.stdout.strip().splitlines()]
        
        if filtered_container_names:
            containers = [c for c in containers if any(name in c['Names'] for name in filtered_container_names)]
        
        logger.info(f"Listando {len(containers)} contêineres Docker filtrados")
        return {"containers": containers}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao listar contêineres: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar contêineres Docker")

@app.post("/containers/{container_name}/stop")
async def stop_container(container_name: str):
    try:
        subprocess.run(["docker", "stop", container_name], check=True)
        logger.info(f"Contêiner {container_name} parado")
        return {"message": f"Contêiner {container_name} parado com sucesso."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao parar contêiner {container_name}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao parar contêiner")

@app.post("/containers/{container_name}/start")
async def start_container(container_name: str):
    try:
        subprocess.run(["docker", "start", container_name], check=True)
        logger.info(f"Contêiner {container_name} iniciado")
        return {"message": f"Contêiner {container_name} iniciado com sucesso."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao iniciar contêiner {container_name}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao iniciar contêiner")

@app.post("/containers/{container_name}/restart")
async def restart_container(container_name: str):
    try:
        subprocess.run(["docker", "restart", container_name], check=True)
        logger.info(f"Contêiner {container_name} reiniciado")
        return {"message": f"Contêiner {container_name} reiniciado com sucesso."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao reiniciar contêiner {container_name}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao reiniciar contêiner")

if __name__ == "__main__":
    pid = os.getpid()
    log_pid(pid)
    logger.info("Iniciando a aplicação FastAPI")