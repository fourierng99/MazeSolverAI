# -*- coding: utf-8 -*-
import numpy as np
import pygame
import maze_generator
from os.path import exists
from sys import exit


class MazeSolver:
    """
    Solve a maze given in "block form" by maze_generator.py (a NumPy Array with 0 as a corridor and 1 as a wall block; outer edges are wall blocks).
    Show progress graphically. The mouse can be used to pick begin and end positions; maze resolution changed by up & down cursor keys.

    @author: kalle
    """

    def __init__(self, screen, rect, blocks, start_pos, end_pos):

        self.screen = screen
        self.rect = np.asarray(rect, dtype=np.int16)  # the rect inside which the maze resides (top x, top y, width, height)
        self.blocks = blocks  # blocks should be given as (y, x) array, dtype=np.byte, 0 as a corridor and 1 as a wall
        self.start_pos = start_pos.astype(np.int16)
        self.end_pos = end_pos.astype(np.int32)  # the goal to seek
        self.block_size = np.asarray(np.shape(self.blocks))
        self.screen_size = np.asarray(self.screen.get_size())
        self.screen_block_size = np.min(self.rect[2:4] / np.flip(self.block_size))
        self.screen_block_offset = self.rect[0:2] + (self.rect[2:4] - self.screen_block_size * np.flip(self.block_size)) // 2
        self.prev_update = 0
        self.running = True
        self.screen_info = pygame.Surface((1100, 90))

        self.junctions = np.zeros((100, 7), dtype=np.int16)  # will store the junction cell, the cell before that, distance to end, and nr of directions to go
        self.junction_nr = -1
        self.junctions_used = 0

        self.solution_type = 0

        self.cell_size = 0
        self.slow_mode = False
        self.info_display = False
        self.last_message = ''
        pygame.font.init()
        self.font = pygame.font.SysFont('CourierNew', 16)

        self.background_color = (0, 0, 0)
        self.info_color = (255, 255, 255)
        self.maze_color = (200, 200, 200)
        self.start_color = (50, 50, 200)
        self.end_color = (50, 200, 50)
        self.path_color = (200, 200, 0)
        self.solution_color = (240, 50, 50)

        self.bfs_path_color = (136, 3, 252)
        self.dfs_path_color = (3, 161, 252)
        self.a_star_path_color = (252, 103, 3)
        self.a_dfs_hybrid_color = (200, 200, 0)

        self.bfs_solution_color = (252, 3, 152)
        self.dfs_solution_color = (45, 3, 252)
        self.a_star_solution_color = (3, 252, 107)
        self.a_dfs_hybrid_solution_color = (240, 50, 50)
        self.is_save_img = False

    def solve_maze(self):
        #self.slow_mode = True
        #self.solution_type = 4

        start_pos = np.copy(self.start_pos)
        end_pos = np.copy(self.end_pos)
        blocks = np.copy(self.blocks)

        if(np.array_equal(self.start_pos, self.end_pos)):
            return
        if self.solution_type == 9:
            self.solve_maze_sample()
        elif self.solution_type == 0:
            self.solve_maze_bfs()
        elif self.solution_type == 1:
            self.solve_maze_dfs() 
        elif self.solution_type == 2:
            self.solve_maze_a_star()
        elif self.solution_type == 3:
            self.solve_maze_dfs_hybrid()
        elif self.solution_type == 4:
            self.solve_maze_greedy()
        elif self.solution_type == 5:
            self.start_pos =np.copy(start_pos)
            self.end_pos = np.copy(end_pos)
            self.blocks = np.copy(blocks)
            self.solve_maze_bfs()

            self.start_pos =np.copy(start_pos)
            self.end_pos = np.copy(end_pos)
            self.blocks = np.copy(blocks)
            self.solve_maze_dfs()

            self.start_pos =np.copy(start_pos)
            self.end_pos = np.copy(end_pos)
            self.blocks = np.copy(blocks)
            self.solve_maze_a_star()

            self.start_pos =np.copy(start_pos)
            self.end_pos = np.copy(end_pos)
            self.blocks = np.copy(blocks)
            self.solve_maze_dfs_hybrid()

            self.start_pos =np.copy(start_pos)
            self.end_pos = np.copy(end_pos)
            self.blocks = np.copy(blocks)
            self.solve_maze_greedy()

        

        self.draw_cell(start_pos, start_pos, self.start_color)
        self.draw_cell(end_pos, end_pos, self.end_color)

    def solve_maze_a_star(self):
        if self.blocks[self.start_pos[0], self.start_pos[1]] != 0 or self.blocks[self.end_pos[0], self.end_pos[1]] != 0:
            print('Start and end positions must not be in a wall.')
            self.running = False
            return

        self.save_image()
        i_cnt = 0
        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        directions = np.array([
            [-1,  0],  # up
            [ 1,  0],  # down
            [ 0, -1],  # left
            [ 0,  1]   # right
            ], dtype=np.int16)
        
        open_list = []
        open_heuristics = []

        open_list.append(cell)
        open_heuristics.append(np.zeros(2))

        close_list = []

        trace_mat = np.ones((self.block_size[0], self.block_size[1], 2), dtype=np.int16)*-1
        trace_mat[cell[0], cell[1]] = cell

        while self.running and (not np.array_equal(cell, self.end_pos)):
            if len(open_list) == 0:
                break
            current_index = 0
            for i in range(0, len(open_list)):
                if sum(open_heuristics[i]) <= sum(open_heuristics[current_index]):
                    current_index = i
                # if open_heuristics[i][1] < open_heuristics[current_index][1]:
                #     current_index = i

            cell = open_list.pop(current_index)
            heuristics = open_heuristics.pop(current_index)
            close_list.append(cell)
            
            #if(not np.array_equal(cell, self.end_pos)):

            previous = np.copy(cell)
            self.draw_cell(cell, previous, self.a_star_path_color)

            self.blocks[cell[0], cell[1]] = 2

            cell_neighbors = np.hstack((
                cell + directions,
                np.sum((self.end_pos - cell) * directions, axis=1)[:, None]
                ))
            valid_neighbors = cell_neighbors[(self.blocks[cell_neighbors[:, 0], cell_neighbors[:, 1]] == 0)]
            #print(valid_neighbors, "xxx", open_list)
            for nb in valid_neighbors:
                for i in range(len(open_list)):
                    if(np.array_equal(open_list[i], nb[:2])):
                        print(open_list[i])
                open_list.append(nb[:2])
                n_heuristic = np.zeros(2)
                n_heuristic[0] = heuristics[0] +1
                n_heuristic[1] = int(np.sqrt(np.sum((self.end_pos - cell) ** 2)))
                open_heuristics.append(n_heuristic)
                trace_mat[nb[0], nb[1]] = previous
            
            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()

        pygame.display.flip()
        self.save_image()
        i_cnt = 0

        t_cell = self.end_pos
        prev = np.copy(t_cell)
        while(not np.array_equal(t_cell, self.start_pos)):
            self.draw_cell(t_cell, prev, self.a_star_solution_color)
            prev = np.copy(t_cell)
            t_cell = trace_mat[t_cell[0], t_cell[1]]

            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()
        
        self.blocks[cell[0], cell[1]] = 4  # mark starting cell as route
        # ensure display is updated
        pygame.display.flip()

        self.save_image()

    def solve_maze_greedy(self):
        if self.blocks[self.start_pos[0], self.start_pos[1]] != 0 or self.blocks[self.end_pos[0], self.end_pos[1]] != 0:
            print('Start and end positions must not be in a wall.')
            self.running = False
            return

        self.save_image()
        i_cnt = 0
        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        directions = np.array([
            [-1,  0],  # up
            [ 1,  0],  # down
            [ 0, -1],  # left
            [ 0,  1]   # right
            ], dtype=np.int16)
        
        open_list = []

        open_list.append(cell)

        close_list = []

        trace_mat = np.ones((self.block_size[0], self.block_size[1], 2), dtype=np.int16)*-1
        trace_mat[cell[0], cell[1]] = cell

        while self.running and (not np.array_equal(cell, self.end_pos)):
            if len(open_list) == 0:
                break
            open_list.sort(reverse=True, key = lambda x : np.sum((self.end_pos - x) ** 2 ))
            cell = open_list.pop()

            close_list.append(cell)
            previous = np.copy(cell)
            self.draw_cell(cell, previous, self.a_star_path_color)

            self.blocks[cell[0], cell[1]] = 2

            cell_neighbors = np.hstack((
                cell + directions,
                np.sum((self.end_pos - cell) * directions, axis=1)[:, None]
                ))
            valid_neighbors = cell_neighbors[(self.blocks[cell_neighbors[:, 0], cell_neighbors[:, 1]] == 0)]

            for nb in valid_neighbors:
                open_list.append(nb[:2])
                trace_mat[nb[0], nb[1]] = previous
            
            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()

        pygame.display.flip()
        self.save_image()
        i_cnt = 0

        t_cell = self.end_pos
        prev = np.copy(t_cell)
        while(not np.array_equal(t_cell, self.start_pos)):
            self.draw_cell(t_cell, prev, self.a_star_solution_color)
            prev = np.copy(t_cell)
            t_cell = trace_mat[t_cell[0], t_cell[1]]

            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()
        
        self.blocks[cell[0], cell[1]] = 4  # mark starting cell as route
        # ensure display is updated
        pygame.display.flip()

        self.save_image()

    def solve_maze_bfs(self):
        if self.blocks[self.start_pos[0], self.start_pos[1]] != 0 or self.blocks[self.end_pos[0], self.end_pos[1]] != 0:
            print('Start and end positions must not be in a wall.')
            self.running = False
            return
        
        self.save_image()
        i_cnt = 0
        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        directions = np.array([
            [-1,  0],  # up
            [ 1,  0],  # down
            [ 0, -1],  # left
            [ 0,  1]   # right
            ], dtype=np.int16)
        
        open_list = []
        open_list.append(cell)
        close_list = []

        trace_mat = np.ones((self.block_size[0], self.block_size[1], 2), dtype=np.int16)*-1
        trace_mat[cell[0], cell[1]] = cell

        while self.running and (not np.array_equal(cell, self.end_pos)):
            if len(open_list) == 0:
                break
            cell = open_list.pop()
            close_list.append(cell)

            previous = np.copy(cell)
            if(not np.array_equal(cell, self.start_pos) or not np.array_equal(cell, self.end_pos)):
                self.draw_cell(cell, previous, self.bfs_path_color)
            

            self.blocks[cell[0], cell[1]] = 2

            cell_neighbors = np.hstack((
                cell + directions,
                np.sum((self.end_pos - cell) * directions, axis=1)[:, None]
                ))
            valid_neighbors = cell_neighbors[(self.blocks[cell_neighbors[:, 0], cell_neighbors[:, 1]] == 0)]
            for nb in valid_neighbors:
                open_list.insert(0,nb[:2])
                trace_mat[nb[0], nb[1]] = previous

            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()

        pygame.display.flip()
        self.save_image()
        i_cnt = 0

        t_cell = self.end_pos
        prev = np.copy(t_cell)
        
        while(not np.array_equal(t_cell, self.start_pos)):
            t_cell = trace_mat[t_cell[0], t_cell[1]]
            prev = np.copy(t_cell)
            # if(np.array_equal(t_cell, self.start_pos) or np.array_equal(t_cell, self.end_pos)):
            #     continue
            self.draw_cell(t_cell, prev, self.bfs_solution_color)
            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()

        self.blocks[cell[0], cell[1]] = 4  # mark starting cell as route
        # ensure display is updated
        pygame.display.flip()

        self.save_image()

    def solve_maze_dfs(self):
        if self.blocks[self.start_pos[0], self.start_pos[1]] != 0 or self.blocks[self.end_pos[0], self.end_pos[1]] != 0:
            print('Start and end positions must not be in a wall.')
            self.running = False
            return
        
        self.save_image()
        i_cnt = 0
        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        directions = np.array([
            [-1,  0],  # up
            [ 1,  0],  # down
            [ 0, -1],  # left
            [ 0,  1]   # right
            ], dtype=np.int16)
        
        open_list = []
        open_list.append(cell)
        close_list = []

        trace_mat = np.ones((self.block_size[0], self.block_size[1], 2), dtype=np.int16)*-1
        trace_mat[cell[0], cell[1]] = cell

        while self.running and (not np.array_equal(cell, self.end_pos)):
            if len(open_list) == 0:
                break
            cell = open_list.pop()
            close_list.append(cell)

            #if(not np.array_equal(cell, self.end_pos)):

            previous = np.copy(cell)
            self.draw_cell(cell, previous, self.dfs_path_color)

            self.blocks[cell[0], cell[1]] = 2

            cell_neighbors = np.hstack((
                cell + directions,
                np.sum((self.end_pos - cell) * directions, axis=1)[:, None]
                ))
            valid_neighbors = cell_neighbors[(self.blocks[cell_neighbors[:, 0], cell_neighbors[:, 1]] == 0)]
            for nb in valid_neighbors:
                open_list.append(nb[:2])
                trace_mat[nb[0], nb[1]] = previous

            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()

        pygame.display.flip()
        self.save_image()
        i_cnt = 0

        t_cell = self.end_pos
        prev = np.copy(t_cell)
        while(not np.array_equal(t_cell, self.start_pos)):
            self.draw_cell(t_cell, prev, self.dfs_solution_color)
            prev = np.copy(t_cell)
            t_cell = trace_mat[t_cell[0], t_cell[1]]

            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()     
                    
        self.blocks[cell[0], cell[1]] = 4  # mark starting cell as route
        # ensure display is updated
        pygame.display.flip()

        self.save_image()

    def solve_maze_dfs_hybrid(self):
        if self.blocks[self.start_pos[0], self.start_pos[1]] != 0 or self.blocks[self.end_pos[0], self.end_pos[1]] != 0:
            print('Start and end positions must not be in a wall.')
            self.running = False
            return
        
        self.save_image()
        i_cnt = 0
        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        directions = np.array([
            [-1,  0],  # up
            [ 1,  0],  # down
            [ 0, -1],  # left
            [ 0,  1]   # right
            ], dtype=np.int16)
        
        open_list = []
        open_list.append(cell)
        close_list = []

        trace_mat = np.ones((self.block_size[0], self.block_size[1], 2), dtype=np.int16)*-1
        trace_mat[cell[0], cell[1]] = cell

        while self.running and (not np.array_equal(cell, self.end_pos)):
            if len(open_list) == 0:
                break
            cell = open_list.pop()
            close_list.append(cell)

            #if(not np.array_equal(cell, self.end_pos)):

            previous = np.copy(cell)
            self.draw_cell(cell, previous, self.a_dfs_hybrid_color)

            self.blocks[cell[0], cell[1]] = 2

            cell_neighbors = np.hstack((
                cell + directions,
                np.sum((self.end_pos - cell) * directions, axis=1)[:, None]
                ))
            valid_neighbors = cell_neighbors[(self.blocks[cell_neighbors[:, 0], cell_neighbors[:, 1]] == 0)]

            nb_count = np.shape(valid_neighbors)[0]
            if nb_count >= 1:
                valid_lst = [x[0:2] for x in valid_neighbors]
                valid_lst.sort(reverse = True,key = lambda x: sum((self.end_pos - x) ** 2))
                for nb in valid_lst:
                    open_list.append(nb[:2])
                    trace_mat[nb[0], nb[1]] = previous
            else:
                lst_distance = [sum((self.end_pos - x) ** 2) for x in open_list]
                ix = np.argmin(lst_distance)
                e = open_list.pop(ix)
                open_list.append(e)
            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()

        pygame.display.flip()
        self.save_image()
        print(i_cnt)
        i_cnt = 0

        t_cell = self.end_pos
        prev = np.copy(t_cell)
        while(not np.array_equal(t_cell, self.start_pos)):
            self.draw_cell(t_cell, prev, self.a_dfs_hybrid_solution_color)
            prev = np.copy(t_cell)
            t_cell = trace_mat[t_cell[0], t_cell[1]]

            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()     
                    
        self.blocks[cell[0], cell[1]] = 4  # mark starting cell as route
        # ensure display is updated
        pygame.display.flip()

        self.save_image()

    def solve_maze_sample(self):

        # solves a maze.

        # first check that solving is possible
        if self.blocks[self.start_pos[0], self.start_pos[1]] != 0 or self.blocks[self.end_pos[0], self.end_pos[1]] != 0:
            print('Start and end positions must not be in a wall.')
            self.running = False
            return

        self.save_image()
        i_cnt = 0

        cell = np.copy(self.start_pos)
        previous = np.copy(cell)

        # a simple definition of the four neighboring cells relative to current cell
        directions = np.array([
            [-1,  0],  # up
            [ 1,  0],  # down
            [ 0, -1],  # left
            [ 0,  1]   # right
            ], dtype=np.int16)

        while self.running and not np.array_equal(cell, self.end_pos):

            self.blocks[cell[0], cell[1]] = 2  # mark as visited, prevents from turning back.
            # define target direction
            # get the four neighbors for current cell and the "main distance" to indicate preferable direction
            cell_neighbors = np.hstack((
                cell + directions,
                np.sum((self.end_pos - cell) * directions, axis=1)[:, None]
                ))
            
            # pick the ones which are corridors and not visited yet
            valid_neighbors = cell_neighbors[(self.blocks[cell_neighbors[:, 0], cell_neighbors[:, 1]] == 0)]
            vn_count = np.shape(valid_neighbors)[0]

            if vn_count > 1:
                # multiple directions available - add the cell to the junctions stack
                # if there are three valid neighbors, not to worry - the third one will be taken care of if this junction is returned to
                self.junction_nr += 1
                # make sure there is enough stack
                if self.junction_nr >= np.shape(self.junctions)[0]:
                    self.junctions = np.resize(self.junctions, (self.junction_nr + 100, 6))
                # junction: store data on cell location and its distance to the end_pos
                self.junctions[self.junction_nr, 0:2] = cell      # cell location
                self.junctions[self.junction_nr, 2:4] = previous  # previous location - needed when retracing the solution
                self.junctions[self.junction_nr, 4] = int(np.sqrt(np.sum((self.end_pos - cell) ** 2)))  # distance to end_pos
                self.junctions[self.junction_nr, 5] = vn_count    # nr of directions (valid neighbors) available

            if vn_count == 1:
                # one direction available, take it. Store previous cell to use when coming to a junction.
                previous = np.copy(cell)
                cell = valid_neighbors[0, 0:2]
                self.draw_cell(cell, previous, self.path_color)

            else:
                # either a dead end (vn_count = 0) or a junction (vn_count > 1): pick the junction with the shortest distance to end_pos with valid neighbors
                closest = np.argmin(self.junctions[:self.junction_nr + 1, 4])
                self.junctions[closest, 5] -= 1  # this junction now has one less valid neighbors left
                if self.junctions[closest, 5] == 0:
                    self.junctions[closest, 4] = 32767  # junction fully used - make it look like it is far away
                if np.array_equal(cell, self.junctions[closest, 0:2]):
                    # continuing from current junction = cell
                    previous = np.copy(cell)
                else:
                    # switched to a closer junction - get the valid neighbors for it
                    previous = np.copy(self.junctions[closest, 0:2])  # start from it
                    # get the four neighbors for current cell and the "main distance" to indicate preferable direction
                    cell_neighbors = np.hstack((
                        previous + directions,
                        np.sum((self.end_pos - previous) * directions, axis=1)[:, None]
                        ))
                    # pick the ones which are corridors and not visited yet
                    valid_neighbors = cell_neighbors[(self.blocks[cell_neighbors[:, 0], cell_neighbors[:, 1]] == 0)]
                # select the "best route" i.e. simply the one that takes us towards the end_pos most
                cell = valid_neighbors[np.argmax(valid_neighbors[:, 2]), 0:2]
                self.draw_cell(cell, previous, self.path_color)

            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()

        pygame.display.flip()
        self.save_image()
        i_cnt = 0

        # retract to starting position to show the route.
        previous = np.copy(cell)
        self.junctions_used = 0
        while self.running and not np.array_equal(cell, self.start_pos):
            self.blocks[cell[0], cell[1]] = 4  # mark as the correct route
            # find the way back. While this takes time it avoids storing all paths in memory.
            cell_neighbors = cell + directions
            valid_neighbors = cell_neighbors[(self.blocks[cell_neighbors[:, 0], cell_neighbors[:, 1]] == 2)]
            if np.shape(valid_neighbors)[0] == 1:
                # one way to go only
                cell = valid_neighbors[0, 0:2]
            else:
                # a junction. Find it in junctions to select direction (the "previous cell" stored in the junction - now returning to it).
                cell = self.junctions[:self.junction_nr + 1, 2:4][(self.junctions[:self.junction_nr + 1, 0] == previous[0]) &
                                                                  (self.junctions[:self.junction_nr + 1, 1] == previous[1])][0]
                self.junctions_used += 1
            self.draw_cell(cell, previous, self.solution_color)
            previous = np.copy(cell)

            i_cnt += 1
            if i_cnt > 50:
                i_cnt = 0
                pygame.display.flip()
                self.save_image()

        self.blocks[cell[0], cell[1]] = 4  # mark starting cell as route
        # ensure display is updated
        pygame.display.flip()

        self.save_image()

    def draw_cell(self, cell, previous, color):

        # draw passage from cell to neighbor. As these are always adjacent can min/max be used.
        min_coord = (np.flip(np.minimum(cell, previous)) * self.screen_block_size + self.screen_block_offset).astype(np.int16)
        max_coord = (np.flip(np.maximum(cell, previous)) * self.screen_block_size + int(self.screen_block_size) + self.screen_block_offset).astype(np.int16)
        pygame.draw.rect(self.screen, color, (min_coord, max_coord - min_coord))

        if self.slow_mode or pygame.time.get_ticks() > self.prev_update + 16:  # increase the addition for faster but less frequent screen updates
            self.prev_update = pygame.time.get_ticks()
            pygame.display.flip()

            # when performing display flip, handle pygame events as well.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_f:
                        self.toggle_fullscreen()
                    if event.key == pygame.K_m:
                        self.toggle_slow_mode()
        if self.slow_mode:
            pygame.time.wait(3)

    def toggle_info_display(self):

        # switch between a windowed display and full screen
        self.info_display = not(self.info_display)
        if self.info_display:
            self.plot_info(self.last_message)
        else:
            x = (self.screen_size[0] - self.screen_info.get_size()[0]) // 2
            self.screen.fill(self.background_color, (x, 10, self.screen_info.get_size()[0], self.screen_info.get_size()[1]))
            pygame.display.update((x, 10, self.screen_info.get_size()[0], self.screen_info.get_size()[1]))

    def toggle_slow_mode(self):

        # switch between a windowed display and full screen
        self.slow_mode = not(self.slow_mode)
        self.plot_info(self.last_message)
    
    def toggle_save_mode(self):

        # switch between a windowed display and full screen
        self.is_save_img = not(self.is_save_img)
        self.plot_info(self.last_message)

    def plot_info(self, phase_msg):

        # show info

        if self.info_display:

            while self.screen_info.get_locked():
                self.screen_info.unlock()
            self.screen_info.fill(self.background_color)

            y = 0
            x = 0
            info_msg = 'i:     Info display ON/OFF'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            if self.slow_mode:
                info_msg = 'm:     Slow mode ON/OFF (on)'
            else:
                info_msg = 'm:     Slow mode ON/OFF (off)'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)

            if self.is_save_img:
                info_msg = 'x:     Save image ON/OFF (on)'
            else:
                info_msg = 'x:     Save image ON/OFF (off)'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)

            info_msg = 's:     Save .png image'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            info_msg = 'ESC:   Exit'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            y = 0
            x = 310
            pygame.draw.line(self.screen_info, self.info_color, (x - 10, y), (x - 10, y + 75))
            info_msg = 'Space:  Solve maze / next maze'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            info_msg = 'd:      Increase cell size'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            info_msg = 'a:      Decrease cell size'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            info_msg = 'Mouse:  Select start & end'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            y = 0
            x = 700
            pygame.draw.line(self.screen_info, self.info_color, (x - 10, y), (x - 10, y + 75))
            self.last_message = phase_msg
            y = self.plot_info_msg(self.screen_info, x, y, phase_msg)
            info_msg = f'Maze size: {self.block_size[1]} x {self.block_size[0]} = {(self.block_size[1] * self.block_size[0])} cells'
            y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            if phase_msg[:12] == 'Maze solved.':
                solution_cells = np.count_nonzero(self.blocks == 4)
                visited_cells = solution_cells + np.count_nonzero(self.blocks == 2)
                info_msg = f'Cell size: {self.cell_size:2d}, solution: {solution_cells} cells'
                y = self.plot_info_msg(self.screen_info, x, y, info_msg)
                info_msg = f'(Visited:  {visited_cells}, junctions: {self.junctions_used})'
                y = self.plot_info_msg(self.screen_info, x, y, info_msg)
            else:
                info_msg = f'Cell size: {self.cell_size:2d}'
                y = self.plot_info_msg(self.screen_info, x, y, info_msg)

            # copy to screen
            x = (self.screen_size[0] - self.screen_info.get_size()[0]) // 2
            self.screen.blit(self.screen_info, (x, 10))
            pygame.display.update((x, 10, self.screen_info.get_size()[0], self.screen_info.get_size()[1])) 
    def plot_info_msg(self, screen, x, y, msg):
        
        f_screen = self.font.render(msg, False, self.info_color, self.background_color)
        f_screen.set_colorkey(self.background_color)
        screen.blit(f_screen, (x, y))
        return y + 16

    def toggle_winner_display(self):
        # switch between a windowed display and full screen
        #self.info_display = not(self.info_display)

        x = (self.screen_size[0] - self.screen_info.get_size()[0]) // 2
        y = self.screen.get_size()[1] //2 - self.screen_info.get_size()[1]//2
        
        self.screen.fill(self.background_color, (x, y, self.screen_info.get_size()[0], self.screen_info.get_size()[1]))

        info_msg = f'YOU WWIN, Press [SPACE] to regenerate a new maze, or [ESC] to escape'
        f_screen = self.font.render(info_msg, False, self.info_color, self.background_color)
        f_screen.set_colorkey(self.background_color)

        msg_x= (self.screen_info.get_size()[0] - f_screen.get_size()[0])//2
        msg_y = y + f_screen.get_size()[1]

        screen.blit(f_screen, (msg_x, msg_y))
        self.screen.blit(self.screen_info, (x, 10))

        pygame.display.update((x, y, self.screen_info.get_size()[0], self.screen_info.get_size()[1]))

    def toggle_fullscreen(self):

        # toggle between fullscreen and windowed mode
        screen_copy = self.screen.copy()
        pygame.display.toggle_fullscreen()
        self.screen.blit(screen_copy, (0, 0))
        pygame.display.flip()

    def save_image(self):
        if not self.is_save_img:
            return
        # save maze as a png image. Use the first available number to avoid overwriting a previous image.
        for file_nr in range(1, 1000):
            file_name = 'img/Mazegif_' + ('00' + str(file_nr))[-3:] + '.png'
            if not exists(file_name):
                pygame.image.save(self.screen, file_name)
                break
    def set_pos_start(self,x, y):
        cell = np.array([x,y])
        # make sure is within array
        if cell[0] >= 1 and cell[1] >= 1 and cell[0] <= np.shape(self.blocks)[0] - 2 and cell[1] <= np.shape(self.blocks)[1] - 2:
            # make sure is not in a wall
            if self.blocks[cell[0], cell[1]] != 1:
                    self.draw_cell(self.start_pos, self.start_pos, self.maze_color)  # previous start cell back to maze_solver color
                    self.start_pos = np.copy(cell)
                    self.draw_cell(cell, cell, self.start_color)  # new start cell to start color
                    if(np.array_equal(self.start_pos, self.end_pos)):
                        self.toggle_winner_display()
                    pygame.display.flip()
    def pause(self):

        # wait for exit (window close or ESC key) or continue (space bar) or other user controls

        running = True
        pausing = True
        is_start_pos = True

        while pausing:

            event = pygame.event.wait()  # wait for user input, yielding to other processes

            if event.type == pygame.QUIT:
                pausing = False
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pausing = False
                if event.key == pygame.K_f:
                    self.toggle_fullscreen()
                if event.key == pygame.K_s:
                    # save screen as png image
                    self.save_image()
                if event.key == pygame.K_i:
                    self.toggle_info_display()  
                if event.key == pygame.K_m:
                    self.toggle_slow_mode()
                if event.key == pygame.K_x:
                    self.toggle_save_mode()
                if event.key == pygame.K_a:
                    self.cell_size -= 1
                    if self.cell_size < 1:
                        self.cell_size = 1
                    pausing = False
                if event.key == pygame.K_d:
                    self.cell_size += 1
                    if self.cell_size > min(self.rect[2], self.rect[3]) // 10:
                        self.cell_size = min(self.rect[2], self.rect[3]) // 10
                    pausing = False
                if event.key == pygame.K_ESCAPE:
                    pausing = False
                    running = False
                if event.key == pygame.K_0:
                    self.solution_type = 0
                elif event.key == pygame.K_1:
                    self.solution_type = 1
                elif event.key == pygame.K_2:
                    self.solution_type = 2
                elif event.key == pygame.K_3:
                    self.solution_type = 3
                elif event.key == pygame.K_4:
                    self.solution_type = 4
                if event.key == pygame.K_UP:
                    self.set_pos_start(self.start_pos[0]-1, self.start_pos[1])
                elif event.key == pygame.K_DOWN:
                    self.set_pos_start(self.start_pos[0]+1, self.start_pos[1])
                elif event.key == pygame.K_LEFT:
                    self.set_pos_start(self.start_pos[0], self.start_pos[1] -1)
                elif event.key == pygame.K_RIGHT:
                    self.set_pos_start(self.start_pos[0], self.start_pos[1] +1)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # left button: choose start and end position.
                    mouse_pos = np.asarray(pygame.mouse.get_pos())
                    cell = np.flip((mouse_pos - self.screen_block_offset) // (self.screen_block_size)).astype(np.int)
                    # make sure is within array
                    if cell[0] >= 1 and cell[1] >= 1 and cell[0] <= np.shape(self.blocks)[0] - 2 and cell[1] <= np.shape(self.blocks)[1] - 2:
                        # make sure is not in a wall
                        if self.blocks[cell[0], cell[1]] != 1:
                            # position is valid - change start or end position to it
                            if is_start_pos:
                                self.draw_cell(self.start_pos, self.start_pos, self.maze_color)  # previous start cell back to maze_solver color
                                self.start_pos = np.copy(cell)
                                self.draw_cell(cell, cell, self.start_color)  # new start cell to start color
                            else:
                                self.draw_cell(self.end_pos, self.end_pos, self.maze_color)  # previous end cell back to maze_solver color
                                self.end_pos = np.copy(cell)
                                self.draw_cell(cell, cell, self.end_color)  # new end cell to end color
                            is_start_pos = not(is_start_pos)  # alternate between changing start cell and end cell positions
                            pygame.display.flip()

        return running


if __name__ == '__main__':

    # Generate and display the Maze. Then solve it.
    # Left mouse button: generate a new maze.
    # ESC or close the window: Quit.

    # set screen size and initialize it
    pygame.display.init()
    disp_size = (1920, 1080)
    disp_size = (1280, 720)
    info_display = False
    screen = pygame.display.set_mode(disp_size)
    pygame.display.set_caption('Magic Maze by Team 11')
    running = True

    # initialize maze solver with bogus data to make it available
    maze_solver = MazeSolver(screen, (0, 0, 100, 100), np.ones((1, 1)), np.array([1, 1]), np.array([1, 1]))
    maze_solver.info_display = info_display
    maze_solver.cell_size =20  # cell size in pixels

    is_menu = True
    spriteTitle = pygame.image.load('TestTitle.png')
    while is_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_SPACE]:
                is_menu = False
            if pressed[pygame.K_ESCAPE]:
                pygame.quit()
        screen.fill((0,0,0))
        screen.blit(spriteTitle, (0,0))
        pygame.display.update()
    while running:

        # intialize a maze, given size (y, x)
        cell_size = maze_solver.cell_size
        rect = np.array([0, info_display * 80, disp_size[0], disp_size[1] - info_display * 80])  # the rect inside which to draw the maze.
        maze = maze_generator.Maze(rect[2] // (cell_size * 2) - 1, rect[3] // (cell_size * 2) - 1)
        maze.screen = screen  # if this is set, the maze generation process will be displayed in a window. Otherwise not.
        screen.fill((0, 0, 0))
        maze.screen_size = np.asarray(disp_size)
        maze.screen_block_size = np.min(rect[2:4] / np.flip(maze.block_size))
        maze.screen_block_offset = rect[0:2] + (rect[2:4] - maze.screen_block_size * np.flip(maze.block_size)) // 2
        maze.slow_mode = maze_solver.slow_mode

        maze_solver.block_size = maze.block_size
        maze_solver.cell_size = cell_size
        maze_solver.plot_info('Generating a maze.')
        start_time = pygame.time.get_ticks()
        # generate the maze - parameter: corridor length (optional)
        blocks = maze.gen_maze_2D()
        maze_solver.slow_mode = maze.slow_mode

        if maze.running:

            maze_solver.plot_info('Maze ready.  Time: {:0.2f} seconds.'.format((pygame.time.get_ticks() - start_time) / 1000.0))
            blocks_copy = np.copy(blocks)
            screen_copy = screen.copy()
            # default start and end in maze corners
            prev_start_pos = np.array([-1, -1], dtype=np.int)
            prev_end_pos = np.array([-1, -1], dtype=np.int)
            prev_msg = maze_solver.last_message
            prev_mode = maze_solver.slow_mode
            prev_info = maze_solver.info_display
            end_pos = np.asarray(np.shape(blocks), dtype=np.int) - 2  # bottom right corner
            start_pos = np.array([1, 1], dtype=np.int)

            maze_solver = MazeSolver(screen, rect, blocks, start_pos, end_pos)

            maze_solver.last_message = prev_msg
            maze_solver.slow_mode = prev_mode
            maze_solver.info_display = prev_info
            maze_solver.cell_size = cell_size
            maze_solver.draw_cell(start_pos, start_pos, maze_solver.start_color)
            maze_solver.draw_cell(end_pos, end_pos, maze_solver.end_color)
            pygame.display.flip()

            prev_cell_size = np.copy(maze_solver.cell_size)
            running = maze_solver.pause()
            while running and maze_solver.cell_size == prev_cell_size \
                    and not (np.array_equal(maze_solver.start_pos, prev_start_pos) and np.array_equal(maze_solver.end_pos, prev_end_pos)):
                maze_solver.plot_info('Solving the maze.')
                # reset maze_solver in case getting another solution for the same maze
                maze_solver.blocks = np.copy(blocks_copy)
                maze_solver.screen.blit(screen_copy, (0, 0))
                maze_solver.junction_nr = -1
                maze_solver.draw_cell(maze_solver.end_pos, maze_solver.end_pos, maze_solver.end_color)
                start_time = pygame.time.get_ticks()
                maze_solver.solve_maze()  # this actually solves the maze.
                maze_solver.draw_cell(maze_solver.start_pos, maze_solver.start_pos, maze_solver.start_color)
                maze_solver.draw_cell(maze_solver.end_pos, maze_solver.end_pos, maze_solver.end_color)
                pygame.display.flip()
                if maze_solver.running:
                    maze_solver.plot_info('Maze solved. Time: {:0.2f} seconds.'.format((pygame.time.get_ticks() - start_time) / 1000.0))
                    prev_start_pos = np.copy(maze_solver.start_pos)
                    prev_end_pos = np.copy(maze_solver.end_pos)
                    if running:
                        # wait for exit (window close or ESC key) or new maze (space bar) etc.
                        running = maze_solver.pause()

                else:
                    running = False

        else:
            running = False

        info_display = maze_solver.info_display

    # exit; close display, stop music
    pygame.quit()
    exit()

