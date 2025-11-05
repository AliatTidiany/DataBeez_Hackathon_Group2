#!/bin/bash

echo "🚀 Démarrage du service ML Models..."

# Vérifier si l'entraînement est demandé
if [ "$TRAIN_ON_START" = "true" ]; then
    echo "📚 Entraînement forcé via TRAIN_ON_START=true"
    python models/train_all_models.py
    echo "✅ Entraînement terminé!"
elif [ ! -d "/app/models/saved" ] || [ -z "$(ls -A /app/models/saved)" ]; then
    echo "📚 Aucun modèle trouvé. Entraînement automatique..."
    python models/train_all_models.py
    echo "✅ Entraînement terminé!"
else
    echo "✅ Modèles existants trouvés, pas besoin d'entraîner"
fi

# Lancer Streamlit
echo "🌐 Lancement de l'interface Streamlit..."
streamlit run models/streamlit_app.py --server.port=8501 --server.address=0.0.0.0