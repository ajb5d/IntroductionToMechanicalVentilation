class Patient:
    def __init__(self):
        self.volume = 0
        self.compliance = 0.05
        self.resistance = 10
        self.ventilator = None
        
    def setPeepHint(self, peep):
        self.volume = self.compliance * peep
        
    def addVolume(self, deltaVolume):
        self.volume = self.volume + deltaVolume
        
    def getPressure(self):
        return self.volume / self.compliance