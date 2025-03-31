import os
import telebot
import threading
import time
from datetime import datetime
from config import BOT_TOKEN
from logger import MessageLogger
from data_manager import DataManager
from ai_service import AIService

# Initialize components
bot = telebot.TeleBot(BOT_TOKEN)
logger = MessageLogger()
data_manager = DataManager()
ai_service = AIService()

# Carica i dati salvati PRIMA di usarli
print("Caricamento dati precedenti...")
user_data = data_manager.load_user_data()
conversation_history = data_manager.load_conversations()
log_count = logger.load_logs()

# Cache per il contesto delle chat
chat_context_cache = {}

# Carica i contesti salvati precedentemente (DOPO aver caricato user_data)
print("Caricamento contesti salvati...")
for chat_id in user_data.keys():
    context_file = f"data/context_cache_{chat_id}.txt"
    if os.path.exists(context_file):
        try:
            with open(context_file, "r", encoding="utf-8") as f:
                context_text = f.read()
                chat_context_cache[chat_id] = {
                    "last_update": datetime.fromtimestamp(os.path.getmtime(context_file)),
                    "context": context_text,
                    "message_count": len(context_text.split("\n"))
                }
            print(f"Caricato contesto salvato per chat {chat_id}")
        except Exception as e:
            print(f"Errore nel caricamento del contesto per chat {chat_id}: {e}")

# Estrai gli utenti dai log e integra con i dati esistenti
print("Estrazione utenti dai log...")
log_users = logger.extract_users_from_logs()
users_from_logs = 0
characters_from_logs = 0

# Estrai i messaggi dagli utenti per analizzare il loro carattere
print("Analisi messaggi dai log per determinare il carattere degli utenti...")
log_messages = logger.extract_messages_from_logs()

for chat_id, users in log_users.items():
    if chat_id not in user_data:
        user_data[chat_id] = {}
    
    for user_id, user_info in users.items():
        is_new_user = user_id not in user_data[chat_id]
        
        # Aggiungiamo un nuovo utente dai log o aggiorniamo dati mancanti
        if is_new_user:
            user_data[chat_id][user_id] = user_info
            users_from_logs += 1
        else:
            # L'utente esiste già, ma potrebbe essere utile aggiornare alcuni campi
            for key, value in user_info.items():
                if key not in user_data[chat_id][user_id] or not user_data[chat_id][user_id][key]:
                    user_data[chat_id][user_id][key] = value
        
        # Controlla se abbiamo messaggi per questo utente per analizzare il carattere
        if ('carattere' not in user_data[chat_id][user_id] and 
            chat_id in log_messages and 
            user_id in log_messages[chat_id] and 
            len(log_messages[chat_id][user_id]) >= 5):
            
            try:
                print(f"Analisi carattere di {user_info['first_name']} dai log ({len(log_messages[chat_id][user_id])} messaggi)...")
                carattere = ai_service.analyze_user_character(log_messages[chat_id][user_id])
                if carattere:
                    user_data[chat_id][user_id]['carattere'] = carattere
                    characters_from_logs += 1
                    print(f"Carattere da log: {carattere[:50]}...")
            except Exception as e:
                print(f"Errore nell'analisi del carattere dai log: {e}")

# Conta il totale degli utenti dopo l'integrazione
total_users = sum(len(chat_users) for chat_users in user_data.values())
users_with_character = sum(1 for chat in user_data.values() for user in chat.values() if 'carattere' in user)

print(f"Dati caricati: {len(user_data)} chat, {total_users} utenti totali")
print(f"Utenti recuperati dai log: {users_from_logs}, di cui {characters_from_logs} con carattere analizzato")
print(f"Messaggi nella cronologia: {sum(len(chat) for chat in conversation_history.values() if isinstance(chat, list))}, log storici: {log_count}")

# Avvia il thread di salvataggio automatico
def auto_save_thread():
    data_manager.auto_save(user_data, conversation_history)

save_thread = threading.Thread(target=auto_save_thread, daemon=True)
save_thread.start()

