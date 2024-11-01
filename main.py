from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os
import subprocess
from logs import log_pid

app = FastAPI()

# CORS configuration (unchanged)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "API funcionando!"}

@app.get("/containers")
async def list_containers():
    try:
        # List all containers, including stopped ones
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"], 
            stdout=subprocess.PIPE, 
            text=True,
            check=True
        )
        containers = [eval(line) for line in result.stdout.strip().splitlines()]
        logger.info("Listando todos os contêineres Docker (incluindo parados)")
        return {"containers": containers}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao listar contêineres: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar contêineres Docker")

@app.post("/containers/{container_id}/stop")
async def stop_container(container_id: str):
    try:
        subprocess.run(["docker", "stop", container_id], check=True)
        logger.info(f"Contêiner {container_id} parado")
        return {"message": f"Contêiner {container_id} parado com sucesso."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao parar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao parar contêiner")

@app.post("/containers/{container_id}/start")
async def start_container(container_id: str):
    try:
        subprocess.run(["docker", "start", container_id], check=True)
        logger.info(f"Contêiner {container_id} iniciado")
        return {"message": f"Contêiner {container_id} iniciado com sucesso."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao iniciar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao iniciar contêiner")

@app.post("/containers/{container_id}/restart")
async def restart_container(container_id: str):
    try:
        subprocess.run(["docker", "restart", container_id], check=True)
        logger.info(f"Contêiner {container_id} reiniciado")
        return {"message": f"Contêiner {container_id} reiniciado com sucesso."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao reiniciar contêiner {container_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao reiniciar contêiner")

if __name__ == "__main__":
    pid = os.getpid()
    log_pid(pid)
    logger.info("Iniciando a aplicação FastAPI")