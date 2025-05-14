# coding=utf-8
# Copyright 2024 DeepMind Technologies Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for android_env.components.emulator_simulator."""

import builtins
import os
from unittest import mock

from absl.testing import absltest

from android_env.components import adb_call_parser
from android_env.components import adb_controller
from android_env.components import config_classes
from android_env.components.simulators.real_device import real_device_simulator


class DeviceSimulatorTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.addCleanup(mock.patch.stopall)  # Disable previous patches.

    self._adb_controller = mock.create_autospec(adb_controller.AdbController)
    self._adb_call_parser = mock.create_autospec(adb_call_parser.AdbCallParser)

    mock.patch.object(
        adb_controller, 'AdbController',
        return_value=self._adb_controller).start()
    mock.patch.object(
        adb_call_parser,
        'AdbCallParser',
        autospec=True,
        return_value=self._adb_call_parser).start()

  def test_adb_device_name_not_empty(self):
      config = config_classes.RealDeviceConfig(
          device_name="172.16.116.186:5555",
          adb_controller_config=config_classes.AdbControllerConfig(
              adb_path='/opt/homebrew/bin/adb',
              adb_server_port=5037,
          ),
      )
      simulator = real_device_simulator.RealDeviceSimulator(config=config)
      self.assertNotEmpty(simulator.adb_device_name())

  @mock.patch.object(os.path, 'exists', autospec=True, return_value=True)
  @mock.patch.object(builtins, 'open', autospec=True)
  def test_logfile_path(self, mock_open, unused_mock_exists):
      config = config_classes.RealDeviceConfig(
          device_name="172.16.116.186:5555",
          adb_controller_config=config_classes.AdbControllerConfig(
              adb_path='/opt/homebrew/bin/adb',
              adb_server_port=5037,
          ),
          logfile_path="fake/logfile/path"
      )
      simulator = real_device_simulator.RealDeviceSimulator(config=config)
      mock_open.return_value.__enter__.return_value.read.return_value = (
          'fake_logs'.encode('utf-8'))
      logs = simulator.get_logs()
      mock_open.assert_called_once_with('fake/logfile/path', 'rb')
      self.assertEqual(logs, 'fake_logs')

  def test_close(self):
      config = config_classes.RealDeviceConfig(
          device_name="172.16.116.186:5555",
          adb_controller_config=config_classes.AdbControllerConfig(
              adb_path='/opt/homebrew/bin/adb',
              adb_server_port=5037,
          ),
      )
      simulator = real_device_simulator.RealDeviceSimulator(config=config)

      # The simulator should launch and not crash.
      simulator.launch()

      # For whatever reason clients may want to close the EmulatorSimulator.
      # We just want to check that the simulator does not crash and/or leak
      # resources.
      simulator.close()

  def test_get_screenshot(self):
      config = config_classes.RealDeviceConfig(
          device_name="172.16.116.186:5555",
          adb_controller_config=config_classes.AdbControllerConfig(
              adb_path='/opt/homebrew/bin/adb',
              adb_server_port=5037,
          ),
      )
      simulator = real_device_simulator.RealDeviceSimulator(config=config)

      # The simulator should launch and not crash.
      simulator.launch()

      mock_image = mock.MagicMock(name = "PIL.Image.Image")
      from unittest.mock import patch
      with patch("PIL.Image.open", return_value=mock_image) as mock_open:
          # 调用你的代码，这时 Image.open(...) 会返回 mock_image
          mock_open.assert_called_once()

      mock_image.size = (1234, 5678)
      mock_image.mode = "RGB"

      screenshot = simulator.get_screenshot()
      # The screenshot should have the same screen dimensions as reported by ADB
      # and it should have 3 channels (RGB).
      self.assertEqual(screenshot.shape, (1234, 5678, 3))


if __name__ == '__main__':
  absltest.main()
