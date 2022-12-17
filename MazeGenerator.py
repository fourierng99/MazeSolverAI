import numpy as np
import random
import pygame

class Maze:
    def __init__(self,size_x, size_y):
        self.screen = None 
        self.screen_size = None
        self.screen_block_size = None
        self.screen_block_offset = None
        self.prev_update = 0
        self.clock = pygame.time.Clock()
        self.slow_mode = False
        self.running = True

        
        self.wall_size = np.array([size_y, size_x], dtype=np.int)
        
        self.walls = np.ones((self.wall_size[0] + 2, self.wall_size[1] + 2, 3), dtype=np.byte)
        
        self.walls[:, 0, 0] = -1
        self.walls[:, self.wall_size[1] + 1, 0] = -1
        self.walls[0, :, 0] = -1
        self.walls[self.wall_size[0] + 1, :, 0] = -1

        
        self.block_size = np.array([size_y * 2 + 1, size_x * 2 + 1], dtype=np.int)
        self.blocks = np.ones((self.block_size[0], self.block_size[1]), dtype=np.byte)

    def gen_maze_walls(self, corrider_len = 999):
        cell = np.array([random.randrange(2, self.wall_size[0]), random.randrange(2, self.wall_size[1])], dtype=np.int)
        self.walls[cell[0], cell[1], 0] = 0

        up    = np.array([-1,  0], dtype=np.int)
        down  = np.array([ 1,  0], dtype=np.int)
        left  = np.array([ 0, -1], dtype=np.int)
        right = np.array([ 0,  1], dtype=np.int)

        need_cell_range = False
        round_nr = 0
        corridor_start = 0
        if corridor_len <= 4:
            corridor_len = 5

        while np.size(cell) > 0 and self.running:

            round_nr += 1
            # get the four neighbors for current cell (cell may be an array of cells)
            cell_neighbors = np.vstack((cell + up, cell + left, cell + down, cell + right))
            # valid neighbors are the ones not yet visited
            valid_neighbors = cell_neighbors[self.walls[cell_neighbors[:, 0], cell_neighbors[:, 1], 0] == 1]

            if np.size(valid_neighbors) > 0:
                # there is at least one valid neighbor, pick one of them (at random)
                neighbor = valid_neighbors[random.randrange(0, np.shape(valid_neighbors)[0]), :]
                if np.size(cell) > 2:
                    # if cell is an array of cells, pick one cell with this neighbor only, at random
                    cell = cell[np.sum(abs(cell - neighbor), axis=1) == 1]  # cells where distance to neighbor == 1
                    cell = cell[random.randrange(0, np.shape(cell)[0]), :]
                # mark neighbor visited
                self.walls[neighbor[0], neighbor[1], 0] = 0
                # remove the wall between current cell and neighbor. Applied to down and right walls only so may be that of the cell or the neighbor
                self.walls[min(cell[0], neighbor[0]), min(cell[1], neighbor[1]), 1 + abs(neighbor[1] - cell[1])] = 0
                if self.screen is not None:
                    # if screen is set, draw the corridor from cell to neighbor
                    self.draw_cell(cell, neighbor)
                # check if more corridor length is still available
                if round_nr - corridor_start < corridor_len:
                    # continue current corridor: set current cell to neighbor
                    cell = np.array([neighbor[0], neighbor[1]], dtype=np.int)
                else:
                    # maximum corridor length fully used; make a new junction and continue from there
                    need_cell_range = True

            else:
                # no valid neighbors for this cell
                if np.size(cell) > 2:
                    # if cell already contains an array of cells, no more valid neighbors are available at all
                    cell = np.zeros((0, 0))  # this will end the while loop, the maze is finished.
                    if self.screen is not None:
                        # if screen is set, make sure it is updated as the maze is now finished.
                        pygame.display.flip()
                else:
                    # a dead end; make a new junction and continue from there
                    need_cell_range = True

            if need_cell_range:
                # get all visited cells (=0) not marked as "no neighbors" (=-1), start a new corridor from one of these (make a junction)
                cell = np.transpose(np.nonzero(self.walls[1:-1, 1:-1, 0] == 0)) + 1  # not checking the edge cells, hence needs the "+ 1"
                # check these for valid neighbors (any adjacent cell with "1" as visited status (ie. not visited) is sufficient, hence MAX)
                valid_neighbor_exists = np.array([self.walls[cell[:, 0] - 1, cell[:, 1], 0],
                                                  self.walls[cell[:, 0] + 1, cell[:, 1], 0],
                                                  self.walls[cell[:, 0], cell[:, 1] - 1, 0],
                                                  self.walls[cell[:, 0], cell[:, 1] + 1, 0]
                                                  ]).max(axis=0)
                # get all visited cells with no neighbors
                cell_no_neighbors = cell[valid_neighbor_exists != 1]
                # mark these (-1 = no neighbors) so they will no longer be actively used. This is not required but helps with large mazes.
                self.walls[cell_no_neighbors[:, 0], cell_no_neighbors[:, 1], 0] = -1
                corridor_start = round_nr + 0  # start a new corridor.
                need_cell_range = False

        # return: drop out the additional edge cells. All cells visited anyway so just return the down and right edge data.
        if self.running:
            return self.walls[1:-1, 1:-1, 1:3] 

    def gen_maze_2D(self, corrider_len = 999):
        self.gen_maze_walls(corridor_len)

        if self.running:
            # use wall data to set final output maze
            self.blocks[1:-1:2, 1:-1:2] = 0  # every cell is visited if correctly generated
            # horizontal walls
            self.blocks[1:-1:2, 2:-2:2] = self.walls[1:-1, 1:-2, 2]  # use the right wall
            # vertical walls
            self.blocks[2:-2:2, 1:-1:2] = self.walls[1:-2, 1:-1, 1]  # use the down wall

            return self.blocks

    def draw_cell(self, cell, neighbor):
        pass
        