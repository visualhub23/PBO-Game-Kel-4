# Mengimport modul yang diperlukan
import pygame
from enum import Enum
from maze_controller import *

# Menetapkan posisi gambar dan arah karakter saat bergerak
class Direction(Enum):
    DOWN = -90
    RIGHT = 0
    UP = 90
    LEFT = 180
    NONE = 360

# Menetapkan skor untuk masing-masing objek yang didapat
class ScoreType(Enum):
    SOUL = 10
    POWERUP = 50
    GHOUL = 400

# Menetapkan perilaku jiwa jahat antara mengejar player atau tersebar di labirin
class GhoulBehaviour(Enum):
    CHASE = 1
    SCATTER = 2

# Untuk suara background dan efek lainnya
pygame.mixer.init()
pygame.mixer.music.load('sounds/ambiance.wav')
pygame.mixer.music.play()

kill_ghoul = pygame.mixer.Sound('sounds/deathghoul.wav')
kill_ghoul.set_volume(0.3)
kill_player = pygame.mixer.Sound('sounds/deathhero.wav')
kill_player.set_volume(0.3)

# Mengubah koordinat layar ke labirin (melakukan operasi pada game)
def translate_screen_to_maze(in_coords, in_size=22):
    return int(in_coords[0] / in_size), int(in_coords[1] / in_size)

# Mengubah koordinat labirin ke layar (menampilkan objek ke layar)
def translate_maze_to_screen(in_coords, in_size=22):
    return in_coords[0] * in_size, in_coords[1] * in_size

# Kelas untuk objek
class GameObject:
    # Renderer, koordinat posisi, ukuran, warna, bentuk objek
    def __init__(self, in_surface, x, y,
                 in_size: int, in_color=(255, 0, 0),
                 is_circle: bool = False):
        self._size = in_size
        self._renderer: GameRenderer = in_surface
        self._surface = in_surface._screen
        self.y = y
        self.x = x
        self._color = in_color
        self._circle = is_circle
        self._shape = pygame.Rect(self.x, self.y, in_size, in_size)

    def draw(self):
        if self._circle:
            pygame.draw.circle(self._surface,
                               self._color,
                               (self.x, self.y),
                               self._size)
        else:
            rect_object = pygame.Rect(self.x, self.y, self._size, self._size)
            pygame.draw.rect(self._surface,
                             self._color,
                             rect_object,
                             border_radius=1)
    
    # Fungsi memperbarui kondisi game secara berkala
    def tick(self):
        pass
    
    # Fungsi ambil bentuk objek
    def get_shape(self):
        return pygame.Rect(self.x, self.y, self._size, self._size)

    # Fungsi menetapkan posisi objek
    def set_position(self, in_x, in_y):
        self.x = in_x
        self.y = in_y

    # Fungsi mengambil posisi objek
    def get_position(self):
        return (self.x, self.y)

# Kelas untuk tembok turunan dari GameObject
class Wall(GameObject):
    def __init__(self, in_surface, x, y, in_size: int, in_color=(255, 0, 0)):
        super().__init__(in_surface, x * in_size, y * in_size, in_size, in_color)

# Kelas untuk jiwa turunan dari GameObject
class Soul(GameObject):
    def __init__(self, in_surface, x, y):
        super().__init__(in_surface, x, y, 4, (0, 255, 0), True)

# Kelas untuk powerup turunan dari GameObject
class Powerup(GameObject):
    def __init__(self, in_surface, x, y):
        super().__init__(in_surface, x, y, 8, (255, 255, 255), True)

