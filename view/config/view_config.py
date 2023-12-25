import pygame as p
import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")


class ViewConfig:
    MAX_FPS = 15
    WIDTH = HEIGHT = 512
    DIMENSION = 8
    SQ_SIZE = WIDTH // DIMENSION
    BROWN = (100, 40, 0)
    BEIGE = (255, 211, 155)
    COLOR_BROWN = p.Color(BROWN)
    COLOR_BEIGE = p.Color(BEIGE)
