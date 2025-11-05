# Dockerfile pour les modèles prédictifs
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY models/requirements.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copier le code de l'application
COPY models/ /app/models/
COPY data/ /app/data/
COPY config/ /app/config/
COPY etl/ /app/etl/

# Créer les dossiers nécessaires
RUN mkdir -p /app/models/saved
RUN mkdir -p /app/logs

# Exposer le port
EXPOSE 8501

# Variables d'environnement
ENV PYTHONPATH=/app

# Script de démarrage avec entraînement optionnel
COPY models/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Commande de démarrage
CMD ["/app/start.sh"]