# Kelas untuk objek yang bergerak turunan dari GameObject
class MovableObject(GameObject):
    # Arah saat ini, arah yang tersimpan sementara, arah terakhir, antrian lokasi, target selanjutnya
    def __init__(self, in_surface, x, y, in_size: int, in_color=(255, 0, 0), is_circle: bool = False):
        super().__init__(in_surface, x, y, in_size, in_color, is_circle)
        self.current_direction = Direction.NONE
        self.direction_buffer = Direction.NONE
        self.last_working_direction = Direction.NONE
        self.location_queue = []
        self.next_target = None
        self.image = pygame.image.load('images/ghoul.png')

    # Fungsi ambil lokasi selanjutnya dari antrian
    def get_next_location(self):
        return None if len(self.location_queue) == 0 else self.location_queue.pop(0)

    # Fungsi menetapkan arah objek
    def set_direction(self, in_direction):
        self.current_direction = in_direction
        self.direction_buffer = in_direction

    # Fungsi ketika bertabrakan dengan tembok
    def collides_with_wall(self, in_position):
        # Membuat sebuah area yang sama dengan objek yang melakukan tabrakan
        collision_rect = pygame.Rect(in_position[0], in_position[1], self._size, self._size)
        collides = False
        walls = self._renderer.get_walls()

        # Di cek apakah objek bertabrakan dengan dinding
        for wall in walls:
            collides = collision_rect.colliderect(wall.get_shape())
            if collides: break
        return collides

    # Fungsi untuk menetapkan posisi selanjutnya bagi objek
    def check_collision_in_direction(self, in_direction: Direction):
        desired_position = (0, 0)
        if in_direction == Direction.NONE: return False, desired_position
        if in_direction == Direction.UP:
            desired_position = (self.x, self.y - 1)
        elif in_direction == Direction.DOWN:
            desired_position = (self.x, self.y + 1)
        elif in_direction == Direction.LEFT:
            desired_position = (self.x - 1, self.y)
        elif in_direction == Direction.RIGHT:
            desired_position = (self.x + 1, self.y)

        # Ketika ternyata menabrak tembok, arah selanjutnya diambil dan disimpan
        return self.collides_with_wall(desired_position), desired_position

    # Fungsi pergerakan otomatis
    def automatic_move(self, in_direction: Direction):
        pass

    def tick(self):
        # Memperbarui status saat objek sampai targer dan menghandle pergerakan otomatis
        self.reached_target()
        self.automatic_move(self.current_direction)

    # Fungsi saat sudah sampai target
    def reached_target(self):
        pass

    # Fungsi untuk menggambar objek ke layar
    def draw(self):
        self.image = pygame.transform.scale(self.image, (22, 22))
        self._surface.blit(self.image, self.get_shape())

