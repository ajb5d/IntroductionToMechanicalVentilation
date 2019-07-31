import numpy as np
import matplotlib.pyplot as plt
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
    
    def interactive_shim(self, volume_target, peep, flow, respiratory_rate, flow_pattern, 
        rise_time, inspiratory_pause, resistance, compliance):
        self['volume_target'] = volume_target
        self['peep'] = peep
        self['flow'] = flow
        self['respiratory_rate'] = respiratory_rate
        self['flow_pattern'] = flow_pattern
        self['rise_time'] = rise_time
        self['inspiratory_pause'] = inspiratory_pause
        self.patient.resistance = resistance
        self.patient.compliance = compliance

        self.simulate(12)

        f, (ax1,ax2,ax3) = plt.subplots(3,1,figsize=(12, 12))
        ax1.set_ylim(0,50)
        self.plot(['pressure', 'p_alv'], ax1)
        self.plot('flow', ax2, scalefactor = 60)
        ax2.set_ylim(-120, 120)
        self.plot('volume', ax3, scalefactor = 1000)

    def interact(self):
        import ipywidgets as widgets
        import IPython.display

        volume_target_widget = widgets.FloatSlider(
            value = self['volume_target'],
            min = 0.1,
            max = 2.0,
            step = 0.05,
            continuous_update = False,
            description = "Vt")

        peep_widget = widgets.IntSlider(
            value = self['peep'],
            min = 0,
            max = 20,
            step = 1,
            continuous_update = False,
            description = "PEEP"
        )

        flow_widget = widgets.FloatSlider(
            value = self['flow'],
            min = 0,
            max = 2,
            step = 0.05,
            continuous_update = False,
            description = "Flow"
        )
        respiratory_rate_widget = widgets.IntSlider(
            value = self['respiratory_rate'],
            min = 0,
            max = 60,
            step = 1,
            continuous_update = False,
            description = "RR"
        )

        flow_pattern_widget = widgets.Dropdown(
            options = [(x.name.title(), x) for x in self.flow_patterns],
            value = self.flow_patterns.square,
            description = "Flow Pattern"
        )

        resistance_widget = widgets.FloatSlider(
            value = self.patient.resistance,
            min = 1, 
            max = 50,
            step = 1,
            continuous_update = False,
            description = "Resistance"
        )

        compliance_widget = widgets.FloatLogSlider(
            value = self.patient.compliance,
            min = -2, 
            max = -1,
            base = 10, 
            step = 0.01,
            continuous_update = False,
            description = "Compliance"
        )

        vent_ui = widgets.VBox([volume_target_widget, peep_widget, flow_widget, respiratory_rate_widget, flow_pattern_widget])
        patient_ui = widgets.VBox([resistance_widget, compliance_widget])
        ui = widgets.HBox([vent_ui, patient_ui])

        output = widgets.interactive_output(self.interactive_shim, 
        {'volume_target': volume_target_widget,
            'peep': peep_widget,
            'flow': flow_widget,
            'respiratory_rate': respiratory_rate_widget,
            'rise_time': widgets.fixed(0),
            'inspiratory_pause': widgets.fixed(0),
            'flow_pattern': flow_pattern_widget,
            'resistance': resistance_widget,
            'compliance': compliance_widget})

        return IPython.display.display(ui, output)