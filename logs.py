from loguru import logger

# Configuração do logger
logger.add("logs/api.log", rotation="500 MB", level="INFO", format="{time} {level} {message}")

def log_pid(pid):
    logger.info(f"Aplicação iniciada com PID: {pid}")
