import telebot
from telebot.apihelper import ApiTelegramException
import os
import re
import string
from thefuzz import fuzz
from chat import Chat
from lang import Lang
import string
import time
import json

from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
# next to add: EN_US, RU_UR, RU_UK, RU_BR

bot = telebot.TeleBot(SECRET_KEY)

chats = {}
if not os.path.exists("chats/"):
	os.mkdir("chats/")
if not os.path.exists("langs/"):
	os.mkdir("langs")

langs = {}
if not os.path.exists("langs/en_us.json"):
	langs["en_us"] = Lang.create_locale(
		"en_us",
		{
			"help_info": """Bot commands: 
/help - get a list of commands 
/word add/remove <word> - add a word/remove a word 
\t\t\t\t\t or list - get a list of words
""",
			"no_perms": "You do not have permission to run this command.",
			"arg_tip0": "Use add, remove or list.",
			"arg_tip1": "/word add <word>",
			"arg_tip2": "/word remove <word>",
			"word_add": "Word %s successful added",
			"word_remove": "Word %s successful removed",
			"list_line": "List of forbidden words in this chat:",
			"donate_msg": "You can support the author with money here:\nhttps://boosty.to/author_gmp14",
			"delete_fail": "I can't delete a message, make sure the bot has the \"Delete messages\" right",
			"lang_help": "/lang <support lang>\n/lang list - for list supported langs",
			"lang_list_part": "List of supported languages:",
			"lang_not_exists": "Lang %s not supported",
			"lang_setted": "Lang %s successful setted"
		}
	)

with os.scandir("langs/") as entries:
	for entry in entries:
		if not entry.is_file():
			continue
		langs[entry.name.lower().split(".")[0]] = Lang.get_locale(entry.name.lower().split(".")[0])

chats_settings = {
	"default": {
		"lang": "en_us"
	}
}
if os.path.exists("chats_settings.json"):
	chats_settings = json.load(open("chats_settings.json", "r"))
else:
	json.dump(chats_settings, open("chats_settings.json", "w"), indent="\t")

def update_data(chat, key, value):
	global chats_settings
	if chats_settings.get(chat, None) == None:
		chats_settings[chat] = {}
	chats_settings[chat][key] = value 
	json.dump(chats_settings, open("chats_settings.json", "w"), indent="\t")

def compare(v0, v1):
	if v0.lower() == v1.lower():
		return True
	return False

def exists_in(dictionary, string):
	for k, v in dictionary.items():
		if compare(k, string):
			return True
	return False

exceptions = []
user_last_message = {}
def _to_cyrillic(text: str) -> str:
	translit_dict = {
		'shch': 'щ', 'sch': 'щ', 'ch': 'ч', 'sh': 'ш', 'zh': 'ж',
		'yu': 'ю', 'ya': 'я', 'yo': 'ё', 'ts': 'ц', 'ii': 'ий', 'iy': 'ий',
		'a': 'а', 'b': 'б', 'c': 'ц', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г',
		'h': 'х', 'i': 'и', 'j': 'й', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н',
		'o': 'о', 'p': 'п', 'q': 'к', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у',
		'v': 'в', 'w': 'в', 'x': 'кс', 'y': 'ы', 'z': 'з',
		"'": 'ь', "''": 'ъ', '`': 'ь', '``': 'ъ'}
	
	text = text.lower()
	for key in sorted(translit_dict.keys(), key=len, reverse=True):
		text = text.replace(key, translit_dict[key])
	return text

def fuzzy_search(
	search_word: str,
	sentence: str,
	threshold: int = 70,
	method: str = "word",
	ignore_case: bool = True,
	support_translit: bool = False) -> bool:

	global exceptions

	if support_translit:
		search_word = _to_cyrillic(search_word)
		sentence = _to_cyrillic(sentence)
		ignore_case = True

	if ignore_case:
		search_word = search_word.lower()
		sentence_clean = sentence.lower()
	else:
		sentence_clean = sentence

	translator = str.maketrans('', '', string.punctuation)
	sentence_clean = sentence_clean.translate(translator)

	if method == "word":
		words = re.split(r'\s+', sentence_clean)
		for word in words:
			if fuzz.ratio(search_word, word) >= threshold:
				#if not word in exceptions:
				return True
		return False

	elif method == "substring":
		return fuzz.partial_ratio(search_word, sentence_clean) >= threshold

	else:
		raise ValueError("Unavailable search method. Use 'word' or 'substring'")