# Thread per aggiornare periodicamente il contesto dai log
def context_update_thread():
    """Thread per aggiornare periodicamente il contesto dalle chat dai log"""
    global chat_context_cache
    
    print("Avviato thread di aggiornamento contesto...")
    while True:
        try:
            print("\n--- Aggiornamento contesto dalle chat ---")
            # Aggiorna il contesto per ogni chat conosciuta
            for chat_id in user_data.keys():
                # Recupera la cronologia messaggi dell'intera chat
                chat_history = logger.get_chat_message_history(chat_id)
                
                if not chat_history:
                    continue
                
                print(f"Analisi di {len(chat_history)} messaggi nella chat {chat_id} per contesto...")
                # Usa un prompt generico per l'analisi del contesto
                try:
                    context_analysis = ai_service.analyze_chat_context(chat_history)
                    # Salva il contesto analizzato nella cache
                    chat_context_cache[chat_id] = {
                        "last_update": datetime.now(),
                        "context": context_analysis,
                        "message_count": len(chat_history)
                    }
                    # Salva anche su disco per persistenza tra riavvii
                    with open(f"data/context_cache_{chat_id}.txt", "w", encoding="utf-8") as f:
                        f.write(context_analysis)
                    print(f"Contesto aggiornato per chat {chat_id}: {context_analysis[:100]}...")
                except Exception as e:
                    print(f"Errore durante l'analisi del contesto per la chat {chat_id}: {e}")
            
            # Dormi per 30 minuti (modificato da 2 minuti)
            time.sleep(1800)
        except Exception as e:
            print(f"Errore nel thread di aggiornamento contesto: {e}")
            time.sleep(30)  # Riprova dopo 30 secondi in caso di errore

# Thread per analizzare il carattere degli utenti periodicamente
def character_analysis_thread():
    """Thread per analizzare il carattere degli utenti ogni 30 minuti"""
    global user_data
    
    print("Avviato thread di analisi del carattere...")
    while True:
        try:
            print("\n--- Analisi periodica del carattere degli utenti ---")
            # Per ogni chat conosciuta
            for chat_id in user_data.keys():
                # Recupera tutti i messaggi della chat
                chat_history = logger.get_chat_message_history(chat_id)
                
                if not chat_history:
                    continue
                
                print(f"Analizzando caratteri nella chat {chat_id} con {len(chat_history)} messaggi...")
                
                # Raggruppa i messaggi per utente
                user_messages = {}
                for msg in chat_history:
                    user_id = msg['user_id']
                    if user_id not in user_messages:
                        user_messages[user_id] = []
                    user_messages[user_id].append(msg['text'])
                
                # Analizza il carattere di ogni utente
                for user_id, messages in user_messages.items():
                    # Verifica che ci siano abbastanza messaggi per l'analisi
                    if len(messages) < 5:
                        continue
                    
                    # Verifica che l'utente sia nel database
                    if user_id not in user_data[chat_id]:
                        continue
                    
                    user_info = user_data[chat_id][user_id]
                    try:
                        print(f"Analisi carattere di {user_info['first_name']} ({len(messages)} messaggi)...")
                        carattere = ai_service.analyze_user_character(messages)
                        if carattere:
                            user_data[chat_id][user_id]['carattere'] = carattere
                            print(f"Carattere aggiornato: {carattere[:50]}...")
                    except Exception as e:
                        print(f"Errore nell'analisi del carattere: {e}")
            
            # Salva i dati dopo l'analisi
            data_manager.save_user_data(user_data)
            
            # Attendi 30 minuti
            print("Analisi completata. Prossima analisi tra 30 minuti.")
            time.sleep(1800)  # 30 minuti in secondi
        except Exception as e:
            print(f"Errore nel thread di analisi del carattere: {e}")
            time.sleep(300)  # 5 minuti in caso di errore

# Avvia il thread per l'aggiornamento del contesto
context_thread = threading.Thread(target=context_update_thread, daemon=True)
context_thread.start()

