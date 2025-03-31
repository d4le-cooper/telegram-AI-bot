import requests
import json
import os

class AIService:
    def __init__(self, model="llama3", api_url="http://localhost:11434/api/chat", log_dir="./logs"):
        self.model = model
        self.api_url = api_url
        self.log_dir = log_dir
    
    def analyze_user_character(self, user_messages):
        """Analizza il carattere dell'utente basandosi sui suoi messaggi"""
        try:
            # Se non abbiamo abbastanza messaggi, ritorna
            if len(user_messages) < 3:
                return None
                
            # Prepariamo la richiesta per l'analisi del carattere
            prompt = f"""
            Analizza il carattere dell'utente basandoti sui seguenti messaggi. 
            Fornisci una breve descrizione (massimo 50 parole) della personalità e del modo di comunicare dell'utente.
            Identifica tratti come formalità/informalità, serietà/giocosità, tecnicità/semplicità, pazienza/impazienza.
            
            Messaggi dell'utente:
            {json.dumps(user_messages, indent=2)}
            
            Descrivi il carattere dell'utente in modo chiaro e conciso:
            """
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Sei un analista della personalità che deve descrivere brevemente il carattere di un utente basandoti sui suoi messaggi."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.5
                }
            }
            
            # Effettua la chiamata API a Ollama locale
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            # Estrai la risposta
            result = response.json()
            character_analysis = result["message"]["content"]
            
            return character_analysis
            
        except Exception as e:
            print(f"Errore durante l'analisi del carattere: {e}")
            return None
    
    def generate_response(self, messages, system_message=None):
        """Genera una risposta basata sulla cronologia dei messaggi"""
        try:
            if not system_message:
                from datetime import datetime
                current_date = datetime.now().strftime("%d %B %Y")
                system_message = f"Sei un assistente AI italiano molto intelligente, utile e preciso. Oggi è {current_date}, siamo nel 2025. Rispondi sempre in italiano."
            
            payload_messages = [{"role": "system", "content": system_message}]
            payload_messages.extend(messages)
            
            payload = {
                "model": self.model,
                "messages": payload_messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500
                }
            }
            
            # Effettua la chiamata API a Ollama locale
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            # Estrai la risposta
            result = response.json()
            ai_response = result["message"]["content"]
            
            return ai_response
            
        except Exception as e:
            print(f"Errore durante la generazione della risposta AI: {e}")
            return f"Mi dispiace, c'è stato un problema con la mia risposta: {str(e)}"
    
    def generate_ai_response(self, prompt, chat_id, user_info=None, history_analysis=None):
        """Genera una risposta AI con contesto arricchito dai log delle conversazioni"""
        try:
            # Preparazione del sistema di messaggi
            from datetime import datetime
            current_date = datetime.now().strftime("%d %B %Y")
            
            # Prepara il messaggio di sistema con info utente
            system_message = f"Sei un assistente AI italiano molto intelligente, utile e preciso. Oggi è {current_date}, siamo nel 2025. Rispondi sempre in italiano."
            
            # Aggiungi info personalizzazione se disponibile
            if user_info:
                system_message += f" Stai parlando con {user_info['first_name']}"
                if user_info.get('username'):
                    system_message += f" (@{user_info['username']})"
                
                # Aggiungi informazioni sul carattere dell'utente
                if 'carattere' in user_info and user_info['carattere']:
                    system_message += f". Questo utente ha il seguente carattere: {user_info['carattere']}."
                    system_message += " Adatta il tuo tono e contenuto in base a questo carattere."
                
                system_message += ". Personalizza le tue risposte in base a questo utente."
                
            # Aggiungi il contesto dalla cronologia della chat se disponibile
            if history_analysis and history_analysis != "Nessuna informazione rilevante trovata.":
                system_message += f"\n\nContesto della conversazione in questa chat: {history_analysis}\n\nUsa queste informazioni per contestualizzare la tua risposta e ricordati di chi ha detto cosa quando è rilevante, ma senza menzionare esplicitamente che stai usando informazioni dei messaggi precedenti."
            
            # Crea un singolo messaggio con il prompt
            messages = [{"role": "user", "content": prompt}]
            
            # Utilizziamo il metodo generate_response esistente
            return self.generate_response(messages, system_message)
            
        except Exception as e:
            print(f"Errore durante la generazione della risposta AI: {e}")
            return f"Mi dispiace, c'è stato un problema con la mia risposta: {str(e)}"
    
    def analyze_message_history(self, chat_messages, current_topic):
        """Analizza la cronologia dei messaggi della chat per trovare contenuti rilevanti"""
        try:
            # Limita a 50 messaggi più recenti per non sovraccaricare il modello
            recent_messages = chat_messages[-500:] if len(chat_messages) > 500 else chat_messages
            
            # Costruisci la rappresentazione della cronologia
            messages_text = []
            for msg in recent_messages:
                messages_text.append(f"- {msg['timestamp']}: {msg['user_name']} (@{msg['username'] if msg['username'] else 'no-username'}): {msg['text']}")
            
            messages_history = "\n".join(messages_text)
            
            prompt = f"""
            Analizza questa cronologia di messaggi della chat e trova informazioni rilevanti per rispondere al messaggio attuale: "{current_topic}".
            
            Cronologia della chat:
            {messages_history}
            
            Fornisci un riassunto (massimo 200 parole) delle informazioni rilevanti dalla cronologia che possono aiutare a rispondere al messaggio attuale.
            Ricorda di considerare chi ha detto cosa e di mantenere il contesto delle conversazioni tra i diversi utenti.
            Identifica eventuali argomenti di discussione, opinioni diverse, e informazioni condivise rilevanti per l'argomento attuale.
            
            Se non ci sono informazioni rilevanti, rispondi con "Nessuna informazione rilevante trovata."
            """
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Sei un assistente analitico che deve trovare informazioni rilevanti nella cronologia di una chat per rispondere meglio al messaggio attuale."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.5
                }
            }
            
            # Effettua la chiamata API
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            # Estrai la risposta
            result = response.json()
            analysis = result["message"]["content"]
            
            return analysis
            
        except Exception as e:
            print(f"Errore durante l'analisi della cronologia chat: {e}")
            return "Nessuna informazione rilevante trovata."