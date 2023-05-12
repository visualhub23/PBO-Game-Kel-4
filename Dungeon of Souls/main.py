# Mengimport modul yang diperlukan
import pygame
from enum import Enum
from maze_controller import *

# Menetapkan posisi gambar karakter saat bergerak
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


def translate_screen_to_maze(in_coords, in_size=22):
    return int(in_coords[0] / in_size), int(in_coords[1] / in_size)


def translate_maze_to_screen(in_coords, in_size=22):
    return in_coords[0] * in_size, in_coords[1] * in_size

# Kelas untuk objek
class GameObject:
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

    def tick(self):
        pass

    def get_shape(self):
        return pygame.Rect(self.x, self.y, self._size, self._size)

    def set_position(self, in_x, in_y):
        self.x = in_x
        self.y = in_y

    def get_position(self):
        return (self.x, self.y)


class Wall(GameObject):
    def __init__(self, in_surface, x, y, in_size: int, in_color=(255, 0, 0)):
        super().__init__(in_surface, x * in_size, y * in_size, in_size, in_color)

class MovableObject(GameObject):
    def __init__(self, in_surface, x, y, in_size: int, in_color=(255, 0, 0), is_circle: bool = False):
        super().__init__(in_surface, x, y, in_size, in_color, is_circle)
        self.current_direction = Direction.NONE
        self.direction_buffer = Direction.NONE
        self.last_working_direction = Direction.NONE
        self.location_queue = []
        self.next_target = None
        self.image = pygame.image.load('images/ghoul.png')

    def get_next_location(self):
        return None if len(self.location_queue) == 0 else self.location_queue.pop(0)

    def set_direction(self, in_direction):
        self.current_direction = in_direction
        self.direction_buffer = in_direction

    def collides_with_wall(self, in_position):
        collision_rect = pygame.Rect(in_position[0], in_position[1], self._size, self._size)
        collides = False
        walls = self._renderer.get_walls()
        for wall in walls:
            collides = collision_rect.colliderect(wall.get_shape())
            if collides: break
        return collides

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

        return self.collides_with_wall(desired_position), desired_position

    def automatic_move(self, in_direction: Direction):
        pass

    def tick(self):
        self.reached_target()
        self.automatic_move(self.current_direction)

    def reached_target(self):
        pass
    
    def draw(self):
        self.image = pygame.transform.scale(self.image, (32, 32))
        self._surface.blit(self.image, self.get_shape())


class Hero(MovableObject):
    def __init__(self, in_surface, x, y, in_size: int):
        super().__init__(in_surface, x, y, in_size, (255, 255, 0), False)
        self.last_non_colliding_position = (0, 0)
        self.player = pygame.image.load("images/player.png")
        self.image = self.player

    def tick(self):
        # TELEPORT
        if self.x < 0:
            self.x = self._renderer._width

        if self.x > self._renderer._width:
            self.x = 0

        self.last_non_colliding_position = self.get_position()

        if self.check_collision_in_direction(self.direction_buffer)[0]:
            self.automatic_move(self.current_direction)
        else:
            self.automatic_move(self.direction_buffer)
            self.current_direction = self.direction_buffer

        if self.collides_with_wall((self.x, self.y)):
            self.set_position(self.last_non_colliding_position[0], self.last_non_colliding_position[1])

        self.handle_soul_pickup()
        self.handle_ghouls()

    def automatic_move(self, in_direction: Direction):
        collision_result = self.check_collision_in_direction(in_direction)

        desired_position_collides = collision_result[0]
        if not desired_position_collides:
            self.last_working_direction = self.current_direction
            desired_position = collision_result[1]
            self.set_position(desired_position[0], desired_position[1])
        else:
            self.current_direction = self.last_working_direction

    def handle_soul_pickup(self):
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        souls = self._renderer.get_souls()
        powerups = self._renderer.get_powerups()
        game_objects = self._renderer.get_game_objects()
        soul_to_remove = None
        for soul in souls:
            collides = collision_rect.colliderect(soul.get_shape())
            if collides and soul in game_objects:
                game_objects.remove(soul)
                self._renderer.add_score(ScoreType.SOUL)
                soul_to_remove = soul

        if soul_to_remove is not None:
            souls.remove(soul_to_remove)

        if len(self._renderer.get_souls()) == 0:
            self._renderer.set_won()

        for powerup in powerups:
            collides = collision_rect.colliderect(powerup.get_shape())
            if collides and powerup in game_objects:
                if not self._renderer.is_power_active():
                    game_objects.remove(powerup)
                    self._renderer.add_score(ScoreType.POWERUP)
                    self._renderer.activate_power()

    def handle_ghouls(self):
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        ghouls = self._renderer.get_ghouls()
        game_objects = self._renderer.get_game_objects()
        
        for ghoul in ghouls:
            collides = collision_rect.colliderect(ghoul.get_shape())
            if collides and ghoul in game_objects:
                if self._renderer.is_power_active():
                    game_objects.remove(ghoul)
                    kill_ghoul.play()
                    self._renderer.add_score(ScoreType.GHOUL)
                    translated = translate_maze_to_screen(ghoul_spawn)
                    ghoul = Ghoul(game_renderer, translated[0], translated[1], unified_size, dungeon_game,
                                  dungeon_game.ghoul_colors[random.randint(0,3)])
                    self._renderer.add_ghoul(ghoul)
                else:
                    if not self._renderer.get_won():
                        self._renderer.kill_hero()
                        kill_player.play()

    def draw(self):
        half_size = self._size / 2
        self.image = self.player
        self.image = pygame.transform.rotate(self.image, self.current_direction.value)
        super(Hero, self).draw()