# Avvia il thread per l'analisi del carattere
character_thread = threading.Thread(target=character_analysis_thread, daemon=True)
character_thread.start()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logger.log_message(message)
    bot.reply_to(message, "Ciao! Sono il tuo bot Telegram alimentato da AI. Menzionami in un gruppo per farmi rispondere!")

@bot.message_handler(commands=['reset'])
def reset_conversation(message):
    logger.log_message(message)
    chat_id = message.chat.id
    if chat_id in conversation_history:
        conversation_history[chat_id] = []
        bot.reply_to(message, "Ho azzerato la memoria della nostra conversazione.")
    else:
        bot.reply_to(message, "Non c'era alcuna conversazione da azzerare.")

@bot.message_handler(commands=['carattere'])
def view_character(message):
    logger.log_message(message)
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Verifica se stiamo rispondendo a qualcuno
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        if chat_id in user_data and target_user_id in user_data[chat_id] and 'carattere' in user_data[chat_id][target_user_id]:
            carattere = user_data[chat_id][target_user_id]['carattere']
            nome = user_data[chat_id][target_user_id]['first_name']
            bot.reply_to(message, f"Il carattere di {nome} che ho rilevato è: {carattere}")
        else:
            bot.reply_to(message, "Non ho ancora analizzato abbastanza messaggi di questo utente per determinarne il carattere.")
    else:
        # Informazioni sul proprio carattere
        if chat_id in user_data and user_id in user_data[chat_id] and 'carattere' in user_data[chat_id][user_id]:
            carattere = user_data[chat_id][user_id]['carattere']
            bot.reply_to(message, f"Il carattere che ho rilevato per te è: {carattere}")
        else:
            bot.reply_to(message, "Non ho ancora analizzato abbastanza tuoi messaggi per determinare il tuo carattere.")

@bot.message_handler(commands=['utenti'])
def list_users(message):
    """Mostra la lista degli utenti che hanno interagito col bot nella chat corrente"""
    logger.log_message(message)
    chat_id = message.chat.id
    
    if chat_id not in user_data or len(user_data[chat_id]) == 0:
        bot.reply_to(message, "Non ho ancora memorizzato alcun utente in questa chat.")
        return
    
    # Crea una lista formattata degli utenti
    user_list = []
    for user_id, info in user_data[chat_id].items():
        user_text = f"• {info['first_name']}"
        
        if info.get('username'):
            user_text += f" (@{info['username']})"
            
        if info.get('carattere'):
            # Limita la descrizione del carattere a una lunghezza ragionevole
            carattere = info['carattere']
            carattere = carattere[:100] + "..." if len(carattere) > 100 else carattere
            user_text += f"\n  Carattere: {carattere}"
        else:
            user_text += "\n  Carattere: non ancora analizzato"
        
        user_list.append(user_text)
    
    # Conta gli utenti e formatta il messaggio
    num_users = len(user_list)
    header = f"🧠 *Utenti memorizzati in questa chat ({num_users}):*\n\n"
    users_text = "\n\n".join(user_list)
    
    # Aggiungi una nota finale
    footer = "\n\nℹ️ Il carattere degli utenti viene aggiornato automaticamente in base ai loro messaggi."
    
    # Invia il messaggio con formattazione Markdown
    try:
        bot.reply_to(message, header + users_text + footer, parse_mode="Markdown")
    except Exception as e:
        # In caso di errore di formattazione, invia senza Markdown
        print(f"Errore nell'invio del messaggio formattato: {e}")
        bot.reply_to(message, "Utenti memorizzati:\n\n" + "\n\n".join(user_list))

