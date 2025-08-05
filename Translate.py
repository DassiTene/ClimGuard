#!/usr/bin/env python3
"""
Script de traduction automatique pour les fichiers .po Django
Utilise Google Translate API via googletrans et deep-translator
"""

import os
import time
import polib
from googletrans import Translator
from deep_translator import GoogleTranslator
from langdetect import detect, detect_langs, DetectorFactory
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration initiale
DetectorFactory.seed = 0  # Pour des résultats reproductibles
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration des traductions
LOCALE_DIR = "locale/"
TARGET_LANGS = ['en', 'fr']
MAX_RETRIES = 3
REQUEST_DELAY = 1  # Délai entre les requêtes en secondes

class TranslationManager:
    def __init__(self):
        self.translator = Translator()
        self.translations_cache = {}
        self.fallback_translator = GoogleTranslator

    def detect_source_language(self, text, target_langs):
        """Détecte si le texte est en 'fr' ou 'en' uniquement"""
        try:
            lang = detect(text)
            if lang in ('fr', 'en'):
                return lang
            # Si la détection retourne autre chose, choisir la langue la plus probable parmi fr/en
            lang_probabilities = detect_langs(text)
            for lang_prob in sorted(lang_probabilities, key=lambda x: -x.prob):
                if lang_prob.lang in ('fr', 'en'):
                    return lang_prob.lang
            return 'en'  # Fallback à l'anglais
        except:
            return 'en'  # Fallback à l'anglais

    def translate_text(self, text, source_lang, target_lang, retry_count=0):
        """
        Effectue la traduction avec gestion des erreurs et réessais
        """
        try:
            # Essayer d'abord avec googletrans
            translated = self.translator.translate(
                text, src=source_lang, dest=target_lang
            )
            if translated and hasattr(translated, 'text'):
                return translated.text
            
            # Fallback à deep-translator si échec
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        except Exception as e:
            if retry_count < MAX_RETRIES:
                time.sleep(REQUEST_DELAY * (retry_count + 1))
                return self.translate_text(text, source_lang, target_lang, retry_count + 1)
            logger.error(f"Échec traduction après {MAX_RETRIES} tentatives: {text}")
            return None

def process_po_file(lang):
    """Traite un fichier .po pour une langue spécifique"""
    po_file_path = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', 'django.po')
    
    if not os.path.exists(po_file_path):
        logger.warning(f"Fichier PO introuvable: {po_file_path}")
        return False

    po = polib.pofile(po_file_path)
    tm = TranslationManager()
    changed = False

    for entry in po:
        if not entry.msgstr and entry.msgid:
            source_lang = tm.detect_source_language(entry.msgid, TARGET_LANGS)
            if source_lang == lang:  # Éviter de traduire dans la même langue
                continue

            translated = tm.translate_text(
                entry.msgid,
                source_lang,
                lang
            )

            if translated:
                entry.msgstr = translated
                changed = True
                logger.info(
                    f"[{source_lang}→{lang}] {entry.msgid[:50]}... → {translated[:50]}..."
                )

    if changed:
        po.save()
        logger.info(f"Fichier {po_file_path} sauvegardé avec les traductions")
    return True

def main():
    """Fonction principale"""
    logger.info("Début du processus de traduction")
    
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(process_po_file, lang): lang
            for lang in TARGET_LANGS
        }
        
        for future in as_completed(futures):
            lang = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Erreur traitement {lang}: {str(e)}")

    logger.info("Processus de traduction terminé")

if __name__ == "__main__":
    main()