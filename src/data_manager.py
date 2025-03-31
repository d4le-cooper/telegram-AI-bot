import os
import json
import time

class DataManager:
    def __init__(self, data_dir="data"):
        """Inizializza il gestore dei dati"""
        self.data_dir = data_dir
        self.user_data_file = os.path.join(data_dir, "user_data.json")
        self.conversation_file = os.path.join(data_dir, "conversations.json")
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Assicura che la directory dei dati esista"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"Creata directory dei dati: {self.data_dir}")
    
    def load_user_data(self):
        """Carica i dati degli utenti dal file"""
        try:
            if os.path.exists(self.user_data_file):
                with open(self.user_data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Errore durante il caricamento dei dati utenti: {e}")
            return {}
    
    def save_user_data(self, user_data):
        """Salva i dati degli utenti nel file"""
        try:
            with open(self.user_data_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Errore durante il salvataggio dei dati utenti: {e}")
            return False
    
    def load_conversations(self):
        """Carica la cronologia delle conversazioni dal file"""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Errore durante il caricamento delle conversazioni: {e}")
            return {}
    
    def save_conversations(self, conversations):
        """Salva la cronologia delle conversazioni nel file"""
        try:
            with open(self.conversation_file, "w", encoding="utf-8") as f:
                json.dump(conversations, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Errore durante il salvataggio delle conversazioni: {e}")
            return False
    
    def auto_save(self, user_data, conversations, interval=600):
        """Salva automaticamente i dati a intervalli regolari"""
        last_save = time.time()
        while True:
            current_time = time.time()
            if current_time - last_save >= interval:
                print("Salvataggio automatico dei dati...")
                self.save_user_data(user_data)
                self.save_conversations(conversations)
                last_save = current_time
            time.sleep(60)  # Controlla ogni minuto