# Kelas untuk karakter player turunan dari MovableObject
class Hero(MovableObject):
    # Posisi terakhir yang tak menabrak objek, gambar karakter
    def __init__(self, in_surface, x, y, in_size: int):
        super().__init__(in_surface, x, y, in_size, (255, 255, 0), False)
        self.last_non_colliding_position = (0, 0)
        self.player = pygame.image.load("images/player.png")
        self.image = self.player

    def tick(self):
        # Jika melewati batas layar, akan diteleport ke posisi yang berlawanan
        if self.x < 0:
            self.x = self._renderer._width

        if self.x > self._renderer._width:
            self.x = 0

        self.last_non_colliding_position = self.get_position()

        # Jika tak tabrakan, maka terus berjalan sesuai posisi saat ini
        if self.check_collision_in_direction(self.direction_buffer)[0]:
            self.automatic_move(self.current_direction)
        
        # Jika tabrakan dan sebelumnya menekan tombol lain maka simpan arah tersebut
        else:
            self.automatic_move(self.direction_buffer)
            self.current_direction = self.direction_buffer

        # Jika tabrakan dan tidak menekan tombol lain maka akan dikembalikan ke posisi sebelumnya yang tak tabrakan
        if self.collides_with_wall((self.x, self.y)):
            self.set_position(self.last_non_colliding_position[0], self.last_non_colliding_position[1])

        # Memperbarui status saat mengambil jiwa dan saat membunuh jiwa jahat
        self.handle_soul_pickup()
        self.handle_ghouls()

    # Fungsi pergerakan otomatis bagi karakter player
    def automatic_move(self, in_direction: Direction):
        # Simpan hasil cek jika tabrakan atau tidak
        collision_result = self.check_collision_in_direction(in_direction)

        desired_position_collides = collision_result[0]

        # Jika sudah tak terjadi tabrakan, ubah posisi
        if not desired_position_collides:
            self.last_working_direction = self.current_direction
            desired_position = collision_result[1]
            self.set_position(desired_position[0], desired_position[1])

        # Jika terjadi tabrakan, posisi tetap seperti yang sebelumnya berhasil
        else:
            self.current_direction = self.last_working_direction

    # Fungsi saat mengambil jiwa
    def handle_soul_pickup(self):
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        souls = self._renderer.get_souls()
        powerups = self._renderer.get_powerups()
        game_objects = self._renderer.get_game_objects()
        soul_to_remove = None

        # Saat jiwa ditabrak / diambil maka akan dihapus jiwa tersebut dan menambah skor
        for soul in souls:
            collides = collision_rect.colliderect(soul.get_shape())
            if collides and soul in game_objects:
                game_objects.remove(soul)
                self._renderer.add_score(ScoreType.SOUL)
                soul_to_remove = soul

        # Hapus jiwa jika masih ada
        if soul_to_remove is not None:
            souls.remove(soul_to_remove)

        # Jika jiwa telah diambil semua, game dimenangkan
        if len(self._renderer.get_souls()) == 0:
            self._renderer.set_won()

        # Jika tabrakan dengan powerup, aktifkan kekuatannya dan tambah skor
        for powerup in powerups:
            collides = collision_rect.colliderect(powerup.get_shape())
            if collides and powerup in game_objects:
                if not self._renderer.is_power_active():
                    game_objects.remove(powerup)
                    self._renderer.add_score(ScoreType.POWERUP)
                    self._renderer.activate_power()

    # Fungsi menangani saat bertabrakan dengan jiwa jahat
    def handle_ghouls(self):
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        ghouls = self._renderer.get_ghouls()
        game_objects = self._renderer.get_game_objects()
        
        for ghoul in ghouls:
            collides = collision_rect.colliderect(ghoul.get_shape())
            if collides and ghoul in game_objects:
                # Jika menabrak dengan powerup masih aktif, bunuh jiwa jahat dan tambah skor serta respawn jiwa jahatnya
                if self._renderer.is_power_active():
                    game_objects.remove(ghoul)
                    kill_ghoul.play()
                    self._renderer.add_score(ScoreType.GHOUL)
                    translated = translate_maze_to_screen(ghoul_spawn)
                    ghoul = Ghoul(game_renderer, translated[0], translated[1], unified_size, dungeon_game,
                                  dungeon_game.ghoul_colors[random.randint(0,3)])
                    self._renderer.add_ghoul(ghoul)

                # Jika menabrak tanpa powerup aktif, player mati
                else:
                    if not self._renderer.get_won():
                        self._renderer.kill_hero()
                        kill_player.play()

    # Untuk menggambar kembali karakter player dengan kondisi telah diputar sesuai arah sekarang
    def draw(self):
        half_size = self._size / 2
        self.image = self.player
        self.image = pygame.transform.rotate(self.image, self.current_direction.value)
        super(Hero, self).draw()

