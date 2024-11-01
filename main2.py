from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os
import subprocess
import json
import csv
from io import StringIO
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

# Global variable to store filtered container IDs
filtered_container_ids = set()

@app.get("/")
async def read_root():
    return {"message": "API funcionando!"}

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    global filtered_container_ids
    filtered_container_ids.clear()
    
    content = await file.read()
    csv_content = content.decode()
    csv_reader = csv.DictReader(StringIO(csv_content))
    
    for row in csv_reader:
        if 'container_id' in row:
            filtered_container_ids.add(row['container_id'])
    
    return {"message": f"CSV processado. {len(filtered_container_ids)} IDs de contêineres filtrados."}

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
        
        if filtered_container_ids:
            containers = [c for c in containers if c['ID'] in filtered_container_ids]
        
        logger.info(f"Listando {len(containers)} contêineres Docker filtrados")
        return {"containers": containers}
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao listar contêineres: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar contêineres Docker")

# Existing stop_container, start_container, and restart_container functions remain unchanged

if __name__ == "__main__":
    pid = os.getpid()
    log_pid(pid)
    logger.info("Iniciando a aplicação FastAPI")