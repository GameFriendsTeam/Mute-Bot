import os

class Chat:
	def __init__(self, words, filepath):
		self._words = words
		if self._words == None:
			self._words = []
		self._file = filepath
	
	def getWords(self):
		if len(self._words) > 0:
			return self._words
		else:
			return []

	def _file_CAC(self):
		if os.path.exists(self._file):
			return
		open(self._file, 'w')

	def readFile(self):
		lines = []
		self._file_CAC()
		with open(self._file, 'r') as f:
			for line in f:
				lines.append(line.replace('\n', ''))
		return lines
	
	def addWord(self, word):
		if word not in self._words:
			self._words.append(word)
			self._file_CAC()
			with open(self._file, 'a') as f:
				f.write(word+"\n")

	def removeWord(self, word):
		if word in self._words:
			self._words.remove(word)
			self._file_CAC()
		lines = self.readFile()
		if word in lines:
			lines.remove(word)
		with open(self._file, 'w') as f:
			for line in lines:
				f.write(line+"\n")
