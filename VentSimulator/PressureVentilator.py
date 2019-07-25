import numpy as np
from VentSimulator.Ventilator import Ventilator

class PressureVentilator(Ventilator):
    mode_defaults = {Ventilator.settings.pressure_target: 20, 
                     Ventilator.settings.inspiratory_time: 0.8}
    
    def __init__(self, patient = None):
        super().__init__(patient)
    
    def simulate(self, time_length = 60, time_step = 0.02):
        super().simulate(time_length, time_step)

        phase = self.phase.inspiratory
        current_time = 0
        current_volume = 0
        last_breath_start = 0      

        while current_time < time_length:
            self.tick()
            self.record({'time': current_time})

            if phase == self.phase.inspiratory:
                current_flow = ((self['pressure_target'] - self.patient.getPressure()) / self.patient.resistance)
                delta_volume = current_flow * time_step
                self.patient.addVolume(delta_volume)
                current_volume = current_volume + delta_volume
                
                if (current_time - last_breath_start) > self['inspiratory_time']:
                    if self['inspiratory_pause'] > 0:
                        phase = self.phase.inspiratory_pause
                        last_pause_start = current_time
                    else:
                        phase = self.phase.expiratory
                
                self.record({'flow': current_flow,
                             'volume': current_volume,
                             'pressure': self['pressure_target'],
                             'p_alv': self.patient.getPressure()})
            elif phase == self.phase.inspiratory_pause:
                self.record({'flow': 0,
                             'volume': current_volume,
                             'pressure':self.patient.getPressure(),
                             'p_alv': self.patient.getPressure()})
                if current_time > last_pause_start + self['inspiratory_pause']:
                    phase = self.phase.expiratory
            else:
                current_flow = -1 * ((self.patient.getPressure() - self['peep']) / self.patient.resistance)
                delta_volume = current_flow * time_step
                self.patient.addVolume(delta_volume)
                current_volume = current_volume + delta_volume
                
                self.record({'flow': current_flow,
                             'volume': current_volume,
                             'pressure': self['peep'],
                             'p_alv': self.patient.getPressure()}) 
                
                if self['respiratory_rate'] > 0 and ((current_time - last_breath_start) > (60 / self['respiratory_rate'])):
                    phase = self.phase.inspiratory
                    current_volume = 0
                    last_breath_start = current_time
            current_time = current_time + time_step