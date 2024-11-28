import time

import vidmaker
import pygame as p
import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from gym_wrapper.environment import ChessGym


class VideoRecorder:
    def __init__(self, env: ChessGym, video_path):
        self.env = env
        self.video_recorder = vidmaker.Video(video_path, late_export=True)

    def record(self):
        self.video_recorder.update(p.surfarray.pixels3d(self.env.chess_screen.screen).swapaxes(0, 1), inverted=False)

    def export(self):
        self.video_recorder.export(verbose=True)


if __name__ == '__main__':
    p.init()
    env_ = ChessGym()
    record_env = VideoRecorder(env_, "random_action.mp4")
    env_.make("white")
    state = env_.reset()
    score = 0
    done = False

    while not done:
        from_pos, to_pos = env_.action_space.sample()
        reward, done, _, _ = env_.step_inference(state, (from_pos, to_pos))
        score += reward
        print(f"Score: {score}")
        record_env.record()
        time.sleep(0.2)

    record_env.export()
    env_.close()
