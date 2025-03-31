import os
import json
from datetime import datetime

class MessageLogger:
    def __init__(self, log_dir="logs"):
        """Inizializza il logger dei messaggi"""
        self.log_dir = log_dir
        self.current_log_file = None
        self.ensure_log_directory()
        
    def ensure_log_directory(self):
        """Assicura che la directory dei log esista"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            print(f"Creata directory dei log: {self.log_dir}")

            
    
    def get_current_log_file(self):
        """Ottiene il nome del file di log corrente basato sulla data"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"telegram_log_{today}.jsonl")
        return log_file
    
    def log_message(self, message):
        """Salva un messaggio nel file di log"""
        try:
            log_file = self.get_current_log_file()
            
            # Estrai le informazioni rilevanti dal messaggio
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "chat_type": message.chat.type,
                "user_id": message.from_user.id,
                "user_first_name": message.from_user.first_name,
                "user_last_name": message.from_user.last_name,
                "username": message.from_user.username,
                "text": message.text,
                # Corretto: converte il timestamp UNIX in una stringa ISO
                "date": datetime.fromtimestamp(message.date).isoformat() if hasattr(message, 'date') else None,
            }
            
            # Aggiungi il messaggio al file di log in formato JSONL (JSON Lines)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
            return True
        except Exception as e:
            print(f"Errore durante il salvataggio del log: {e}")
            return False
    
    def get_recent_logs(self, count=100):
        """Legge i log più recenti"""
        try:
            log_file = self.get_current_log_file()
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, "r", encoding="utf-8") as f:
                # Leggi le ultime 'count' righe
                lines = f.readlines()[-count:]
                logs = [json.loads(line) for line in lines]
                return logs
        except Exception as e:
            print(f"Errore durante la lettura dei log: {e}")
            return []
    
    def load_logs(self):
        """Carica i log precedenti all'avvio del bot"""
        try:
            log_files = []
            
            # Trova tutti i file di log nella directory
            if os.path.exists(self.log_dir):
                for file in os.listdir(self.log_dir):
                    if file.startswith("telegram_log_") and file.endswith(".jsonl"):
                        log_files.append(os.path.join(self.log_dir, file))
            
            if not log_files:
                print("Nessun file di log precedente trovato.")
                return 0
                
            total_logs = 0
            # Conta le righe in tutti i file di log
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        log_count = len(lines)
                        total_logs += log_count
                        print(f"File di log {os.path.basename(log_file)}: {log_count} messaggi")
                except Exception as e:
                    print(f"Errore durante la lettura del file di log {log_file}: {e}")
                    
            print(f"Totale messaggi nei log: {total_logs}")
            return total_logs
        except Exception as e:
            print(f"Errore durante il caricamento dei log: {e}")
            return 0
    
    def extract_users_from_logs(self):
        """Estrae gli utenti dai file di log"""
        try:
            users = {}  # Dizionario chat_id -> {user_id -> user_info}
            
            # Controlla se la directory esiste
            if not os.path.exists(self.log_dir):
                print("Directory dei log non trovata.")
                return users
                
            # Trova tutti i file di log nella directory
            log_files = []
            for file in os.listdir(self.log_dir):
                if file.startswith("telegram_log_") and file.endswith(".jsonl"):
                    log_files.append(os.path.join(self.log_dir, file))
            
            if not log_files:
                print("Nessun file di log trovato per estrarre utenti.")
                return users
                
            print(f"Estrazione utenti da {len(log_files)} file di log...")
            
            # Processa ogni file di log
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                log_entry = json.loads(line)
                                
                                # Estrai dati rilevanti
                                chat_id = log_entry.get("chat_id")
                                user_id = log_entry.get("user_id")
                                
                                if chat_id is None or user_id is None:
                                    continue
                                    
                                # Inizializza la struttura dati se necessario
                                if chat_id not in users:
                                    users[chat_id] = {}
                                    
                                # Aggiorna o crea l'utente
                                if user_id not in users[chat_id]:
                                    users[chat_id][user_id] = {
                                        'id': user_id,
                                        'first_name': log_entry.get("user_first_name", ""),
                                        'last_name': log_entry.get("user_last_name", ""),
                                        'username': log_entry.get("username", "")
                                    }
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"Errore durante la lettura del file {log_file}: {e}")
                    continue
                    
            # Conta il numero di utenti estratti
            total_users = sum(len(chat_users) for chat_users in users.values())
            print(f"Estratti {total_users} utenti unici dai log")
            
            return users
        except Exception as e:
            print(f"Errore durante l'estrazione degli utenti dai log: {e}")
            return {}
    
    def extract_messages_from_logs(self):
        """Estrae i messaggi degli utenti dai file di log"""
        try:
            user_messages = {}  # Dizionario {chat_id -> {user_id -> [messaggi]}}
            
            # Controlla se la directory esiste
            if not os.path.exists(self.log_dir):
                print("Directory dei log non trovata.")
                return user_messages
                
            # Trova tutti i file di log nella directory
            log_files = []
            for file in os.listdir(self.log_dir):
                if file.startswith("telegram_log_") and file.endswith(".jsonl"):
                    log_files.append(os.path.join(self.log_dir, file))
            
            if not log_files:
                print("Nessun file di log trovato per estrarre messaggi.")
                return user_messages
                
            print(f"Estrazione messaggi da {len(log_files)} file di log...")
            
            # Processa ogni file di log
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                log_entry = json.loads(line)
                                
                                # Estrai dati rilevanti
                                chat_id = log_entry.get("chat_id")
                                user_id = log_entry.get("user_id")
                                text = log_entry.get("text", "")
                                
                                # Ignora messaggi vuoti o comandi
                                if not text or text.startswith('/') or chat_id is None or user_id is None:
                                    continue
                                    
                                # Inizializza la struttura dati se necessario
                                if chat_id not in user_messages:
                                    user_messages[chat_id] = {}
                                if user_id not in user_messages[chat_id]:
                                    user_messages[chat_id][user_id] = []
                                    
                                # Aggiungi il messaggio alla lista dei messaggi dell'utente
                                user_messages[chat_id][user_id].append(text)
                                
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"Errore durante la lettura del file {log_file}: {e}")
                    continue
            
            # Conta il numero totale di messaggi estratti
            total_messages = sum(len(messages) for chat_msgs in user_messages.values() for messages in chat_msgs.values())
            print(f"Estratti {total_messages} messaggi da {len(user_messages)} chat")
            
            return user_messages
        except Exception as e:
            print(f"Errore durante l'estrazione dei messaggi dai log: {e}")
            return {}
    
    def get_user_message_history(self, chat_id, user_id):
        """Estrae tutti i messaggi di un utente specifico dai log"""
        user_messages = []
        
        # Controlla se la directory esiste
        if not os.path.exists(self.log_dir):
            return user_messages
            
        # Trova tutti i file di log nella directory
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.startswith("telegram_log_") and file.endswith(".jsonl"):
                log_files.append(os.path.join(self.log_dir, file))
        
        # Processa ogni file di log
        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line)
                            
                            # Controlla se il messaggio è dell'utente e della chat specifici
                            if (log_entry.get("user_id") == user_id and 
                                log_entry.get("chat_id") == chat_id and 
                                log_entry.get("text") and 
                                not log_entry.get("text").startswith('/')):  # Ignora i comandi
                                
                                # Aggiungi il messaggio con timestamp
                                user_messages.append({
                                    "timestamp": log_entry.get("timestamp", ""),
                                    "text": log_entry.get("text", "")
                                })
                                
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Errore durante la lettura del file {log_file}: {e}")
                continue

            
        
        # Ordina i messaggi per timestamp
        user_messages.sort(key=lambda x: x["timestamp"])
        
        return user_messages
    
    def get_chat_message_history(self, chat_id):
        """Estrae tutti i messaggi di una chat specifica dai log, organizzati per utente"""
        chat_messages = []
        messages_count = 0
        
        # Controlla se la directory esiste
        if not os.path.exists(self.log_dir):
            return chat_messages
            
        # Trova tutti i file di log nella directory
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.startswith("telegram_log_") and file.endswith(".jsonl"):
                log_files.append(os.path.join(self.log_dir, file))
        
        # Ordina i file di log per data (più recenti prima)
        log_files.sort(reverse=True)
        
        # Processa ogni file di log
        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line)
                            
                            # Controlla se il messaggio è della chat specifica
                            # Includi TUTTI i messaggi, anche i comandi (rimuovendo il filtro)
                            if (log_entry.get("chat_id") == chat_id and 
                                log_entry.get("text")):
                                
                                # Aggiungi il messaggio con informazioni complete
                                chat_messages.append({
                                    "timestamp": log_entry.get("timestamp", ""),
                                    "user_id": log_entry.get("user_id", ""),
                                    "user_name": log_entry.get("user_first_name", ""),
                                    "username": log_entry.get("username", ""),
                                    "text": log_entry.get("text", "")
                                })
                                messages_count += 1
                                
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Errore durante la lettura del file {log_file}: {e}")
                continue
        
        # Ordina i messaggi per timestamp
        chat_messages.sort(key=lambda x: x["timestamp"])
        
        print(f"Estratti {messages_count} messaggi totali dalla chat {chat_id}")
        
        return chat_messages