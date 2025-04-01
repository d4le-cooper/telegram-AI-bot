import requests
import json
import os
import random

class AIService:
    def __init__(self, model="llama3", api_url="http://localhost:11434/api/chat", log_dir="./logs"):
        self.model = model
        self.api_url = api_url
        
        # Carica gli intercalari e gli appellativi
        self.intercalari_cattivo = self._load_data_file("data/intercalari_cattivo.json", [])
        self.intercalari_non_cattivo = self._load_data_file("data/intercalari_non_cattivo.json", [])
        self.appellativi_cattivo = self._load_data_file("data/appellativi_cattivo.json", [])
        self.appellativi_non_cattivo = self._load_data_file("data/appellativi_non_cattivo.json", [])
        
        print(f"Caricati {len(self.intercalari_cattivo)} intercalari cattivi e {len(self.intercalari_non_cattivo)} intercalari non cattivi")
        print(f"Caricati {len(self.appellativi_cattivo)} appellativi cattivi e {len(self.appellativi_non_cattivo)} appellativi non cattivi")
        print(f"Intercalari cattivi: {self.intercalari_cattivo}")
        print(f"Intercalari non cattivi: {self.intercalari_non_cattivo}")
        print(f"Appellativi cattivi: {self.appellativi_cattivo}")
        print(f"Appellativi non cattivi: {self.appellativi_non_cattivo}")

    def _load_data_file(self, filepath, default_value):
        """Carica un file JSON e restituisce il contenuto"""
        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            print(f"⚠️ File {filepath} non trovato. Uso valore predefinito.")
            return default_value
        except json.JSONDecodeError as e:
            print(f"❌ Errore nel parsing del file {filepath}: {e}")
            return default_value
        except Exception as e:
            print(f"❌ Errore nel caricamento del file {filepath}: {e}")
            return default_value

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
            
            print(f"Payload inviato: {payload}")
            
            # Effettua la chiamata API a Ollama locale
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            print(f"Risposta ricevuta: {response.json()}")
            
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
                system_message = f"Sei un assistente AI italiano molto intelligente, utile e preciso. Oggi è {current_date}, siamo nel 2025."
            
            # Istruzione modificata per bilanciare fattualità e utilità
            system_message = system_message + "\n\nIMPORTANTE: Quando hai informazioni specifiche dal contesto della conversazione, utilizzale come fonte primaria. Quando non hai informazioni dal contesto, utilizza le tue conoscenze generali per fornire risposte utili. Evita di inventare fatti specifici che non puoi verificare, ma condividi liberamente le tue conoscenze generali. Non rispondere 'non ho sufficienti informazioni' a meno che la domanda non richieda dettagli molto specifici che non potresti conoscere."
            
            payload_messages = [{"role": "system", "content": system_message}]
            payload_messages.extend(messages)
            
            payload = {
                "model": self.model,
                "messages": payload_messages,
                "stream": False,
                "options": {
                    "temperature": 0.5,  # Aumentata per risposte più naturali
                    "num_predict": 1000,  # Aumentata da 300 a 1000 per risposte più lunghe
                    "top_p": 0.8        # Aumentato per maggiore variabilità
                }
            }
            
            print(f"Payload inviato: {payload}")
            
            # Effettua la chiamata API a Ollama locale
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            print(f"Risposta ricevuta: {response.json()}")
            
            # Estrai la risposta
            result = response.json()
            ai_response = result["message"]["content"]
            
            return ai_response
            
        except Exception as e:
            print(f"Errore durante la generazione della risposta AI: {e}")
            return f"Mi dispiace, c'è stato un problema con la mia risposta: {str(e)}"
    
    def generate_ai_response(self, prompt, chat_id, user_info=None, history_analysis=None, is_directed=True, is_cattivo=False):
        try:
            from datetime import datetime
            current_date = datetime.now().strftime("%d %B %Y")
            
            # Seleziona intercalari e appellativi in base alla modalità
            if is_cattivo:
                intercalare = random.choice(self.intercalari_cattivo) if self.intercalari_cattivo else "mannaggia"
                appellativo = random.choice(self.appellativi_cattivo) if self.appellativi_cattivo else "genio"
                print(f"Modalità cattivo: intercalare='{intercalare}', appellativo='{appellativo}'")
                system_message = f"Sei un assistente AI molto cattivo, maleducato e sarcastico. Oggi è {current_date}. Usa espressioni come '{intercalare}' e chiama l'utente '{appellativo}' in modo sarcastico e irrispettoso. IMPORTANTE: RISPONDI SEMPRE IN ITALIANO."
            else:
                intercalare = random.choice(self.intercalari_non_cattivo) if self.intercalari_non_cattivo else "oh cielo"
                appellativo = random.choice(self.appellativi_non_cattivo) if self.appellativi_non_cattivo else "amico"
                print(f"Modalità non cattivo: intercalare='{intercalare}', appellativo='{appellativo}'")
                system_message = f"Sei un assistente AI gentile e rispettoso. Oggi è {current_date}. Usa espressioni come '{intercalare}' e chiama l'utente '{appellativo}' in modo amichevole. IMPORTANTE: RISPONDI SEMPRE IN ITALIANO."
            
            # Aggiungi istruzioni per distinguere meglio i messaggi diretti al bot
            if is_directed:
                system_message += "\n\nIMPORTANTE: Rispondi specificamente alla domanda attuale senza confonderla con altre conversazioni."
            
            # Aggiungi il contesto dalla cronologia della chat se disponibile
            if history_analysis and history_analysis != "Nessuna informazione rilevante trovata.":
                system_message += f"\n\nDi seguito il contesto della conversazione:\n\n{history_analysis}\n\nUsa queste informazioni per contestualizzare la tua risposta."
            
            # Crea un singolo messaggio con il prompt
            messages = [{"role": "user", "content": prompt}]
            
            # Log del payload
            print(f"Payload inviato: {messages}")
            
            # Utilizziamo il metodo generate_response esistente
            return self.generate_response(messages, system_message)
        except Exception as e:
            print(f"Errore durante la generazione della risposta AI: {e}")
            return f"Mi dispiace, c'è stato un problema con la mia risposta: {str(e)}"
    
    def analyze_message_history(self, chat_messages, current_topic):
        """Analizza la cronologia dei messaggi della chat per trovare contenuti rilevanti"""
        try:
            # Limita a 50 messaggi più recenti per non sovraccaricare il modello
            recent_messages = chat_messages[-50:] if len(chat_messages) > 50 else chat_messages
            
            # Costruisci la rappresentazione della cronologia
            messages_text = []
            for msg in recent_messages:
                messages_text.append(f"- {msg['timestamp']}: {msg['user_name']} (@{msg['username'] if msg['username'] else 'no-username'}): {msg['text']}")
            
            messages_history = "\n".join(messages_text)
            
            prompt = f"""
            Analizza questa cronologia di messaggi della chat e trova SOLO informazioni FATTUALI e VERIFICABILI che sono rilevanti per rispondere al messaggio attuale: "{current_topic}".
            
            Cronologia della chat:
            {messages_history}
            
            Fornisci un breve riassunto (massimo 100 parole) delle informazioni FATTUALI trovate nella cronologia che possono aiutare a rispondere al messaggio attuale.
            Non inserire interpretazioni o speculazioni, solo fatti menzionati esplicitamente nei messaggi.
            
            Se non ci sono informazioni fattuali e verificabili rilevanti, rispondi con "Nessuna informazione rilevante trovata."
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
            
            print(f"Payload inviato: {payload}")
            
            # Effettua la chiamata API
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            print(f"Risposta ricevuta: {response.json()}")
            
            # Estrai la risposta
            result = response.json()
            analysis = result["message"]["content"]
            
            return analysis
            
        except Exception as e:
            print(f"Errore durante l'analisi della cronologia chat: {e}")
            return "Nessuna informazione rilevante trovata."
    
    def analyze_message_history_with_focus(self, chat_messages, current_topic, bot_username):
        """Analizza la cronologia dei messaggi con focus sui messaggi diretti al bot"""
        try:
            # Limita a 50 messaggi più recenti per non sovraccaricare il modello
            recent_messages = chat_messages[-50:] if len(chat_messages) > 50 else chat_messages
            
            # Costruisci la rappresentazione della cronologia con evidenza dei messaggi diretti al bot
            messages_text = []
            for msg in recent_messages:
                if bot_username in msg['text']:
                    # Evidenzia i messaggi diretti al bot
                    messages_text.append(f"- [MESSAGGIO DIRETTO AL BOT] {msg['timestamp']}: {msg['user_name']}: {msg['text']}")
                else:
                    # Messaggi normali
                    messages_text.append(f"- {msg['timestamp']}: {msg['user_name']}: {msg['text']}")
            
            messages_history = "\n".join(messages_text)
            
            prompt = f"""
            Analizza questa cronologia di messaggi della chat e trova informazioni RILEVANTI per rispondere al messaggio attuale: "{current_topic}".
            
            IMPORTANTE:
            1. Distingui chiaramente tra messaggi diretti al bot [MESSAGGIO DIRETTO AL BOT] e conversazioni generali
            2. Quando rispondi, riferisciti SOLO ai messaggi diretti al bot, non ai messaggi tra altri utenti
            3. Usa le conversazioni generali solo come contesto informativo, ma NON rispondere come se fossi uno degli utenti
            4. Quando ti viene fatta una domanda diretta, rispondi alla domanda senza confonderla con domande precedenti rivolte ad altri
            
            Cronologia della chat:
            {messages_history}
            
            Fornisci un breve riassunto delle informazioni rilevanti, concentrandoti principalmente sui messaggi diretti al bot.
            """
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Sei un assistente analitico che deve distinguere tra messaggi diretti al bot e conversazioni generali."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3
                }
            }
            
            print(f"Payload inviato: {payload}")
            
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            print(f"Risposta ricevuta: {response.json()}")
            
            result = response.json()
            return result["message"]["content"]
            
        except Exception as e:
            print(f"Errore durante l'analisi del contesto messaggi: {e}")
            return "Nessuna informazione rilevante trovata."
    
    def analyze_chat_context(self, chat_messages):
        """Analizza l'intera chat per creare un contesto comprensivo"""
        try:
            # Aumentato drasticamente il numero di messaggi analizzati
            # Usa fino a 5000 messaggi per avere un contesto più completo
            recent_messages = chat_messages[-5000:] if len(chat_messages) > 5000 else chat_messages
            
            print(f"Analizzando {len(recent_messages)} messaggi per il contesto della chat")
            
            # Costruisci la rappresentazione della cronologia
            messages_text = []
            for msg in recent_messages:
                messages_text.append(f"- {msg['timestamp']}: {msg['user_name']} (@{msg['username'] if msg['username'] else 'no-username'}): {msg['text']}")
            
            messages_history = "\n".join(messages_text)
            
            prompt = f"""
            Analizza questa cronologia di messaggi della chat e crea un RIASSUNTO COMPLETO di tutto ciò di cui si è discusso.
            
            IMPORTANTISSIMO:
            1. Mantieni traccia di TUTTI gli argomenti discussi, anche quelli apparentemente non importanti
            2. Ricorda PRECISAMENTE chi ha detto cosa
            3. Includi dettagli specifici, nomi, luoghi, eventi e opinioni menzionati
            4. Non filtrare o escludere informazioni - tutto potrebbe essere rilevante per future conversazioni
            
            Cronologia della chat:
            {messages_history}
            
            Fornisci un riassunto COMPLETO (fino a 1000 parole) che catturi TUTTE le informazioni discusse nella conversazione.
            Organizza il riassunto per argomenti principali, mantenendo chiaro chi ha detto cosa e quando.
            """
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Sei un assistente analitico ESTREMAMENTE PRECISO che deve creare un riassunto COMPLETO di una conversazione. Il tuo compito è ricordare OGNI dettaglio di cui si è parlato."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1000  # Aumentato per consentire riassunti più lunghi
                }
            }
            
            print(f"Payload inviato: {payload}")
            
            # Effettua la chiamata API
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            print(f"Risposta ricevuta: {response.json()}")
            
            # Estrai la risposta
            result = response.json()
            analysis = result["message"]["content"]
            
            return analysis
            
        except Exception as e:
            print(f"Errore durante l'analisi del contesto chat: {e}")
            return "Nessuna informazione rilevante trovata."
    
    def analyze_chat_context_with_focus(self, chat_messages, bot_username):
        """Analizza l'intera chat con focus distinto sui messaggi diretti al bot"""
        try:
            # Limita per non sovraccaricare
            recent_messages = chat_messages[-1000:] if len(chat_messages) > 1000 else chat_messages
            
            # Costruisci rappresentazione strutturata
            messages_to_bot = []
            general_messages = []
            
            for msg in recent_messages:
                if bot_username in msg['text']:
                    messages_to_bot.append(f"- [AL BOT] {msg['user_name']}: {msg['text']}")
                else:
                    general_messages.append(f"- {msg['user_name']}: {msg['text']}")
            
            prompt = f"""
            Analizza questa conversazione e crea un riassunto strutturato che distingua chiaramente:
            
            1. MESSAGGI DIRETTI AL BOT (indicati con [AL BOT])
            2. CONVERSAZIONI GENERALI tra gli utenti
            
            MESSAGGI DIRETTI AL BOT:
            {"\n".join(messages_to_bot)}
            
            CONVERSAZIONI GENERALI:
            {"\n".join(general_messages[:300])}  # Limitati per lunghezza
            
            Crea un riassunto organizzato con queste sezioni:
            1. "Riassunto dei messaggi diretti al bot" - cosa gli utenti hanno chiesto al bot
            2. "Contesto generale della conversazione" - argomenti principali discussi tra gli utenti
            
            IMPORTANTE: Mantieni questa struttura nel tuo riassunto per aiutare il bot a distinguere tra domande dirette e contesto generale.
            """
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Sei un assistente analitico che deve organizzare una conversazione distinguendo tra messaggi diretti al bot e conversazioni generali."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1000
                }
            }
                        
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result["message"]["content"]
            
        except Exception as e:
            print(f"Errore durante l'analisi del contesto chat: {e}")
            return "Nessuna informazione rilevante trovata."