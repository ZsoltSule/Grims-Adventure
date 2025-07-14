import sys
import pygame
import random
import os

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Grims Adventure')
        info = pygame.display.Info()
        self.native_size = (info.current_w, info.current_h)
        self.screen = pygame.display.set_mode(self.native_size, pygame.FULLSCREEN)
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.movement = [False, False]

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'start_screen': load_image('start_screen.png'),
            'victory_screen': load_image('victory_screen.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur = 12),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur = 12),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur = 16),
            'player/run': Animation(load_images('entities/player/run'), img_dur = 6),
            'player/jump': Animation(load_images('entities/player/jump')),
            'projectile': load_image('projectile.png'),
            'player/attack': load_image('attack.png')
        }

        self.sfx = {
            'jump' : pygame.mixer.Sound('data/sfx/jump.wav'),
            'attack' : pygame.mixer.Sound('data/sfx/attack.wav'),
            'hit' : pygame.mixer.Sound('data/sfx/hit.wav'),
            'death' : pygame.mixer.Sound('data/sfx/death.wav'),
            'enemy_attack' : pygame.mixer.Sound('data/sfx/enemy_attack.wav')
        }

        self.sfx['jump'].set_volume(0.2)
        self.sfx['attack'].set_volume(0.1)
        self.sfx['hit'].set_volume(0.2)
        self.sfx['death'].set_volume(0.2)
        self.sfx['enemy_attack'].set_volume(0.2)

        self.clouds = Clouds(self.assets['clouds'], count = 8)

        self.start_pos = (50, 50)
        self.player = Player(self, self.start_pos, (16, 16))

        self.tilemap = Tilemap(self, tile_size = 16)

        self.level = 0
        self.load_level(self.level)

        self.screenshake = 0

        self.paused = False

        self.attacks = []
        self.projectiles = []
        self.scroll = [0, 0]
    
    def get_letterbox(self, surf):
        scale_x = self.native_size[0] / surf.get_width()
        scale_y = self.native_size[1] / surf.get_height()
        scale = min(scale_x, scale_y)

        new_size = (int(surf.get_width() * scale), int(surf.get_height() * scale))
        scaled = pygame.transform.scale(surf, new_size)
        letterboxed = pygame.Surface(self.native_size)
        letterboxed.fill((0, 0, 0))  
        offset = ((self.native_size[0] - new_size[0]) // 2, (self.native_size[1] - new_size[1]) // 2)
        letterboxed.blit(scaled, offset)
        
        return letterboxed


    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.start_pos = spawner['pos']
                self.player.pos = list(self.start_pos)
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (16, 16)))  

        self.attacks = []
        self.projectiles = []
        self.scroll = [0, 0]
        self.transition = -30

    def pause_menu(self):
        font_button = pygame.font.Font(None, 24)

        button_width = 80
        button_height = 20

        resume_button = pygame.Rect((self.display.get_width() // 2 - button_width // 2, 80), (button_width, button_height))
        restart_button = pygame.Rect((self.display.get_width() // 2 - button_width // 2, 110), (button_width, button_height))
        exit_button = pygame.Rect((self.display.get_width() // 2 - button_width // 2, 140), (button_width, button_height))

        def draw_button(rect, text, hover = False):
            color = (200, 200, 200) if hover else (100, 100, 100)
            pygame.draw.rect(self.display, color, rect, border_radius = 8)
            txt = font_button.render(text, True, (0, 0, 0))
            self.display.blit(txt, (rect.x + rect.width // 2 - txt.get_width() // 2, rect.y + rect.height // 2 - txt.get_height() // 2))

        while self.paused:
            self.display_2.blit(self.assets['background'], (0, 0))  

            mouse_pos = pygame.mouse.get_pos()
            scaled_mouse_pos = (mouse_pos[0] * self.display.get_width() // self.screen.get_width(),
                                mouse_pos[1] * self.display.get_height() // self.screen.get_height())

            draw_button(resume_button, "Resume", resume_button.collidepoint(scaled_mouse_pos))
            draw_button(restart_button, "Restart", restart_button.collidepoint(scaled_mouse_pos))
            draw_button(exit_button, "Exit", exit_button.collidepoint(scaled_mouse_pos))

            self.display_2.blit(self.display, (0, 0))
            final_surf = self.get_letterbox(self.display_2)
            self.screen.blit(final_surf, (0, 0))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if resume_button.collidepoint(scaled_mouse_pos):
                        self.paused = False
                    elif restart_button.collidepoint(scaled_mouse_pos):
                        self.paused = False
                        self.restart_level()
                    elif exit_button.collidepoint(scaled_mouse_pos):
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = False

            self.clock.tick(60)


    def start_screen(self):
        font_button = pygame.font.Font(None, 24)

        start_screen = pygame.transform.scale(self.assets['start_screen'], self.display_2.get_size())

        button_width = 80
        button_height = 20

        start_button = pygame.Rect((self.display.get_width() // 2 - button_width // 2, 110), (button_width, button_height))
        exit_button = pygame.Rect((self.display.get_width() // 2 - button_width // 2, 140), (button_width, button_height))

        def draw_button(rect, text, hover = False):
            color = (180, 180, 180) if hover else (120, 120, 120)
            pygame.draw.rect(self.display, color, rect, border_radius = 8)
            txt = font_button.render(text, True, (0, 0, 0))
            self.display.blit(txt, (rect.x + rect.width // 2 - txt.get_width() // 2, rect.y + rect.height // 2 - txt.get_height() // 2))

        waiting = True
        while waiting:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(start_screen, (0, 0))

            mouse_pos = pygame.mouse.get_pos()
            scaled_mouse_pos = (mouse_pos[0] * self.display.get_width() // self.screen.get_width(),
                                mouse_pos[1] * self.display.get_height() // self.screen.get_height())

            draw_button(start_button, "Start", start_button.collidepoint(scaled_mouse_pos))
            draw_button(exit_button, "Exit", exit_button.collidepoint(scaled_mouse_pos))

            self.display_2.blit(self.display, (0, 0))
            final_surf = self.get_letterbox(self.display_2)
            self.screen.blit(final_surf, (0, 0))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.collidepoint(scaled_mouse_pos):
                        waiting = False
                    elif exit_button.collidepoint(scaled_mouse_pos):
                        pygame.quit()
                        sys.exit()
        self.clock.tick(60)


    def restart_level(self):
        self.tilemap = Tilemap(self, tile_size = 16)

        self.attacks = []
        self.projectiles = []
        self.scroll = [0, 0]
        self.enemies = []

        self.load_level(self.level)

        self.player.air_time = 0
    
    def congratulations_screen(self):
        font_button = pygame.font.Font(None, 20)
        
        victory_screen = pygame.transform.scale(self.assets['victory_screen'], self.display_2.get_size())

        button_width = 80
        button_height = 20
        quit_button = pygame.Rect((self.display.get_width() // 2 - button_width // 2, 160), (button_width, button_height))

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(victory_screen, (0, 0))
            overlay = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.display.blit(overlay, (0, 0))

            mouse_pos = pygame.mouse.get_pos()
            scaled_mouse_pos = (mouse_pos[0] * self.display.get_width() // self.screen.get_width(),
                                mouse_pos[1] * self.display.get_height() // self.screen.get_height())

            hover = quit_button.collidepoint(scaled_mouse_pos)
            pygame.draw.rect(self.display, (180, 180, 180) if hover else (120, 120, 120), quit_button, border_radius=8)
            txt = font_button.render("Exit Game", True, (0, 0, 0))
            self.display.blit(txt, (quit_button.x + quit_button.width // 2 - txt.get_width() // 2,
                                    quit_button.y + quit_button.height // 2 - txt.get_height() // 2))

            self.display_2.blit(self.display, (0, 0))
            final_surf = self.get_letterbox(self.display_2)
            self.screen.blit(final_surf, (0, 0))    
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if quit_button.collidepoint(scaled_mouse_pos):
                        pygame.quit()
                        sys.exit()


    def run(self):
        
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.05)
        pygame.mixer.music.play(-1)
    
        self.start_screen()

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))

            self.screenshake = max(0, self.screenshake - 1)

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    if self.level + 1 >= len(os.listdir('data/maps')):
                        self.congratulations_screen()
                        return
                    else:
                        self.level += 1
                        self.load_level(self.level)


            if self.transition < 0:
                self.transition += 1

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.clouds.update()
            self.clouds.render(self.display, offset = render_scroll)
            self.tilemap.render(self.display, offset = render_scroll)

            for enemy in self.enemies.copy():
                enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)

            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            if self.player.air_time > 180:
                self.sfx['death'].play()
                self.screenshake = max(16, self.screenshake) 
                self.restart_level()
                continue

            self.player.render(self.display, offset = render_scroll)

            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                elif projectile[2] > 90:
                    self.projectiles.remove(projectile)
                elif self.player.rect().collidepoint(projectile[0]):
                    self.sfx['death'].play()
                    self.projectiles.remove(projectile)
                    self.screenshake = max(16, self.screenshake)
                    self.restart_level()
                    continue

            for attack in self.attacks.copy():
                attack[0][0] += attack[1]
                attack[2] += 1
                img = self.assets['player/attack']
                self.display.blit(img, (attack[0][0] - img.get_width() / 2 - render_scroll[0], attack[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(attack[0]):
                    self.attacks.remove(attack)
                elif attack[2] > 60:
                    self.attacks.remove(attack)
                else:
                    for enemy in self.enemies:
                        if enemy.rect().collidepoint(attack[0]):
                            self.sfx['hit'].play()
                            self.screenshake = max(16, self.screenshake)
                            self.enemies.remove(enemy)
                            self.attacks.remove(attack)
                            break
            
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhoutte = display_mask.to_surface(setcolor = (0, 0, 0, 180), unsetcolor = (0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhoutte, (offset))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                       if self.player.jump():
                           self.sfx['jump'].play()
                    if event.key == pygame.K_SPACE:
                        self.player.attack()
                    if event.key == pygame.K_ESCAPE:
                        self.paused = True
                        self.pause_menu()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, 
                                                                      self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - 
                                  self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            final_surf = self.get_letterbox(self.display_2)
            self.screen.blit(final_surf, screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)

Game().run()