@bot.message_handler(commands=['logs'])
def view_logs(message):
    """Mostra gli ultimi log per gli amministratori"""
    logger.log_message(message)
    # Lista degli ID utenti autorizzati a vedere i log
    # Sostituisci con gli ID effettivi
    admin_ids = [12345678, 87654321]
    
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Non sei autorizzato a usare questo comando.")
        return
    
    logs = logger.get_recent_logs(10)
    if not logs:
        bot.reply_to(message, "Nessun log disponibile.")
        return
    
    logs_text = "Ultimi 10 messaggi registrati:\n\n"
    for log in logs:
        logs_text += f"- {log['timestamp']}: {log['user_first_name']} in {log['chat_type']}: {log['text'][:30]}...\n"
    
    bot.reply_to(message, logs_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Log del messaggio ricevuto
        logger.log_message(message)
        
        print(f"\n--- Nuovo messaggio ---")
        print(f"Da: {message.from_user.first_name} ({message.from_user.id})")
        print(f"Chat ID: {message.chat.id}, Tipo: {message.chat.type}")
        print(f"Testo: {message.text if message.text else 'Nessun testo'}")
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Memorizza info utente
        user_info = {
            'id': user_id,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name if message.from_user.last_name else "",
            'username': message.from_user.username if message.from_user.username else ""
        }
        
        # Aggiorna o salva dati utente
        if chat_id not in user_data:
            user_data[chat_id] = {}
        
        # Se l'utente esiste già, preserviamo il carattere esistente
        if user_id in user_data[chat_id] and 'carattere' in user_data[chat_id][user_id]:
            user_info['carattere'] = user_data[chat_id][user_id]['carattere']
        
        # Aggiorniamo i dati dell'utente
        user_data[chat_id][user_id] = user_info
        
        # Recupera la cronologia della conversazione
        if chat_id not in conversation_history:
            conversation_history[chat_id] = []
        
        # Aggiungi il messaggio alla cronologia con info utente
        if message.text:
            user_message = {"role": "user", "content": message.text, "user_info": user_info}
            conversation_history[chat_id].append(user_message)
        
        # Limita la cronologia a 100 messaggi
        if len(conversation_history[chat_id]) > 100:
            conversation_history[chat_id] = conversation_history[chat_id][-100:]
        
        # Lista di parole chiave da monitorare
        keywords = ["gaetano", "gae", "gboipelo"]
        
        # Check if the bot is in a group chat
        if message.chat.type in ["group", "supergroup"] and message.text:
            # Controlla se il messaggio contiene una delle parole chiave (case insensitive)
            lower_text = message.text.lower()
            contains_keyword = any(keyword in lower_text for keyword in keywords)
            
            if contains_keyword:
                print("Parola chiave rilevata! Rispondendo con messaggio speciale...")
                bot.reply_to(message, "Gae scem8")
                return
            
            # Get bot's username
            bot_info = bot.get_me()
            bot_username = bot_info.username
            print(f"Username del bot: {bot_username}")
            
            # Verifica sia per @username che per menzioni dirette
            is_mentioned = False
            if message.text and f"@{bot_username}" in message.text:
                is_mentioned = True
                print("Bot menzionato tramite @username")
            elif message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot.get_me().id:
                is_mentioned = True
                print("Bot menzionato tramite risposta diretta")
                
            if is_mentioned:
                print(f"Bot menzionato! Elaborazione risposta...")
                # Rimuovi la menzione dal prompt
                prompt = message.text.replace(f"@{bot_username}", "").strip() if message.text else ""
                
                # Invia l'azione "sta scrivendo..."
                bot.send_chat_action(message.chat.id, 'typing')
                
                # Recupera la cronologia messaggi dell'intera chat
                print(f"Recupero della cronologia messaggi della chat {message.chat.id}...")
                chat_history = logger.get_chat_message_history(chat_id)
                
                # Usa il contesto memorizzato se disponibile e aggiornato
                cached_context = None
                if chat_id in chat_context_cache:
                    cache_entry = chat_context_cache[chat_id]
                    # Usa la cache se è stata aggiornata negli ultimi 5 minuti
                    if (datetime.now() - cache_entry["last_update"]).total_seconds() < 300:
                        cached_context = cache_entry["context"]
                        print(f"Usando contesto cached (aggiornato {(datetime.now() - cache_entry['last_update']).total_seconds():.1f} secondi fa)")
                
                # Analizza la cronologia per trovare informazioni rilevanti
                print(f"Analisi di {len(chat_history)} messaggi nella chat per contesto...")
                history_analysis = None
                if chat_history and message.text:
                    # Usa il testo del messaggio come argomento corrente
                    history_analysis = ai_service.analyze_message_history(chat_history, prompt)
                    print(f"Contesto rilevante trovato: {history_analysis[:100]}...")
                
                # Combina il contesto memorizzato con l'analisi specifica della query
                combined_context = ""
                if cached_context and cached_context != "Nessuna informazione rilevante trovata.":
                    combined_context += f"CONTESTO GENERALE DELLA CHAT:\n{cached_context}\n\n"
                if history_analysis and history_analysis != "Nessuna informazione rilevante trovata.":
                    combined_context += f"INFORMAZIONI RILEVANTI PER LA DOMANDA ATTUALE:\n{history_analysis}"
                
                # Genera la risposta AI usando la cronologia come contesto aggiuntivo
                response = ai_service.generate_ai_response(prompt if prompt else message.text, chat_id, user_info, combined_context)
                bot.reply_to(message, response)
            else:
                print("Bot non menzionato in questo messaggio")
        elif message.chat.type == "private":
            # In private chats, respond to all messages
            print("Chat privata, rispondo a tutti i messaggi")
            # Invia l'azione "sta scrivendo..."
            bot.send_chat_action(message.chat.id, 'typing')
            
            # Recupera la cronologia messaggi dell'intera chat
            print(f"Recupero della cronologia messaggi della chat {message.chat.id}...")
            chat_history = logger.get_chat_message_history(chat_id)
            
            # Analizza la cronologia per trovare informazioni rilevanti
            print(f"Analisi di {len(chat_history)} messaggi nella chat per contesto...")
            history_analysis = None
            if chat_history and message.text:
                # Usa il testo del messaggio come argomento corrente
                history_analysis = ai_service.analyze_message_history(chat_history, message.text)
                print(f"Contesto rilevante trovato: {history_analysis[:100]}...")
            
            response = ai_service.generate_ai_response(message.text, chat_id, user_info, history_analysis)
            bot.reply_to(message, response)
    except Exception as e:
        print(f"Errore durante l'elaborazione del messaggio: {e}")
        try:
            bot.reply_to(message, "Mi dispiace, c'è stato un problema interno.")
        except:
            pass

if __name__ == '__main__':
    print("Bot avviato con modello AI!")
    print(f"Token del bot configurato: {'Sì' if BOT_TOKEN else 'No'}")
    
    # Forza un salvataggio iniziale dei dati
    data_manager.save_user_data(user_data)
    data_manager.save_conversations(conversation_history)
    
    # Variabili per backoff esponenziale
    retry_count = 0
    max_retries = 10
    base_wait_time = 5
    
    while True:
        try:
            retry_count = 0
            print("Avvio del polling...")
            # Configurazione più robusta del polling (rimosso il parametro allowed_updates)
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except telebot.apihelper.ApiTelegramException as telegram_ex:
            if "Unauthorized" in str(telegram_ex):
                print(f"ERRORE CRITICO: Token non valido o bot disabilitato: {telegram_ex}")
                break  # Esci dal ciclo se il token non è valido
            print(f"Errore API Telegram: {telegram_ex}")
        except requests.exceptions.RequestException as conn_ex:
            print(f"Errore di connessione: {conn_ex}")
        except Exception as e:
            print(f"Errore nel polling: {e}")
            
        # Salvataggio dei dati prima del riavvio
        print("Salvataggio dati in corso...")
        data_manager.save_user_data(user_data)
        data_manager.save_conversations(conversation_history)
        
        # Backoff esponenziale per i tentativi
        retry_count += 1
        if retry_count > max_retries:
            print(f"Troppi tentativi falliti (#{retry_count}). Attendi 2 minuti prima di riprovare.")
            time.sleep(120)
            retry_count = 0
        else:
            wait_time = min(base_wait_time * (2 ** (retry_count - 1)), 60)
            print(f"Tentativo #{retry_count}: riavvio del polling tra {wait_time} secondi...")
            time.sleep(wait_time)