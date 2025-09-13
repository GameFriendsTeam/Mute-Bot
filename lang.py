import json, os

class Lang:
	def __init__(self, filepath, lang_name):
		self._file = filepath
		self._lang = lang_name

		self.load()

	def get_name(self):
		return self._lang

	def load(self):
		self.texts = {}
		
		with open(self._file, 'r') as f:
			self.texts = json.load(f)
		if len(self.texts) < 1:
			raise ValueError("locale is empty")

	def get(self, key):
		return self.texts.get(key, None)

	@staticmethod
	def create_locale(lang_name, texts):
		filepath = f'langs/{lang_name}.json'

		with open(filepath, 'w+') as f:
			json.dump(texts, f, indent="\t")

		return Lang(filepath, lang_name)

	@staticmethod
	def get_locale(lang_name):
		filepath = f'langs/{lang_name}.json'

		if not os.path.exists(filepath):
			return None

		return Lang(filepath, lang_name)