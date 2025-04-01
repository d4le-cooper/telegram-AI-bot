import os
import telebot
import threading
import time
from datetime import datetime
from config import BOT_TOKEN, SKIP_INITIAL_CHARACTER_ANALYSIS
from logger import MessageLogger
from data_manager import DataManager
from ai_service import AIService

# Initialize components
bot = telebot.TeleBot(BOT_TOKEN)
logger = MessageLogger()
data_manager = DataManager()
ai_service = AIService()

# Stato "cattivo" per ciascuna chat
cattivo_mode = {}

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
users_from_logs = 0
characters_from_logs = 0
log_users = logger.extract_users_from_logs()
log_messages = logger.extract_messages_from_logs()

# Integra gli utenti dai log nella struttura principale
for chat_id, users in log_users.items():
    # Crea la chat se non esiste
    if chat_id not in user_data:
        user_data[chat_id] = {}
        
    for user_id, user_info in users.items():
        users_from_logs += 1
        # Aggiungi l'utente se non esiste
        if user_id not in user_data[chat_id]:
            user_data[chat_id][user_id] = user_info
        
        # Analizza il carattere se ci sono abbastanza messaggi e non è già analizzato
        # E SOLO SE l'analisi iniziale non è disabilitata
        if (not SKIP_INITIAL_CHARACTER_ANALYSIS and
            'carattere' not in user_data[chat_id][user_id] and 
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
    
    if SKIP_INITIAL_CHARACTER_ANALYSIS:
        print("Analisi iniziale dei caratteri disattivata. Prima analisi tra 30 minuti...")
        time.sleep(1800)  # Dormi per 30 minuti prima della prima analisi
    
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

# Log informativo
if SKIP_INITIAL_CHARACTER_ANALYSIS:
    print("Analisi iniziale dei caratteri disattivata - verrà eseguita dopo 30 minuti")
else:
    print("Analisi iniziale dei caratteri attiva")

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

@bot.message_handler(commands=['cattivo'])
def toggle_cattivo_mode(message):
    logger.log_message(message)
    chat_id = message.chat.id
    
    cattivo_mode[chat_id] = not cattivo_mode.get(chat_id, False)
    
    if cattivo_mode[chat_id]:
        bot.reply_to(message, "Modalità cattiva attivata. Ora sarò terribilmente maleducato. 😈")
    else:
        bot.reply_to(message, "Modalità cattiva disattivata. Torno ad essere gentile. 🙂")

@bot.message_handler(commands=['ripara_contesto'])
def repair_context(message):
    """Ripara il contesto della chat per migliorare la distinzione tra messaggi"""
    if message.from_user.id in [7905022928]:  # Sostituisci con l'ID dell'amministratore
        chat_id = message.chat.id
        bot.reply_to(message, "🔄 Rigenerazione del contesto in corso...")
        
        try:
            # Ottieni la cronologia completa
            chat_history = logger.get_chat_message_history(chat_id)
            
            if not chat_history:
                bot.reply_to(message, "❌ Nessuna cronologia disponibile per questa chat")
                return
                
            # Get bot's username
            bot_info = bot.get_me()
            bot_username = f"@{bot_info.username}"
            
            # Rigenerazione del contesto con il nuovo metodo
            context_analysis = ai_service.analyze_chat_context_with_focus(chat_history, bot_username)
            
            # Salva il nuovo contesto
            chat_context_cache[chat_id] = {
                "last_update": datetime.now(),
                "context": context_analysis,
                "message_count": len(chat_history)
            }
            
            # Salva su file
            with open(f"data/context_cache_{chat_id}.txt", "w", encoding="utf-8") as f:
                f.write(context_analysis)
                
            bot.reply_to(message, "✅ Contesto rigenerato con successo!")
            
        except Exception as e:
            bot.reply_to(message, f"❌ Errore durante la rigenerazione: {str(e)}")
    else:
        bot.reply_to(message, "⛔ Solo gli amministratori possono usare questo comando")

@bot.message_handler(commands=['reload_files'])
def reload_files(message):
    """Ricarica i file di intercalari e appellativi"""
    logger.log_message(message)
    
    # Verifica se l'utente è un amministratore
    admin_ids = [7905022928]  # Sostituisci con gli ID degli admin
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Non sei autorizzato a usare questo comando.")
        return
    
    try:
        ai_service.intercalari_cattivo = ai_service._load_data_file("data/intercalari_cattivo.json", [])
        ai_service.intercalari_non_cattivo = ai_service._load_data_file("data/intercalari_non_cattivo.json", [])
        ai_service.appellativi_cattivo = ai_service._load_data_file("data/appellativi_cattivo.json", [])
        ai_service.appellativi_non_cattivo = ai_service._load_data_file("data/appellativi_non_cattivo.json", [])
        
        bot.reply_to(message, "✅ File ricaricati con successo!")
    except Exception as e:
        bot.reply_to(message, f"❌ Errore durante il ricaricamento dei file: {e}")

def send_long_message(chat_id, text, reply_to_message_id=None):
    """Divide messaggi lunghi in parti per rispettare il limite di Telegram"""
    MAX_MESSAGE_LENGTH = 4000  # Usando 4000 invece di 4096 per sicurezza
    
    if len(text) <= MAX_MESSAGE_LENGTH:
        # Messaggio abbastanza corto, invialo normalmente
        return bot.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)
    
    # Dividi il messaggio in parti
    parts = []
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        part = text[i:i + MAX_MESSAGE_LENGTH]
        
        # Se non è la prima parte, cerca di dividere su un punto o uno spazio
        if i > 0:
            # Cerca l'ultimo punto o spazio nella parte
            last_sentence_break = part.rfind('. ')
            last_space = part.rfind(' ')
            
            split_point = max(last_sentence_break, last_space)
            if split_point > MAX_MESSAGE_LENGTH // 2:  # Solo se è abbastanza avanti
                remaining = part[split_point+1:]
                part = part[:split_point+1]
                # Aggiungi il resto alla prossima parte
                text = text[:i] + text[i:i+split_point+1] + text[i+split_point+1:]
        
        parts.append(part)
    
    # Invia ogni parte, numerandola
    total_parts = len(parts)
    last_message = None
    
    for idx, part in enumerate(parts):
        if total_parts > 1:
            part_header = f"[Parte {idx+1}/{total_parts}]\n\n"
            message_text = part_header + part
        else:
            message_text = part
        
        # Solo il primo messaggio risponde al messaggio originale
        if idx == 0 and reply_to_message_id:
            last_message = bot.send_message(chat_id, message_text, reply_to_message_id=reply_to_message_id)
        else:
            last_message = bot.send_message(chat_id, message_text)
    
    return last_message

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
        
        # Aggiorna o salva dati utente e conversazione come prima
        user_info = {
            'id': user_id,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name if message.from_user.last_name else "",
            'username': message.from_user.username if message.from_user.username else ""
        }
        
        if chat_id not in user_data:
            user_data[chat_id] = {}
        
        if user_id in user_data[chat_id] and 'carattere' in user_data[chat_id][user_id]:
            user_info['carattere'] = user_data[chat_id][user_id]['carattere']
        
        user_data[chat_id][user_id] = user_info
        
        if chat_id not in conversation_history:
            conversation_history[chat_id] = []
        
        if message.text:
            user_message = {"role": "user", "content": message.text, "user_info": user_info}
            conversation_history[chat_id].append(user_message)
        
        if len(conversation_history[chat_id]) > 100:
            conversation_history[chat_id] = conversation_history[chat_id][-100:]
        
        # Get bot's username
        bot_info = bot.get_me()
        bot_username = f"@{bot_info.username}"
        
        # Determina se il messaggio è diretto al bot
        is_directed_to_bot = (
            message.chat.type == "private" or
            (message.text and bot_username in message.text) or
            (message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id)
        )
        
        # Continua solo se il messaggio è diretto al bot
        if is_directed_to_bot and message.text:
            # Rimuovi il nome del bot dal messaggio se presente
            clean_message = message.text.replace(bot_username, "").strip()
            if not clean_message:
                clean_message = message.text
            
            # Ottieni informazioni di contesto
            chat_history = []
            history_analysis = "Nessuna informazione rilevante trovata."
            
            # Scegli il metodo appropriato per ottenere il contesto
            if chat_id in chat_context_cache:
                history_analysis = chat_context_cache[chat_id]["context"]
                print(f"Usando contesto memorizzato: {history_analysis[:50]}...")
            else:
                chat_history = logger.get_chat_message_history(chat_id)
                if chat_history:
                    # Usa il metodo che chiaramente distingue messaggi per il bot
                    history_analysis = ai_service.analyze_message_history_with_focus(
                        chat_history, clean_message, bot_username
                    )
                    print(f"Contesto rilevante trovato: {history_analysis[:100]}...")
            
            response = ai_service.generate_ai_response(
                clean_message,
                chat_id, 
                user_info, 
                history_analysis,
                is_directed=True,  # Parametro nuovo
                is_cattivo=cattivo_mode.get(chat_id, False)
            )
            
            # Usa la nuova funzione per inviare messaggi lunghi
            send_long_message(chat_id, response, message.message_id)
            
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