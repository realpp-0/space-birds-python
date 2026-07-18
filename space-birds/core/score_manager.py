

class ScoreManager:
    
    def __init__(self):
        self.score = 0

    def add_score(self, points):
        self.score += points

    def reset_score(self):
        self.score = 0

    def get_score(self):
        return self.score