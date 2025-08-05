#!/bin/bash

# Vérifier/créer le dossier locale
LOCALE_DIR="locale"
if [ ! -d "$LOCALE_DIR" ]; then
    echo "Création du dossier $LOCALE_DIR..."
    mkdir -p "$LOCALE_DIR"
fi

# Activer l'environnement virtuel
source .venvclim/bin/activate || { echo "Échec activation virtualenv"; exit 1; }

# Configurations
LANGUAGES=("en" "fr" "es" "pt")
EXTENSIONS="py,html"
IGNORE="migrations"

# Créer les fichiers .po
for lang in "${LANGUAGES[@]}"; do
    echo "Processing language: $lang"
    
    # Solution 1: Avec LOCALE_PATHS configuré
    django-admin makemessages -l "$lang" -e "$EXTENSIONS" -i "$IGNORE" || {
        # Solution 2: Alternative si LOCALE_PATHS non configuré
        echo "Tentative alternative..."
        python manage.py makemessages -l "$lang" -e "$EXTENSIONS" -i "$IGNORE" --locale-dir="$LOCALE_DIR"
    } || {
        echo "Échec création messages pour $lang"
        exit 1
    }
done

# Suite du script...
python Translate.py && django-admin compilemessages
deactivate