# Kelas untuk jiwa jahat turunan dari MovableObject
class Ghoul(MovableObject):
    # Kontroler game, gambar jiwa jahat saat keadaan normal dan keadaan takut
    def __init__(self, in_surface, x, y, in_size: int, in_game_controller, sprite_path="images/ghoul_fright.png"):
        super().__init__(in_surface, x, y, in_size)
        self.game_controller = in_game_controller
        self.sprite_normal = pygame.image.load(sprite_path)
        self.sprite_fright = pygame.image.load("images/ghoul_fright.png")

    # Fungsi saat mencapai target
    def reached_target(self):
        # Mengambil lokasi target selanjutnya dan mengkalkulasi arahnya
        if (self.x, self.y) == self.next_target:
            self.next_target = self.get_next_location()
        self.current_direction = self.calculate_direction_to_next_target()

    # Fungsi membuat jalur baru untuk jiwa jahat
    def set_new_path(self, in_path):
        for item in in_path:
            self.location_queue.append(item)
        self.next_target = self.get_next_location()

    # Fungsi kalkulasi arah ke target selanjutnya
    def calculate_direction_to_next_target(self) -> Direction:
        if self.next_target is None:
            # Jika mode jiwa jahat sedang mengejar dan powerup tak aktif, jiwa jahat akan meminta jalur player sekarang
            if self._renderer.get_current_mode() == GhoulBehaviour.CHASE and not self._renderer.is_power_active():
                self.request_path_to_player(self)

            # Jika jiwa jahat di mode tersebar, maka akan meminta jalur random baru
            else:
                self.game_controller.request_new_random_path(self)
            return Direction.NONE

        # Menghitung perbedaan koordinat ghoul
        diff_x = self.next_target[0] - self.x
        diff_y = self.next_target[1] - self.y
        if diff_x == 0:
            return Direction.DOWN if diff_y > 0 else Direction.UP
        if diff_y == 0:
            return Direction.LEFT if diff_x < 0 else Direction.RIGHT

        if self._renderer.get_current_mode() == GhoulBehaviour.CHASE and not self._renderer.is_power_active():
            self.request_path_to_player(self)
        else:
            self.game_controller.request_new_random_path(self)
        return Direction.NONE

    # Fungsi meminta jalur ke player
    def request_path_to_player(self, in_ghoul):
        player_position = translate_screen_to_maze(in_ghoul._renderer.get_hero_position())
        current_maze_coord = translate_screen_to_maze(in_ghoul.get_position())
        path = self.game_controller.p.get_path(current_maze_coord[1], current_maze_coord[0], player_position[1],
                                               player_position[0])

        new_path = [translate_maze_to_screen(item) for item in path]
        in_ghoul.set_new_path(new_path)

    # Fungsi untuk jiwa jahat bergerak otomatis
    def automatic_move(self, in_direction: Direction):
        if in_direction == Direction.UP:
            self.set_position(self.x, self.y - 1)
        elif in_direction == Direction.DOWN:
            self.set_position(self.x, self.y + 1)
        elif in_direction == Direction.LEFT:
            self.set_position(self.x - 1, self.y)
        elif in_direction == Direction.RIGHT:
            self.set_position(self.x + 1, self.y)

    # Fungsi menggambar jiwa jahat
    def draw(self):
        self.image = self.sprite_fright if self._renderer.is_power_active() else self.sprite_normal
        super(Ghoul, self).draw()

