# Gerenciador de Contêineres Docker

Este projeto é uma aplicação web simples que permite gerenciar contêineres Docker de forma interativa. Você pode visualizar, parar e reiniciar contêineres diretamente pelo navegador.

## Requisitos

### Software Necessário

- **Python**: A aplicação foi desenvolvida em Python. Você pode baixar a versão mais recente do Python [aqui](https://www.python.org/downloads/).
- **Docker**: Certifique-se de que o Docker está instalado e funcionando em sua máquina. Siga as instruções de instalação no site oficial do Docker [aqui](https://docs.docker.com/get-docker/).
- **FastAPI**: Para rodar a aplicação, você precisará instalar o FastAPI e o `uvicorn`, um servidor ASGI.

### Instalação de Dependências

1. **Crie um ambiente virtual (opcional, mas recomendado)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Em Linux/Mac
   venv\Scripts\activate  # Em Windows

