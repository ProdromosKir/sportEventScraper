class Event():
    def __init__(self):
        self.time = None
        self.channel = None
        self.channel_name = None
        self.participants = None
        self.competition = None
        self.image_path = None

    def __repr__(self):
        return f'\n{self.time} {self.channel} \n {self.participants}\n {self.competition}'

   