# Kelas untuk render game
class GameRenderer:
    # Elemen game seperti pengatur frame, karakter, skor, mode, event, nyawa
    def __init__(self, in_width: int, in_height: int):
        pygame.init()
        self._width = in_width
        self._height = in_height
        self._screen = pygame.display.set_mode((in_width, in_height))
        pygame.display.set_caption('Dungeon of Souls')
        self._clock = pygame.time.Clock()
        self._done = False
        self._won = False
        self._game_objects = []
        self._walls = []
        self._souls = []
        self._powerups = []
        self._ghouls = []
        self._hero: Hero = None
        self._lives = 3
        self._score = 0
        self._score_soul_pickup = 10
        self._score_ghoul_eaten = 400
        self._score_powerup_pickup = 50
        self._power_active = False
        self._current_mode = GhoulBehaviour.SCATTER
        self._mode_switch_event = pygame.USEREVENT + 1
        self._power_end_event = pygame.USEREVENT + 2
        
        # Tiap mode / fase akan bergerak dengan waktu tertentu
        self._modes = [
            (7, 20),
            (7, 20),
            (5, 20),
            (5, 999999) # Mode / fase terakhir memiliki waktu tak terbatas
        ]
        self._current_phase = 0

    # Fungsi mengatur kondisi didalam game secara berkala
    def tick(self, in_fps: int):
        # Membersihkan layar
        black = (0, 0, 0)

        # Mengatur game saat di mode tertentu
        self.handle_mode_switch()
        while not self._done:
            for game_object in self._game_objects:
                game_object.tick()
                game_object.draw()

            # Menampilkan text
            self.display_text(f"[Score: {self._score}]  [Lives: {self._lives}]")

            # Jika nyawa player habis, tampilkan "YOU DIED" dan game akan berakhir
            if self._hero is None:
                self.display_text("YOU DIED", (self._width / 2 - 200, self._height / 2 - 75), 100)
                self._done = True 

            # Jika player menang, tampilkan "YOU WON" dan game akan berakhir    
            if self.get_won(): 
                self.display_text("YOU WON", (self._width / 2 - 200, self._height / 2 - 75), 100)
                self._done = True

            # Perbarui tampilan layar, mengatur fps, dan bersihkan layar    
            pygame.display.flip()
            self._clock.tick(in_fps)
            self._screen.fill(black)
            self._handle_events()

        # Delay waktu untuk keluar dari game secara otomatis
        if self._hero is None:
            pygame.time.delay(3000)

        # Keluar game    
        pygame.quit()
        print("Game over")

    # Fungsi mengatur mode tertentu
    def handle_mode_switch(self):
        # Menyimpan fase saat ini beserta waktunya
        current_phase_timings = self._modes[self._current_phase]
        print(f"Current phase: {str(self._current_phase)}, current_phase_timings: {str(current_phase_timings)}")
        
        # Waktu untuk menyebar dan mengejar player
        scatter_timing = current_phase_timings[0]
        chase_timing = current_phase_timings[1]

        # Jika mode mengejar, lanjut fase selanjutnya dan mulai menyebar
        if self._current_mode == GhoulBehaviour.CHASE:
            self._current_phase += 1
            self.set_current_mode(GhoulBehaviour.SCATTER)
        else:
            self.set_current_mode(GhoulBehaviour.CHASE)

        used_timing = scatter_timing if self._current_mode == GhoulBehaviour.SCATTER else chase_timing

        # Waktu untuk mengubah mode
        pygame.time.set_timer(self._mode_switch_event, used_timing * 1000)

    # Fungsi menetapkan waktu aktif powerup
    def start_power_timeout(self):
        pygame.time.set_timer(self._power_end_event, 15000)  # 15s

    # Fungsi menambahkan objek ke daftar objek game
    def add_game_object(self, obj: GameObject):
        self._game_objects.append(obj)

    # Fungsi menambahkan jiwa ke daftar jiwa
    def add_soul(self, obj: GameObject):
        self._game_objects.append(obj)
        self._souls.append(obj)

    # Fungsi menambahkan jiwa jahat ke daftar jiwa jahat
    def add_ghoul(self, obj: GameObject):
        self._game_objects.append(obj)
        self._ghouls.append(obj)

    # Fungsi menambahkan powerup ke daftar powerup
    def add_powerup(self, obj: GameObject):
        self._game_objects.append(obj)
        self._powerups.append(obj)

    # Fungsi aktifkan powerup dan mengubah mode jiwa jahat menjadi menyebar
    def activate_power(self):
        self._power_active = True
        self.set_current_mode(GhoulBehaviour.SCATTER)
        self.start_power_timeout()

    # Fungsi getter & setter saat menang
    def set_won(self):
        self._won = True

    def get_won(self):
        return self._won

    # Fungsi menambahkan skor
    def add_score(self, in_score: ScoreType):
        self._score += in_score.value

    # Fungsi untuk dapatkan posisi karakter player
    def get_hero_position(self):
        return self._hero.get_position() if self._hero != None else (0, 0)

    # Fungsi getter & setter untuk menetapkan mode
    def set_current_mode(self, in_mode: GhoulBehaviour):
        self._current_mode = in_mode

    def get_current_mode(self):
        return self._current_mode

    # Fungsi mengakhiri game
    def end_game(self):
        if self._hero in self._game_objects:
            self._game_objects.remove(self._hero)
        self._hero = None

    # Fungsi untuk membunuh player
    def kill_hero(self):
        self._lives -= 1
        self._hero.set_position(22, 22)
        self._hero.set_direction(Direction.NONE)
        if self._lives == 0: self.end_game()

    # Fungsi untuk menampilkan text ke layar
    def display_text(self, text, in_position=(32, 0), in_size=30):
        font = pygame.font.SysFont('Arial', in_size)
        text_surface = font.render(text, False, (255, 255, 255))
        self._screen.blit(text_surface, in_position)

    # Fungsi cek jika power aktif
    def is_power_active(self):
        return self._power_active

    # Fungsi menambahkan tembok ke daftar tembok
    def add_wall(self, obj: Wall):
        self.add_game_object(obj)
        self._walls.append(obj)

    # Fungsi mendapatkan objek
    def get_walls(self):
        return self._walls

    def get_souls(self):
        return self._souls

    def get_ghouls(self):
        return self._ghouls

    def get_powerups(self):
        return self._powerups

    def get_game_objects(self):
        return self._game_objects

    # Fungsi menambahkan karakter player ke daftar karakter player
    def add_hero(self, in_hero):
        self.add_game_object(in_hero)
        self._hero = in_hero

    # Fungsi untuk mengatur peristiwa / event tertentu
    def _handle_events(self):
        for event in pygame.event.get():
            # Jika ada perintah keluar dari game atau keluar secara mendadak maka game berakhir
            if event.type == pygame.QUIT:
                self._done = True

            # Jika ada perubahan mode, lakukan proses ubah mode
            if event.type == self._mode_switch_event:
                self.handle_mode_switch()

            # Jika waktu powerup habis, tetapkan bahwa power sudah tak aktif
            if event.type == self._power_end_event:
                self._power_active = False

        # Untuk menetapkan pergerakan karakter player dengan keyboard
        pressed = pygame.key.get_pressed()
        if self._hero is None: return
        if pressed[pygame.K_UP]:
            self._hero.set_direction(Direction.UP)
        elif pressed[pygame.K_LEFT]:
            self._hero.set_direction(Direction.LEFT)
        elif pressed[pygame.K_DOWN]:
            self._hero.set_direction(Direction.DOWN)
        elif pressed[pygame.K_RIGHT]:
            self._hero.set_direction(Direction.RIGHT)