class Ghoul(MovableObject):
    def __init__(self, in_surface, x, y, in_size: int, in_game_controller, sprite_path="images/ghoul_fright.png"):
        super().__init__(in_surface, x, y, in_size)
        self.game_controller = in_game_controller
        self.sprite_normal = pygame.image.load(sprite_path)
        self.sprite_fright = pygame.image.load("images/ghoul_fright.png")

    def reached_target(self):
        if (self.x, self.y) == self.next_target:
            self.next_target = self.get_next_location()
        self.current_direction = self.calculate_direction_to_next_target()

    def set_new_path(self, in_path):
        for item in in_path:
            self.location_queue.append(item)
        self.next_target = self.get_next_location()

    def calculate_direction_to_next_target(self) -> Direction:
        if self.next_target is None:
            if self._renderer.get_current_mode() == GhoulBehaviour.CHASE and not self._renderer.is_power_active():
                self.request_path_to_player(self)
            else:
                self.game_controller.request_new_random_path(self)
            return Direction.NONE

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

    def request_path_to_player(self, in_ghoul):
        player_position = translate_screen_to_maze(in_ghoul._renderer.get_hero_position())
        current_maze_coord = translate_screen_to_maze(in_ghoul.get_position())
        path = self.game_controller.p.get_path(current_maze_coord[1], current_maze_coord[0], player_position[1],
                                               player_position[0])

        new_path = [translate_maze_to_screen(item) for item in path]
        in_ghoul.set_new_path(new_path)

    def automatic_move(self, in_direction: Direction):
        if in_direction == Direction.UP:
            self.set_position(self.x, self.y - 1)
        elif in_direction == Direction.DOWN:
            self.set_position(self.x, self.y + 1)
        elif in_direction == Direction.LEFT:
            self.set_position(self.x - 1, self.y)
        elif in_direction == Direction.RIGHT:
            self.set_position(self.x + 1, self.y)

    def draw(self):
        self.image = self.sprite_fright if self._renderer.is_power_active() else self.sprite_normal
        super(Ghoul, self).draw()

class Soul(GameObject):
    def __init__(self, in_surface, x, y):
        super().__init__(in_surface, x, y, 4, (0, 255, 0), True)

class Powerup(GameObject):
    def __init__(self, in_surface, x, y):
        super().__init__(in_surface, x, y, 8, (255, 255, 255), True)