def get_args(input_string: str) -> list:
	parts = input_string.split()

	if len(parts) < 2:
		return []

	return parts[1:]
def get_cmd(input_string: str) -> list:
	parts = input_string.split()
	if len(parts) < 1:
		return []
	return parts[0]

def readFile(filename):
	lines = []
	if not os.path.exists(filename):
		open(filename, 'w')
		return
	with open(filename, 'r') as f:
		for line in f: lines.append(line.replace('\n', ''))
	return lines

def get_chat(id):
	global chats
	if id in chats: return chats.get(id)
def append_chat(id):
	global chats
	filename = f"chats/{id}.txt"
	chat = Chat(readFile(filename), filename)
	chats[id] = chat
	return chat
def GorL_chat(chat_id):
	if chat_id in chats:
		return chats.get(chat_id)
	return append_chat(chat_id)

def get_chat_settings(chat_id):
	global chats_settings
	chat_id = str(chat_id)
	return chats_settings.get(chat_id, chats_settings["default"])
def get_lang(name):
	global langs
	return langs.get(name.lower(), langs["en_us"])
def get_chat_lang(chat_id):
	settings = get_chat_settings(chat_id)
	return get_lang(settings["lang"])

def check_admin(msg):
	user_status = bot.get_chat_member(msg.chat.id, msg.from_user.id).status
	if user_status == 'administrator':
		return True
	elif user_status == 'creator':
		return True
	else:
		return False

@bot.message_handler(commands=['help'])
def help_cmd(cmd):
	bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("help_info"))

@bot.message_handler(commands=['word'])
def word_cmd(cmd):
	chat = GorL_chat(cmd.chat.id)
	user_status = bot.get_chat_member(cmd.chat.id, cmd.from_user.id).status
	if check_admin(cmd) == False:
		bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("no_perms"))
		return

	args = get_args(cmd.text)
	if len(args) < 1:
		bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("arg_tip0"))
		return

	if args[0] == "add":
		if len(args) < 2:
			bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("arg_tip1"))
			return
		chat.addWord(args[1])
		bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("word_add").replace("%s", args[1]))

	elif args[0] == 'remove':
		if len(args) < 2:
			bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("arg_tip2"))
			return
		chat.removeWord(args[1])
		bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("word_remove").replace("%s", args[1]))

	elif args[0] == 'list':
		text = get_chat_lang(cmd.chat.id).get("list_line")+"\n"
		num = 0
		for word in chat.getWords():
			num  += 1
			text += f"{num}. {word}\n"
		bot.reply_to(cmd, text)

@bot.message_handler(commands=['donate'])
def donate_cmd(c):
	bot.reply_to(c, get_chat_lang(c.chat.id).get("donate_msg"))

@bot.message_handler(commands=['lang'])
def lang_cmd(cmd):
	global langs
	local_lang = get_chat_lang(cmd.chat.id)

	if check_admin(cmd) == False:
		bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("no_perms"))
		return
	
	args = get_args(cmd.text)
	if len(args) < 1:
		bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("lang_help"))
		return
	
	if args[0] == "list":
		text = get_chat_lang(cmd.chat.id).get("lang_list_part")+"\n"
		i = 0
		for name, lang in langs.items():
			i += 1
			text += f"{i}. {name}\n"

		bot.reply_to(cmd, text)
		return

	if not exists_in(langs, args[0]):
		bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("lang_not_exists").replace("%s", args[0]))
		return

	update_data(cmd.chat.id, "lang", args[0].lower())
	bot.reply_to(cmd, get_chat_lang(cmd.chat.id).get("lang_setted").replace("%s", args[0]))

@bot.message_handler(content_types=['text'])
def msg_hndr(msg):
	#handle_message_spam(msg)
	chat = GorL_chat(msg.chat.id)
	for word in chat.getWords():
		if (fuzzy_search(str(word), str(msg.text).replace(" ", ""), threshold=90, support_translit=True)):# or is_spam(msg.from_user.id)):
			username = msg.from_user.username
			chat_id = msg.chat.id
			try:
				bot.delete_message(msg.chat.id, msg.id)
				#bot.send_message(chat_id, username+" использовал запрешённое слово")
			except ApiTelegramException:
				bot.reply_to(msg, get_chat_lang(msg.chat.id).get("delete_fail"))
			return

def main(): bot.polling(none_stop=True, interval=0)
if __name__ == "__main__": main()