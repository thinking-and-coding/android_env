import io
import os

import numpy as np
from PIL import Image
from absl import logging

from android_env.components import log_stream, adb_controller, config_classes, adb_log_stream
from android_env.components.simulators import base_simulator
from android_env.components import errors


class RealDeviceSimulator(base_simulator.BaseSimulator):

    def __init__(self, config: config_classes.RealDeviceConfig):
        """Instantiates an RealDeviceSimulator."""

        super().__init__(config)
        self._verbose_logs = None
        self._config = config

        logging.info('Connecting to existing device "%r"', self.adb_device_name())

        # Initialize own ADB controller.
        self._adb_controller = self.create_adb_controller()
        self._adb_controller.init_server()
        logging.info(
            "Initialized device with ADB server port %r.",
            self._config.adb_controller_config.adb_server_port,
        )

        self._logfile_path = self._config.logfile_path or None

    def get_logs(self) -> str:
        """Returns logs recorded by the Device."""
        if self._logfile_path and os.path.exists(self._logfile_path):
            with open(self._logfile_path, "rb") as f:
                return f.read().decode("utf-8")
        else:
            return f"Logfile does not exist: {self._logfile_path}."

    def adb_device_name(self) -> str:
        return self._config.device_name

    def create_adb_controller(self) -> adb_controller.AdbController:
        """Returns an ADB controller which can communicate with this device."""
        return adb_controller.AdbController(self._config.adb_controller_config)

    def create_log_stream(self) -> log_stream.LogStream:
        return adb_log_stream.AdbLogStream(
            adb_command_prefix=self._adb_controller.command_prefix(), verbose=self._verbose_logs
        )

    def _launch_impl(self) -> None:
        logging.info("Launch device specific implementation.")
        cmd_output = self._adb_controller.execute_command(
            ['devices'], device_specific=False)
        cmd_str = cmd_output.decode('utf-8')
        logging.info("Got devices: %r.",cmd_str)
        if not self.adb_device_name() in cmd_str:
            logging.info("Can not launch device: %r.", self.adb_device_name())
            raise errors.SimulatorError()
        logging.info("Launch device: %r success!", self.adb_device_name())

    def send_touch(self, touches: list[tuple[int, int, bool, int]]) -> None:
        """Sends a touch event to be executed on the simulator.

                Args:
                  touches: A list of touch events. Each element in the list corresponds to a
                      single touch event. Each touch event tuple should have:
                      0 x: The horizontal coordinate of this event.
                      1 y: The vertical coordinate of this event.
                      2 is_down: Whether the finger is touching or not the screen.
                      3 identifier: Identifies a particular finger in a multitouch event.
                """
        if len(set([touch[3] for touch in touches])) > 1:
            logging.warn("Only supported single touch in real device by adb!")
        for t in touches:
            if t[2]:
                self._adb_controller.execute_command(['shell', 'input', 'tap', str(t[0]), str(t[1])])

    def send_key(self, keycode: np.int32, event_type: str) -> None:
        """Sends a key event to the device.

                Args:
                  keycode: Code representing the desired key press in XKB format.
                    See the emulator_controller_pb2 for details.
                  event_type: Type of key event to be sent.
                """

        logging.warn("Dot not supported KeyboardEvent in real device by adb!")

    def _get_screenshot_impl(self) -> np.ndarray:
        """Fetches the latest screenshot from the device."""

        image_bytes = self._adb_controller.execute_command(['exec-out', 'screencap', '-p'])
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)[:, :, :3]
        return image_array
