import numpy as np
import matplotlib.pyplot as plt
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
                current_flow = (((self['pressure_target'] + self['peep']) - self.patient.getPressure()) / self.patient.resistance)
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
                             'pressure': self['pressure_target'] + self['peep'],
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
    def interactive_shim(self, pressure_target, inspiratory_time, peep, respiratory_rate, 
        inspiratory_pause, resistance, compliance):
        self['pressure_target'] = pressure_target
        self['inspiratory_time'] = inspiratory_time
        self['peep'] = peep
        self['respiratory_rate'] = respiratory_rate
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
        ax3.set_ylim(0, 1000)

    def interact(self):
        import ipywidgets as widgets
        import IPython.display

        pressure_target_widget = widgets.IntSlider(
            value = self['pressure_target'],
            min = 1,
            max = 40,
            step = 1,
            continuous_update = False,
            description = "PC")

        inspiratory_time_widget = widgets.FloatSlider(
            value = self['inspiratory_time'],
            min = 0,
            max = 2,
            step = 0.05,
            continuous_update = False,
            description = "Ti   "
        )

        peep_widget = widgets.IntSlider(
            value = self['peep'],
            min = 0,
            max = 20,
            step = 1,
            continuous_update = False,
            description = "PEEP"
        )


        respiratory_rate_widget = widgets.IntSlider(
            value = self['respiratory_rate'],
            min = 0,
            max = 60,
            step = 1,
            continuous_update = False,
            description = "RR"
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

        vent_ui = widgets.VBox([pressure_target_widget, inspiratory_time_widget, peep_widget, respiratory_rate_widget])
        patient_ui = widgets.VBox([resistance_widget, compliance_widget])
        ui = widgets.HBox([vent_ui, patient_ui])

        output = widgets.interactive_output(self.interactive_shim, 
        {'pressure_target': pressure_target_widget,
            'peep': peep_widget,
            'inspiratory_time': inspiratory_time_widget,
            'respiratory_rate': respiratory_rate_widget,
            'inspiratory_pause': widgets.fixed(0),
            'resistance': resistance_widget,
            'compliance': compliance_widget})

        return IPython.display.display(ui, output)