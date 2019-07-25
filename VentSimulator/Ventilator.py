import matplotlib.pyplot as plt
import numpy as np
from VentSimulator.Patient import Patient

class Ventilator:
    from enum import IntEnum, Enum
    parameters = IntEnum('parameters', ['time', 'pressure', 'flow', 'volume', 'p_alv'])
    phase = Enum('phase', ['inspiratory', 'expiratory', 'inspiratory_pause'])
    settings = Enum('settings', ['respiratory_rate', 'peep', 'inspiratory_pause', 'flow', 'rise_time', 
                                 'flow_pattern', 'volume_target', 'pressure_target', 'inspiratory_time'])
    
    CLOSE_ENOUGH = 0.001
    
    global_defaults = {settings.respiratory_rate: 10, 
                       settings.peep: 0, 
                       settings.inspiratory_pause: 0,
                       settings.rise_time: 0}
    mode_defaults = {}
    

    def __init__(self, patient):
        self.patient = None
        self.setOutputLength(10)
        self.current_settings = {}
        
        if patient is None:
            patient = Patient()
        self.patient = patient
        self.patient.veilator = self
        
    def __getitem__(self, key):
        if self.settings[key] in self.current_settings:
            return self.current_settings[self.settings[key]]
        
        if self.settings[key] in self.mode_defaults:
            return self.mode_defaults[self.settings[key]]
        
        return self.global_defaults[self.settings[key]]
    
    def __setitem__(self, key, value):
        self.current_settings[self.settings[key]] = value
        
    def setOutputLength(self, length):
        self.output_length = length
        self.output = np.full((self.output_length, len(self.parameters)), np.nan)
        self.output[0,:] = 0
        
    def simulate(self, time_length, time_step):
        self.setOutputLength(int(np.ceil(1/time_step) + 1) * time_length)
        self.patient.setPeepHint(self['peep'])
        self.record({'pressure': self['peep'], 'p_alv': self['peep']})
    
    def tick(self):
        self.output = np.roll(self.output, 1, axis = 0)
    
    def record(self, values):
        for key in values:
            self.output[0, self.parameters[key] - 1] = values[key]
            
    def data(self, key):
        return np.flip(self.output[:, self.parameters[key] - 1])
    
    def plot(self, keys, axis = None, scalefactor = 1, zeroline = True):
        if isinstance(keys, str):
            keys = [keys]
            
        if axis is None:
            axis = plt.gca()
    
        for key in keys:
            axis.plot(self.data('time'), self.data(key) * scalefactor, label = key)
        axis.legend()
        
        if zeroline:
            axis.axhline(0, color = 'black')
        return axis