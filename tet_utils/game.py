import pygame
import time
from tet_utils.board import Board
from tet_utils.handler import Handler
from tet_utils.rng import RNG
from tet_utils.minos import *

ATTACK_TABLE = {
    0: 0,
    1: 0,
    2: 1,
    3: 2,
    4: 4
}

TSPIN_ATTACK_TABLE = {
    0: 0,
    1: 1,
    2: 4,
    3: 6
}

class Game:
    def __init__(self, handling, seed=None):
        self.handling = handling

        self.seed = round(time.time()*10000)
        if seed:
            self.seed = seed
        self.rng = RNG(self.seed)
        self.restart()

    def restart(self, seed=None):
        if seed:
            self.seed = seed
        self.rng = RNG(self.seed)
        self.board = Board(10, 40)
        self.queue = []
        self.next()
        self.handler = Handler(self.handling["das"], self.handling["arr"], self.handling["sdf"])
        self.hold_type = ""
        self.held = False
        self.attack = 0

        self.garbage = 0

    def draw_mino(self, screen, unit, pos, mx, my, mt, mr, color=None):
        if color == None:
            color = MINO_COLORS[mt]
        for y, row in enumerate(MINO_SHAPES[mt][str(mr)]):
            for x, dot in enumerate(row):
                if dot:
                    rect = ((mx+x)*unit+pos[0], (my+y)*unit+pos[1], unit, unit)
                    pygame.draw.rect(screen, color, rect)
    
    def next(self):
        if len(self.queue) <= 5:
            self.queue += self.rng.shuffleArray(MINO_TYPES.copy())
        self.mino = self.pop_queue()

    def draw_next(self, screen, unit, pos):
        gap = 2.8
        for i in range(5):
            mino_type = self.queue[i]
            x = 0
            y = 0
            if mino_type == "I":
                y = -0.5
            if mino_type == "O":
                x = -0.5
            self.draw_mino(screen, unit, pos, 11+x, y+1+i*gap, mino_type, 0, MINO_COLORS[mino_type])

    def soft_drop(self):
        for _ in range(self.board.h):
            if self.mino.move(0, 1, self.board) == False:
                break

    def hard_drop(self):
        self.held = False
        for _ in range(self.board.h):
            if self.mino.move(0, 1, self.board) == False:
                test_mino = Mino(self.mino.type, self.mino.x, self.mino.y, self.mino.rotation)
                tspin = self.mino.type == "T" and test_mino.move(0, -1, self.board) == False
                self.board.place(self.mino)
                
                cleared_lines = self.board.line_clear()
                attack = ATTACK_TABLE[cleared_lines]
                if tspin:
                    attack = TSPIN_ATTACK_TABLE[cleared_lines]
                self.garbage += attack
                self.attack += attack
                
                self.next()
                break
            
        take_garbage = -min(self.garbage, 0)
        self.board.add_garbage(take_garbage, round(self.rng.nextFloat()))
        self.garbage += take_garbage

    def keydown(self, key):
        if key == "right":
            self.handler.down_right()
            self.mino.move(1, 0, self.board)
        if key == "left":
            self.handler.down_left()
            self.mino.move(-1, 0, self.board)
        if key == "softdrop":
            self.handler.down_soft_drop()
            if self.handler.sdf == 0:
                self.soft_drop()
            else:
                self.mino.move(0, 1, self.board)
        if key == "cw":
            self.mino.rotate(1, self.board)
        if key == "ccw":
            self.mino.rotate(-1, self.board)
        if key == "180":
            self.mino.rotate(2, self.board)
        if key == "harddrop":
            self.hard_drop()
        if key == "hold":
            self.hold()

    def keyup(self, key):
        if key == "right":
            self.handler.up_right()
        if key == "left":
            self.handler.up_left()
        if key == "softdrop":
            self.handler.up_soft_drop()

    def hold(self):
        if self.held:
            return
        old_type = self.mino.type
        if self.hold_type == "":
            self.next()
        else:
            self.mino = Mino(self.hold_type, 3, self.board.h//2-4)
        self.hold_type = old_type
        self.held = True

    def update(self, dt):
        movement_queue = self.handler.update(dt, self.board)
        for x, y in movement_queue:
            self.mino.move(x, y, self.board)

    def draw_shadow(self, screen, unit, pos):
        shadow_mino = Mino(self.mino.type, self.mino.x, self.mino.y, self.mino.rotation)
        for _ in range(self.board.h):
            if shadow_mino.move(0, 1, self.board) == False:
                break
        self.draw_mino(screen, unit, pos, self.mino.x, shadow_mino.y, self.mino.type, self.mino.rotation, MINO_COLORS["X"])

    def draw(self, screen, unit, offset=(0, 0)):
        pos = (screen.get_width()/2-unit*10/2+offset[0], screen.get_height()/2-unit*20/2+offset[1])
        pos_margin = (pos[0], pos[1]-self.board.h//2*unit)
        
        self.board.draw(screen, unit, pos_margin)
        self.draw_shadow(screen, unit, pos_margin)
        self.draw_mino(screen, unit, pos_margin, self.mino.x, self.mino.y, self.mino.type, self.mino.rotation)
        if self.hold_type != "":
            color = MINO_COLORS[self.hold_type]
            if self.held:
                color = MINO_COLORS["H"]
            self.draw_mino(screen, unit, pos, -5, 1, self.hold_type, 0, color)
        self.draw_next(screen, unit, pos)

    def fill_queue(self):
        self.queue += self.rng.shuffleArray(MINO_TYPES.copy())

    def pop_queue(self):
        return Mino(self.queue.pop(0), 3, self.board.h//2-4)

    def get_garbage(self):
        garbage = max(0, self.garbage)
        self.garbage -= garbage
        return garbage
    
    def add_garbage(self, amount):
        self.garbage -= amount