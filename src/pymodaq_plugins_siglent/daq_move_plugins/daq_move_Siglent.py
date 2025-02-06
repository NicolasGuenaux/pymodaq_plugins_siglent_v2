from typing import Union, List, Dict

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType,\
    DataActuator  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter

import sys, os
from siglent_wrapper import ActuatorWrapper
sys.path.append('c:\\Users\\attose1_VMI\\local_repository\\pymodaq_plugins_siglent\\src\\pymodaq_plugins_siglent\\daq_move_plugins')


# TODO:
# (1) change the name of the following class to DAQ_Move_TheNameOfYourChoice
# (2) change the name of this file to daq_move_TheNameOfYourChoice ("TheNameOfYourChoice" should be the SAME
#     for the class name and the file name.)
# (3) this file should then be put into the right folder, namely IN THE FOLDER OF THE PLUGIN YOU ARE DEVELOPING:
#     pymodaq_plugins_my_plugin/daq_move_plugins
class DAQ_Move_Siglent(DAQ_Move_base):
    """ Instrument plugin class for an actuator.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of controllers and actuators that should be compatible with this instrument plugin.
        * With which instrument and controller it has been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    # TODO add your particular attributes here if any

    """
    is_multiaxes = True  # TODO for your plugin set to True if this plugin is controlled for a multiaxis controller
    _axis_names: Union[List[str], Dict[str, int]] = ['Amplitude', 'Phase', 'Frequency', 'Delay']  # TODO for your plugin: complete the list
    _controller_units: Union[str, List[str]] = ['V', 'deg', 'Hz', 's']  # TODO for your plugin: put the correct unit here, it could be
    # TODO  a single str (the same one is applied to all axes) or a list of str (as much as the number of axes)
    _epsilon: Union[float, List[float]] = [0.1, 0.1, 0.1, 0.1]  # TODO replace this by a value that is correct depending on your controller
    # TODO it could be a single float of a list of float (as much as the number of axes)
    data_actuator_type = DataActuatorType.DataActuator  # wether you use the new data style for actuator otherwise set this
    # as  DataActuatorType.float  (or entirely remove the line)

    params = [
        {'title': 'Burst:', 'name': 'burst', 'type': 'text', 'value': "ON"},
        {'title': 'Frequency:', 'name': 'frequency', 'type': 'float', 'value': 1e7},
        {'title': 'Offset:', 'name': 'offset', 'type': 'float', 'value': 0},
        {'title': 'Delay:', 'name': 'delay', 'type': 'float', 'value': 5e-6},
        {'title': 'Rep number:', 'name': 'cycles', 'type': 'int', 'value': 1},
        # {'title': 'Wavetype:', 'name': 'wavetype', 'type': 'text', 'value': "SINE"},
        {'title': 'Wavetype:', 'name': 'wavetype', 'type': 'itemselect',
         'value': dict(all_items=["ARB", "SINE", "RAMP", "SQUARE", "DC"], selected=["SINE"])},
        {'title': 'File:', 'name': 'file', 'type': 'text', 'value': ""},
         # TODO for your custom plugin: elements to be added here as dicts in order to control your custom stage
                ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)
    # _epsilon is the initial default value for the epsilon parameter allowing pymodaq to know if the controller reached
    # the target value. It is the developer responsibility to put here a meaningful value

    def ini_attributes(self):
        # #  TODO declare the type of the wrapper (and assign it to self.controller) you're going to use for easy
        # #  autocompletion
        self.controller: ActuatorWrapper

        #TODO declare here attributes you want/need to init with a default value

        pass

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        ## TODO for your custom plugin
        # raise NotImplemented  # when writing your own plugin remove this line
        pos = DataActuator(data=self.controller.get_pos())  # when writing your own plugin replace this line
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        # ## TODO for your custom plugin
        # raise NotImplemented  # when writing your own plugin remove this line
        # #  self.controller.your_method_to_terminate_the_communication()  # when writing your own plugin replace this line

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == 'axis':
            self.controller.set_axis(self.axis_name)
            pos = self.get_actuator_value()
            if self.axis_name == "Delay":
                self.controller.set_burst(mode="ON")
            self.axis_unit = self.controller.get_unit()
            # do this only if you can and if the units are not known beforehand, for instance
            # if the motors connected to the controller are of different type (mm, µm, nm, , etc...)
            # see BrushlessDCMotor from the thorlabs plugin for an exemple

        elif param.name() == "burst":
            self.controller.set_burst(mode=param.value())
        elif param.name() == "frequency":
            self.controller.set_frequency(param.value())
        elif param.name() == "offset":
            self.controller.set_offset(param.value())
        elif param.name() == "delay":
            self.controller.set_delay(param.value())
        elif param.name() == "cycles":
            self.controller.set_cycles(param.value())
        elif param.name() == "wavetype":
            wavetype = param.value().get('selected')[0]
            self.controller.set_wavetype(wavetype)

            burst_state = self.controller.get_burst_state()
            self.settings.child('burst').setValue(burst_state)

            dc = (wavetype == "DC")
            offset = self.controller.get_offset(DC=dc)
            self.settings.child('offset').setValue(offset)
        elif param.name() == "file":
            self.controller.set_arbwave(param.value())
            self.settings.child('wavetype').setValue(
                dict(all_items=["ARB", "SINE", "RAMP", "SQUARE", "DC"], selected=["ARB"]))

            freq = self.controller.get_frequency()
            self.settings.child('frequency').setValue(freq)

            offset = self.controller.get_offset()
            self.settings.child('offset').setValue(offset)

            burst_state = self.controller.get_burst_state()
            self.settings.child('burst').setValue(burst_state)
        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        ##### Si slave ya moyen que ça foire
        if self.is_master:  # is needed when controller is master
            self.controller = ActuatorWrapper()
            # todo: enter here whatever is needed for your controller initialization and eventual
            #  opening of the communication channel

        self.controller.__init__()  # todo
        info = "siglent connected"
        initialized = self.controller.open_communication()

        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
        ## TODO for your custom plugin
        # raise NotImplemented  # when writing your own plugin remove this line
        self.controller.set_pos(value.value())  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['position updated']))

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        pos = self.controller.get_pos()
        self.current_position = pos

        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        ## TODO for your custom plugin
        # raise NotImplemented  # when writing your own plugin remove this line
        # self.controller.set_rel_pos(value.value())  # when writing your own plugin replace this line

        self.controller.set_pos(pos + value.value())
        self.emit_status(ThreadCommand('Update_Status', ['position updated']))

    def move_home(self):
        """Call the reference method of the controller"""

        ## TODO for your custom plugin
        # raise NotImplemented  # when writing your own plugin remove this line
        self.controller.set_amplitude(amp=2)  # when writing your own plugin replace this line
        self.controller.set_phase(phi=0)
        self.emit_status(ThreadCommand('Update_Status', ['moved home (amp = 2, phi=0)']))

    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""

      ## TODO for your custom plugin
    #   raise NotImplemented  # when writing your own plugin remove this line
      self.controller.set_state("OFF")  # when writing your own plugin replace this line
      self.emit_status(ThreadCommand('Update_Status', ['channel output OFF']))


if __name__ == '__main__':
    main(__file__)