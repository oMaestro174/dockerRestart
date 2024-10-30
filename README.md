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
 ```

2. **Instale as dependências necessárias**:
```bash
pip install fastapi[all] docker
```


3. **Configuração do CSV**

Antes de rodar a aplicação filtrados.py, você deve criar um arquivo containers.csv na raiz do projeto, onde você listará os IDs ou nomes dos contêineres que deseja gerenciar. 

Certifique-se de que o seu arquivo containers.csv contenha uma coluna chamada container_name que liste os nomes dos contêineres que você deseja gerenciar. O formato do CSV deve ser assim:


```bash
container_name
windows11
ubuntu
ubuntu2
```


4. **Rodar a aplicação**:

Executar com & no Final de Cada Comando
Adicionar & ao final do comando executa os processos em segundo plano:

```bash
uvicorn filtrados:app --host 0.0.0.0 --port 8080 & #roda aplicação na porta específica com apenas alguns containers
uvicorn main:app --host 0.0.0.0 --port 8081 & # roda a aplicação com todos os containers

```

## Funcionalidades

* Listagem de Contêineres: Visualize todos os contêineres listados no arquivo containers.csv com seu status atual.
* Reiniciar Contêineres: O botão "Reiniciar" permite reiniciar contêineres em execução.
* Parar Contêineres: O botão "Parar" permite parar contêineres em execução e é desativado para contêineres já parados.
* Interface Intuitiva: A interface foi desenvolvida com HTML e CSS para uma melhor experiência do usuário.

## Contribuição
Se você gostaria de contribuir para este projeto, sinta-se à vontade para abrir um pull request ou relatar problemas.

## Licença
Este projeto está sob a Licença MIT. Consulte o arquivo LICENSE para mais detalhes.
