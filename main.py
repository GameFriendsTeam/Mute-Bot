import telebot
from telebot.apihelper import ApiTelegramException
import os
import re
import string
from thefuzz import fuzz
from chat import Chat
import string
from thefuzz import fuzz
import time

from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
# next to add: EN_US, RU_UR, RU_UK, RU_BR

bot = telebot.TeleBot(SECRET_KEY)

chats = {}
if not os.path.exists("chats/"):
	os.mkdir("chats/")

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
		raise ValueError("Недопустимый метод поиска. Используйте 'word' или 'substring'")

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
		for line in f:
			lines.append(line.replace('\n', ''))
	return lines

def get_chat(id):
	global chats
	if id in chats:
		return chats.get(id)
def append_chat(id):
	global chats
	filename = f"chats/{id}.txt"
	words = readFile(filename)
	chat = Chat(words, filename)
	chats[id] = chat
	return chat

def GorL_chat(id):
	if id in chats:
		return chats.get(id)
	else:
		return append_chat(id)

def main():
	bot.polling(none_stop=True, interval=0)

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
	bot.reply_to(cmd, """Команды бота:
/help - получить список команд
/word add/remove <word> - добавление слова/удаление слова
\t\t\t\t\t  или list - получить список слов""")

@bot.message_handler(commands=['word'])
def word_cmd(cmd):
	chat = GorL_chat(cmd.chat.id)
	user_status = bot.get_chat_member(cmd.chat.id, cmd.from_user.id).status
	if check_admin(cmd) == False:
		bot.reply_to(cmd, "У вас нет прав для этой команды.")
		return

	args = get_args(cmd.text)
	if len(args) < 1:
		bot.reply_to(cmd, "Используйте add, remove или list.")
		return

	if args[0] == "add":
		if len(args) < 2:
			bot.reply_to(cmd, "/word add <слово>")
			return
		chat.addWord(args[1])
		bot.reply_to(cmd, "Слово "+args[1]+" добавлено в чёрный список.")

	elif args[0] == 'remove':
		if len(args) < 2:
			bot.reply_to(cmd, "/word remove <слово>")
			return
		chat.removeWord(args[1])
		bot.reply_to(cmd, "Слово "+args[1]+" удалено из чёрного списока.")

	elif args[0] == 'list':
		text = "Вот список запрещённых слов для этого чата:\n"
		num = 0
		for word in chat.getWords():
			num  += 1
			text += f"{num}. {word}\n"
		bot.reply_to(cmd, text)

@bot.message_handler(commands=['donate'])
def donate_cmd(c):
	bot.reply_to(c, "Ты можешь поддержать автора денежкой тут:\nhttps://boosty.to/author_gmp14")

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
				bot.reply_to(msg, "Не могу удалить сообщение, убедитесь что у бота есть право \"Удаление сообщений\"")
			return

if __name__ == "__main__":

	main()