# Ketika program dijalankan maka akan melakukan kode dibawah
if __name__ == "__main__":
    # Menetapkan ukuran keseluruhan objek, labirin bawah tanah, dan proses render game
    unified_size = 22
    dungeon_game = GameController()
    size = dungeon_game.size
    game_renderer = GameRenderer(size[0] * unified_size, size[1] * unified_size)

    # Untuk tiap baris didalam model labirin akan dicek bagian untuk temboknya, dan jika benar maka tambahkan tembok
    for y, row in enumerate(dungeon_game.numpy_maze):
        for x, column in enumerate(row):
            if column == 0:
                game_renderer.add_wall(Wall(game_renderer, x, y, unified_size))

    # Untuk tiap koordinat / tempat jiwa dapat diisi dalam model labirin akan ditambahkan jiwa
    for soul_space in dungeon_game.soul_spaces:
        translated = translate_maze_to_screen(soul_space)
        soul = Soul(game_renderer, translated[0] + unified_size / 2, translated[1] + unified_size / 2)
        game_renderer.add_soul(soul)

    # Untuk tiap koordinat / tempat powerup dapat diisi dalam model labirin akan ditambahkan powerup
    for powerup_space in dungeon_game.powerup_spaces:
        translated = translate_maze_to_screen(powerup_space)
        powerup = Powerup(game_renderer, translated[0] + unified_size / 2, translated[1] + unified_size / 2)
        game_renderer.add_powerup(powerup)

    # Untuk tiap koordinat / tempat jiwa jahat dapat diisi dalam model labirin akan ditambahkan jiwa jahat
    for i, ghoul_spawn in enumerate(dungeon_game.ghoul_spawns):
        translated = translate_maze_to_screen(ghoul_spawn)
        ghoul = Ghoul(game_renderer, translated[0], translated[1], unified_size, dungeon_game,
                      dungeon_game.ghoul_colors[i % 4])
        game_renderer.add_ghoul(ghoul)

    # Inisialisasi player
    player = Hero(game_renderer, unified_size, unified_size, unified_size)

    # Menambahkan karakter player, menetapkan mode jiwa jahat, dan menetapkan fps
    game_renderer.add_hero(player)
    game_renderer.set_current_mode(GhoulBehaviour.CHASE)
    game_renderer.tick(90)