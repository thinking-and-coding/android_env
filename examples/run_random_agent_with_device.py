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

"""Example script demonstrating usage of AndroidEnv."""

from absl import app
from absl import flags
from absl import logging
from android_env import loader
from android_env.components import config_classes
from dm_env import specs
import numpy as np

FLAGS = flags.FLAGS

# Simulator args.
flags.DEFINE_string('adb_path','~/Android/Sdk/platform-tools/adb', 'Path to ADB.')
# Environment args.
flags.DEFINE_string('task_path', None, 'Path to task textproto file.')
# Device name
flags.DEFINE_string('device_name', None, 'Real device to act.')
# Experiment args.
flags.DEFINE_integer('num_steps', 1000, 'Number of steps to take.')


def main(_):

  config = config_classes.AndroidEnvConfig(
      task=config_classes.FilesystemTaskConfig(path=FLAGS.task_path),
      simulator=config_classes.RealDeviceConfig(
          device_name=FLAGS.device_name,
          adb_controller_config=config_classes.AdbControllerConfig(
              adb_path=FLAGS.adb_path,
              device_name=FLAGS.device_name,
          ),
      ),
  )
  with loader.load(config) as env:

    action_spec = env.action_spec()

    def get_random_action() -> dict[str, np.ndarray]:
      """Returns a random AndroidEnv action."""
      action = {}
      for k, v in action_spec.items():
        if isinstance(v, specs.DiscreteArray):
          action[k] = np.random.randint(low=0, high=v.num_values, dtype=v.dtype)
        else:
          action[k] = np.random.random(size=v.shape).astype(v.dtype)
      return action

    _ = env.reset()

    for step in range(FLAGS.num_steps):
      action = get_random_action()
      timestep = env.step(action=action)
      reward = timestep.reward
      logging.info('Step %r, action: %r, reward: %r', step, action, reward)


if __name__ == '__main__':
  logging.set_verbosity('info')
  logging.set_stderrthreshold('info')
  flags.mark_flags_as_required(['adb_path', 'task_path', 'device_name'])
  app.run(main)
