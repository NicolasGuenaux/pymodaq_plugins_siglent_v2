import pyvisa
import time as t

serial_address = 'USB0::0xF4EC::0x1102::SDG7ABAD7R0103::INSTR'
rm = pyvisa.ResourceManager()
global siglent
siglent = rm.open_resource(serial_address)

class ActuatorWrapper:
    """
    Attributes:
    -----------
    burst: string
        Burst operating mode, either "ON" or "OFF"

    load: string
        Impedance load, "50" to "100000" Ohm or "HiZ"

    amplitude: float
        Amplitude of the signal, in V
    
    offset: float
        Offset of the signal, in V

    phase: float
        Phase of the signal, in degrees °

    frequency: float   
        Frequency of the signal, in Hz

    cycles: int
        Number of repetition of the burst original signal, only available in "BURST" mode

    trig_src: string
        Trigger source, either "EXT", "INT" or "MAN", only available in "BURST" mode

    delay: float
        Trigger delay, in s (min value is 2.494us and it is not stable when set too high (like 1ms))
    
    wavetype: string
        Wavetype of the signal, either "SINE", "SQUARE", "RAMP", "DC" or "ARB"
        "ARB" as in arbitrary waveform which is sent via EasyWaveX and cannot originate from here

    file: string
        wavefile name, registered locally and available in "ARB" mode.

    axis: string
        Parameter on which the scans will be performed, either "Amplitude"
        or "Phase" for now

    channel: string
        The output channel, "CH1" by default

    state: string
        Either "ON" or "OFF"
    """

    # units = 'V or °'
    global siglent

    def __init__(self):

        siglent.write("C1:OUTP LOAD,50")
        siglent.write("C1:BTWV STATE,ON")
        siglent.write("C1:BTWV TRSR,EXT")
        siglent.write("C1:BSWV WVTP,SINE")
        siglent.write("C1:BSWV FRQ,10000000")
        siglent.write("C1:BSWV AMP,3")
        siglent.write("C1:BSWV PHSE,0")
        siglent.write("C1:BTWV DLAY,0.000005")
        siglent.write("C1:BTWV TIME,1")
        siglent.write("C1:OUTP ON")

        self.address = serial_address
        self.burst = "ON"
        self.amplitude = 3
        self.offset = 0
        self.phase = 0
        self.frequency = 10000000
        self.delay = 0.000005
        self.cycles = 1
        self.trig_src = "EXT"
        self.wavetype = "SINE"
        self.axis = "Amplitude"
        self.channel = "C1"
        self.state = "OFF"
        self.unit = 'V'

        # self.set_rel_amplitude(1)
        # self.set_rel_amplitude(-1)

    def open_communication(self):
        return True
    
    def get_amplitude(self):
        print("in get_amplitude")
        answer = siglent.query(self.channel + ":BSWV?")
        print("answer = ", answer)
        amplitude = answer.split(',')[7]    # The 7th word corresponds to the amp
        amplitude = float(amplitude[:-1])   # We skip the 'V' at the end
        print("amplitude =", amplitude)
        self.amplitude = amplitude
        return(self.amplitude)

    
    def get_phase(self):
        print("in get_phase")
        answer = siglent.query(self.channel + ":BSWV?")
        print("answer = ", answer)
        wtype = self.get_wavetype()
        if (wtype == "RAMP") or (wtype == "SQUARE"):
            phase = answer.split(',')[-3]   # The 3rd to last word corresponds to the phase
            phase = float(phase)
        else:
            phase = answer.split(',')[-1]   # The last word corresponds to the phase
            phase = float(phase[:-1])       # We get rid of the '\n' at the end
        self.phase = phase
        print("phase =", self.phase)
        return(self.phase)

    def set_burst(self, mode):
        """Sets the burst parameter "ON" or "OFF" """
        siglent.write(self.channel + ":BTWV STATE," + mode)
        self.mode = mode

    def get_burst_state(self):
        answer = siglent.query(self.channel + ":BTWV?")
        state = answer.split(',')[1]
        self.burst = state
        return(self.burst)
    
    def set_amplitude(self, amp):
        """Sets the amplitude to amp, in V"""
        siglent.write(self.channel + ":BSWV AMP," + str(amp))
        self.amplitude = amp

    def set_rel_amplitude(self, rel_amp):
        """Sets the amplitude to amp + rel_amp, in V"""
        amp = self.get_amplitude()
        # siglent.write(self.channel + ":BSWV AMP," + str(amp + rel_amp))
        new_amp = amp + rel_amp
        self.set_amplitude(new_amp)
        self.amplitude = new_amp
        return

    def set_phase(self, phi):
        """Sets the phase to phi, in degrees"""
        siglent.write(self.channel + ":BSWV PHSE," + str(phi))
        self.phase = phi
        return

    def set_rel_phase(self, rel_phi):
        """Sets the phase to phi + rel_phi, in degrees"""
        phi = self.get_phase
        siglent.write(self.channel + ":BSWV PHSE," + str(phi + rel_phi))
        self.phase = phi + rel_phi

    def set_offset(self, ofst):
        """Sets the amplitude offset to ofst, in V"""
        siglent.write(self.channel + ":BSWV OFST," + str(ofst))
        self.offset = ofst

    def get_offset(self, DC=False):
        answer = siglent.query("C1:BSWV?")
        if DC:
            ofst = answer.split(',')[7]
            ofst = float(ofst[:-2])         # We skip the 'V' & \n at the end
        else:
            ofst = answer.split(',')[17]    # the 18th word corresponds to the ofst
            ofst = float(ofst[:-1])         # We skip the 'V' at the end
        self.offset = ofst
        return self.offset

    def set_axis(self, axis):
        self.axis = axis

    def set_unit(self):
        axis = self.axis
        if axis == 'Amplitude':
            self.unit = 'V'
        elif axis == 'Phase':
            self.unit = 'deg'
        elif axis == 'Frequency':
            self.unit = 'Hz'
        else:  # axis == 'Delay'
            self.unit = 's'

    def get_unit(self):
        unit = self.unit
        return unit

    def set_pos(self, pos):
        if self.axis == "Amplitude":
            return(self.set_amplitude(pos))
        elif self.axis == "Phase":
            return(self.set_phase(pos))
        elif self.axis == "Frequency":
            return(self.set_frequency(pos))
        elif self.axis == "Delay":
            return(self.set_delay(pos))

    def get_pos(self):
        if self.axis == "Amplitude":
            return(self.get_amplitude())
        elif self.axis == "Phase":
            return(self.get_phase())
        elif self.axis == "Frequency":
            return(self.get_frequency())
        elif self.axis == "Delay":
            return(self.get_delay())

    def set_rel_pos(self, pos):
        if self.axis == "Amplitude":
            return(self.set_rel_amplitude(pos))
        elif self.axis == "Phase":
            return(self.set_rel_phase(pos))
        elif self.axis == "Frequency":
            return(self.set_rel_frequency(pos))
        elif self.axis == "Delay":
            return(self.set_rel_delay(pos))

    def set_wavetype(self, wtype):
        self.wavetype = wtype
        siglent.write(self.channel + ":BSWV WVTP," + wtype)

    def get_wavetype(self):
        return(self.wavetype)
    
    def set_load(self, load):
        """Sets the load to "HiZ" (ie High Z) or "50" to "100000" Ohm """
        siglent.write(self.channel + ":OUTP LOAD," + load)
        self.load = load

    def get_load(self):
        return(self.load)
    
    def set_trig_src(self, source):
        """Sets the trigger source, either "EXT", "INT" or "MAN"
            only available when burst mode is on"""
        siglent.write(self.channel + ":BTWV TRSR," + source)
        self.trig_src = source
    
    def get_trig_src(self):
        return(self.trig_src)
    
    def set_frequency(self, freq):
        """sets the basewave frequency, in Hz"""
        siglent.write(self.channel + ":BSWV FRQ," + str(freq))
        self.frequency = freq

    def set_rel_frequency(self, freq):
        """Sets the delay, in s, only available in BTWV ext trigger mode"""
        freq0 = self.frequency
        self.set_frequency(freq0 + freq)
        self.frequency = freq0 + freq
    
    def get_frequency(self):
        print("in get_frequency")
        answer = siglent.query("C1:BSWV?")
        print("answer = ", answer)
        freq = answer.split(",")[3]
        freq = float(freq[:-2])         # get rid of the "HZ" at the end
        self.frequency = freq
        print("frequency =", freq)
        return(self.frequency)
    
    def set_delay(self, time):
        """Sets the delay, in s, only available in BTWV ext trigger mode"""
        siglent.write(self.channel + ":BTWV DLAY," + str(time))
        self.delay = time

    def set_rel_delay(self, time):
        """Sets the delay, in s, only available in BTWV ext trigger mode"""
        dlay = self.delay
        self.set_delay(dlay + time)
        self.delay = time + dlay

    def get_delay(self):
        print("in get_delay")
        print("delay =", self.delay)
        return(self.delay)
    
    def set_cycles(self, n):
        """Sets the number of repetition of the basewave in the burst, int"""
        siglent.write(self.channel + ":BTWV TIME," + str(n))
        self.cycles = n

    def get_cycles(self):
        return(self.cycles)
    
    def set_arbwave(self, file):
        """Sets the arbitrary wavefile to be displayed by the siglent module"""
        self.set_wavetype("ARB")
        siglent.write(self.channel + f':ARWV NAME,"{file}"')
        # mandatory if we then want to change signal characteristics such as frequency
        siglent.write(self.channel + ":ARBM AFG")
        self.file = file
        # Actualise class values
        amplitude = self.get_amplitude()
        phase = self.get_phase()

    def get_file(self):
        return(self.file)
    
    def set_state(self, state):
        """Sets the channel output "ON" or "OFF" """
        siglent.write(self.channel + ":OUTP " + state)
        self.state = state

    def get_state(self):
        return(self.state)