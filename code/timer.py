import  pygame
class Timer():
    def __init__(self, length):
        self.length = length
        self.elapsed = 0
        self.current_time = 0
        self.active = False
    def activate(self):
        self.active = True
        self.current_time = pygame.time.get_ticks()
    def update(self):
        if self.active:
            self.elapsed = pygame.time.get_ticks() - self.current_time
            if self.elapsed > self.length:
                self.elapsed = 0
                self.active = False