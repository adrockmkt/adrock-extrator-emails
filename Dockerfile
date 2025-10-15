FROM apify/actor-python:latest

# Copia todos os arquivos da pasta local para o container
COPY . ./

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Comando que será executado ao rodar o Actor
CMD ["python", "extrator.py"]