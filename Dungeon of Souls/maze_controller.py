# Mengimport modul yang diperlukan
import numpy as np
import tcod   # Untuk game berbasis ASCII
import random
from enum import Enum
from main import Ghoul

# Mengubah koordinat layar ke labirin (melakukan operasi pada game)
def translate_screen_to_maze(in_coords, in_size=22):
    return int(in_coords[0] / in_size), int(in_coords[1] / in_size)

# Mengubah koordinat labirin ke layar (menampilkan objek ke layar)
def translate_maze_to_screen(in_coords, in_size=22):
    return in_coords[0] * in_size, in_coords[1] * in_size

# Kelas untuk menemukan jalur terpendek antara karakter player dengan jiwa jahat
class Pathfinder:
    def __init__(self, in_arr):
        try:
            # Membuat representasi grid (jalur) dan menggunakan algoritma A* untuk mencari jalur
            cost = np.array(in_arr, dtype=np.bool_).tolist()
            self.pf = tcod.path.AStar(cost=cost, diagonal=0)
        except ValueError:
            # Pesan error ditampilkan jika labirin (self.ascii_maze) belum dibuat 
            raise ValueError("Silahkan buat model labirin terlebih dahulu!") from None

    # Fungsi mendapatkan jalur dari titik awal ke titik tujuan
    def get_path(self, from_x, from_y, to_x, to_y) -> object:
        res = self.pf.get_path(from_x, from_y, to_x, to_y)
        return [(sub[1], sub[0]) for sub in res]

# Kelas untuk membuat labirin beserta logikanya
class GameController:
    def __init__(self):
        # Membuat labirin dengan ASCII
        self.ascii_maze = [
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "XP           XX            X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXXOXXXXX XX XXXXXOXXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X                          X",
            "X XXXX XX XXXXXXXX XX XXXX X",
            "X XXXX XX XXXXXXXX XX XXXX X",
            "X      XX    XX    XX      X",
            "XXXXXX XXXXX XX XXXXX XXXXXX",
            "XXXXXX XXXXX XX XXXXX XXXXXX",
            "XXXXXX XX     G    XX XXXXXX",
            "XXXXXX XX XXX  XXX XX XXXXXX",
            "XXXXXX XX X      X XX XXXXXX",
            "   G      X      X          ",
            "XXXXXX XX X      X XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "XXXXXX XX    G     XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "X            XX            X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X   XX       G        XX   X",
            "XXX XX XX XXXXXXXX XX XX XXX",
            "XXX XX XX XXXXXXXX XX XX XXX",
            "X      XX    XX    XX      X",
            "X XXXXXXXXXX XX XXXXXXXXXX X",
            "X XXXXXXXXXX XX XXXXXXXXXX X",
            "X   O                 O    X",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
        # Daftar tempat yang dapat diisi
        self.numpy_maze = []
        self.soul_spaces = []
        self.powerup_spaces = []
        self.reachable_spaces = []
        self.ghoul_spawns = []

        # Daftar warna / tipe untuk jiwa jahat
        self.ghoul_colors = [
            "images/ghoul.png",
            "images/ghoul_pink.png",
            "images/ghoul_orange.png",
            "images/ghoul_blue.png"
        ]

        # Menetapkan ukuran awal labirin, mengubah format ASCII ke numpy array, dan mencari jalurnya
        self.size = (0, 0)
        self.convert_maze_to_numpy()
        self.p = Pathfinder(self.numpy_maze)

    # Fungsi meminta jalur random baru untuk jiwa jahat
    def request_new_random_path(self, in_ghoul: Ghoul):
        random_space = random.choice(self.reachable_spaces)
        current_maze_coord = translate_screen_to_maze(in_ghoul.get_position())

        path = self.p.get_path(current_maze_coord[1], current_maze_coord[0], random_space[1],
                               random_space[0])
        test_path = [translate_maze_to_screen(item) for item in path]
        in_ghoul.set_new_path(test_path)

    # Fungsi untuk mengubah format ASCII labirin ke numpy array
    def convert_maze_to_numpy(self):
        # Tiap baris dalam labirin akan dicek
        for x, row in enumerate(self.ascii_maze):
            # Mengupdate ukuran labirin dan menyimpan representasi biner tiap kolom
            self.size = (len(row), x + 1)
            binary_row = []

            # Cek tiap kolom berdasarkan huruf yang ada di labirn ASCII
            for y, column in enumerate(row):
                # "G" berarti tempat jiwa jahat spawn
                if column == "G":
                    self.ghoul_spawns.append((y, x))

                # "X" berarti dinding dan tidak dapat dijadikan jalur
                if column == "X":
                    binary_row.append(0)

                # Selain "X" dan "G" berarti dapat dibuat jalur dan diisi objek   
                else:
                    binary_row.append(1)
                    self.soul_spaces.append((y, x))
                    self.reachable_spaces.append((y, x))

                    # "O" berarti tempat powerup berada
                    if column == "O":
                        self.powerup_spaces.append((y, x))

            # Menambahkan semua kolom binary_row ke dalam labirin
            self.numpy_maze.append(binary_row)


