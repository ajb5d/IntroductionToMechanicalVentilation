import numpy as np
from VentSimulator.Ventilator import Ventilator


class VolumeVentilator(Ventilator):
    from enum import Enum
    flow_patterns = Enum('flowPatterns', ['square', 'decelerating'])
    mode_defaults = {Ventilator.settings.flow: 1, 
                     Ventilator.settings.volume_target: 0.5, 
                     Ventilator.settings.flow_pattern: flow_patterns.square}
    
    def __init__(self, patient = None):
        super().__init__(patient)
        
    def setupInspiratoryFlow(self, time_step):        
        if self['flow_pattern'] == self.flow_patterns.decelerating:
            rise_time_steps = int(np.ceil(self['rise_time'] / time_step))
            rise_time_flow = np.linspace(0, 2, num = rise_time_steps) * self['flow']
            rise_time_volume = np.sum(rise_time_flow * time_step)
        
            planned_inspiratory_time = (self['volume_target'] - rise_time_volume) / self['flow']
            total_time_steps = int(np.ceil(planned_inspiratory_time / time_step))
            
            return np.append(rise_time_flow, np.linspace(2, 0, num = total_time_steps) * self['flow'])
        
        rise_time_steps = int(np.ceil(self['rise_time'] / time_step))
        rise_time_flow = np.linspace(0, 1, num = rise_time_steps) * self['flow']
        return np.append(rise_time_flow, self['flow'])
        
    def simulate(self, time_length = 60, time_step = 0.02):
        super().simulate(time_length, time_step)

        phase = self.phase.inspiratory
        current_time = 0
        current_volume = 0
        last_breath_start = 0
        last_pause_start = 0
        
        flow = self.setupInspiratoryFlow(time_step)

        while current_time < time_length:
            self.tick()
            self.record({'time': current_time})

            if phase == self.phase.inspiratory:
                current_flow = flow[0]
                if(len(flow) > 1):
                    flow = flow[1:]
                
                delta_volume = current_flow * time_step
                self.patient.addVolume(delta_volume)
                current_volume = current_volume + delta_volume
                
                if (self['volume_target'] - current_volume) < self.CLOSE_ENOUGH:
                    if self['inspiratory_pause'] > 0:
                        phase = self.phase.inspiratory_pause
                        last_pause_start = current_time
                    else:
                        phase = self.phase.expiratory
                        
                self.record({'flow': current_flow,
                             'volume': current_volume,
                             'pressure': current_flow * self.patient.resistance + self.patient.getPressure(),
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
                
                if self['respiratory_rate'] > 0 and (current_time - last_breath_start) > (60 / self['respiratory_rate']):
                    phase = self.phase.inspiratory
                    current_volume = 0
                    last_breath_start = current_time
                    flow = self.setupInspiratoryFlow(time_step)
            current_time = current_time + time_step