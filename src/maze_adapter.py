from mazegenerator import MazeGenerator

# methods to call: 'generate', 'maze', 'maze_entry', 'maze_exit', 'shortest_path'


class MazeAdapter:
    def __init__(self, width, height):
        self.maze_gen = MazeGenerator()