class GameRenderer:
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
        self._power_active = False # powerup, special ability
        self._current_mode = GhoulBehaviour.SCATTER
        self._mode_switch_event = pygame.USEREVENT + 1  # custom event
        self._power_end_event = pygame.USEREVENT + 2
        self._modes = [
            (7, 20),
            (7, 20),
            (5, 20),
            (5, 999999)  # 'infinite' chase seconds
        ]
        self._current_phase = 0

    def tick(self, in_fps: int):
        black = (0, 0, 0)

        self.handle_mode_switch()
        while not self._done:
            for game_object in self._game_objects:
                game_object.tick()
                game_object.draw()

            self.display_text(f"[Score: {self._score}]  [Lives: {self._lives}]")
            if self._hero is None:
                self.display_text("YOU DIED", (self._width / 2 - 200, self._height / 2 - 75), 100)
                self._done = True 
            if self.get_won(): 
                self.display_text("YOU WON", (self._width / 2 - 200, self._height / 2 - 75), 100)
                self._done = True
                
            pygame.display.flip()
            self._clock.tick(in_fps)
            self._screen.fill(black)
            self._handle_events()

        if self._hero is None:
            pygame.time.delay(3000)
            
        pygame.quit()
        print("Game over")

    def handle_mode_switch(self):
        current_phase_timings = self._modes[self._current_phase]
        print(f"Current phase: {str(self._current_phase)}, current_phase_timings: {str(current_phase_timings)}")
        scatter_timing = current_phase_timings[0]
        chase_timing = current_phase_timings[1]

        if self._current_mode == GhoulBehaviour.CHASE:
            self._current_phase += 1
            self.set_current_mode(GhoulBehaviour.SCATTER)
        else:
            self.set_current_mode(GhoulBehaviour.CHASE)

        used_timing = scatter_timing if self._current_mode == GhoulBehaviour.SCATTER else chase_timing
        pygame.time.set_timer(self._mode_switch_event, used_timing * 1000)

    def start_power_timeout(self):
        pygame.time.set_timer(self._power_end_event, 15000)  # 15s

    def add_game_object(self, obj: GameObject):
        self._game_objects.append(obj)

    def add_soul(self, obj: GameObject):
        self._game_objects.append(obj)
        self._souls.append(obj)

    def add_ghoul(self, obj: GameObject):
        self._game_objects.append(obj)
        self._ghouls.append(obj)

    def add_powerup(self, obj: GameObject):
        self._game_objects.append(obj)
        self._powerups.append(obj)

    def activate_power(self):
        self._power_active = True
        self.set_current_mode(GhoulBehaviour.SCATTER)
        self.start_power_timeout()

    def set_won(self):
        self._won = True

    def get_won(self):
        return self._won

    def add_score(self, in_score: ScoreType):
        self._score += in_score.value

    def get_hero_position(self):
        return self._hero.get_position() if self._hero != None else (0, 0)

    def set_current_mode(self, in_mode: GhoulBehaviour):
        self._current_mode = in_mode

    def get_current_mode(self):
        return self._current_mode

    def end_game(self):
        if self._hero in self._game_objects:
            self._game_objects.remove(self._hero)
        self._hero = None

    def kill_hero(self):
        self._lives -= 1
        self._hero.set_position(22, 22)
        self._hero.set_direction(Direction.NONE)
        if self._lives == 0: self.end_game()

    def display_text(self, text, in_position=(32, 0), in_size=30):
        font = pygame.font.SysFont('Arial', in_size)
        text_surface = font.render(text, False, (255, 255, 255))
        self._screen.blit(text_surface, in_position)

    def is_power_active(self):
        return self._power_active

    def add_wall(self, obj: Wall):
        self.add_game_object(obj)
        self._walls.append(obj)

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

    def add_hero(self, in_hero):
        self.add_game_object(in_hero)
        self._hero = in_hero

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._done = True

            if event.type == self._mode_switch_event:
                self.handle_mode_switch()

            if event.type == self._power_end_event:
                self._power_active = False

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

if __name__ == "__main__":
    unified_size = 22
    dungeon_game = GameController()
    size = dungeon_game.size
    game_renderer = GameRenderer(size[0] * unified_size, size[1] * unified_size)

    for y, row in enumerate(dungeon_game.numpy_maze):
        for x, column in enumerate(row):
            if column == 0:
                game_renderer.add_wall(Wall(game_renderer, x, y, unified_size))

    for soul_space in dungeon_game.soul_spaces:
        translated = translate_maze_to_screen(soul_space)
        soul = Soul(game_renderer, translated[0] + unified_size / 2, translated[1] + unified_size / 2)
        game_renderer.add_soul(soul)

    for powerup_space in dungeon_game.powerup_spaces:
        translated = translate_maze_to_screen(powerup_space)
        powerup = Powerup(game_renderer, translated[0] + unified_size / 2, translated[1] + unified_size / 2)
        game_renderer.add_powerup(powerup)

    for i, ghoul_spawn in enumerate(dungeon_game.ghoul_spawns):
        translated = translate_maze_to_screen(ghoul_spawn)
        ghoul = Ghoul(game_renderer, translated[0], translated[1], unified_size, dungeon_game,
                      dungeon_game.ghoul_colors[i % 4])
        game_renderer.add_ghoul(ghoul)

    player = Hero(game_renderer, unified_size, unified_size, unified_size)
    game_renderer.add_hero(player)
    game_renderer.set_current_mode(GhoulBehaviour.CHASE)
    game_renderer.tick(120)