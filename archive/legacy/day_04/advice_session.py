class AdviceSession:
	"""
	Purpose: Manage advice dialog state.
	"""

	def __init__(self):
		self.is_active = False
		self.topic = None
		self.question_count = 0
		self.max_questions = 5
		self.user_responses = []

	def start(self, topic: str):
		self.is_active = True
		self.topic = topic
		self.question_count = 0
		self.user_responses = []

	def end(self):
		self.is_active = False

	def add_response(self, text: str):
		self.user_responses.append(text)

	def increment_question_count(self):
		self.question_count += 1

	def can_ask_more_questions(self) -> bool:
		return self.question_count < self.max_questions

	def get_context_for_model(self) -> dict:
		return {
			"topic": self.topic or "",
			"question_count": str(self.question_count),
			"max_questions": str(self.max_questions),
			"user_responses": " | ".join(self.user_responses),
		}

	def get_session_summary(self) -> str:
		return f"Тема: {self.topic}, вопросов: {self.question_count}/{self.max_questions}"


