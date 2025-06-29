import pygame
import random
import sys
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Game elements (all in pixels)
PLAYER_WIDTH = 100  # Reduced from 120
PLAYER_HEIGHT = 40  # Increased from 24 for better proportions
PLAYER_SPEED = 10
BALL_RADIUS = 24  # Increased from 18 to make carrots larger
BALL_SPAWN_INTERVAL = 1800  # ms
MIN_BALL_DISTANCE = 220  # pixels
MAX_BALLS_ON_SCREEN = 4

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    PAUSED = 4

class Level(Enum):
    EASY = 1
    HARD = 2

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            # Load the bunny image and scale it to appropriate size
            original_image = pygame.image.load('img/bunny_facing_backwards__f5e25797-removebg-preview.png').convert_alpha()
            # Scale the image while maintaining aspect ratio
            aspect_ratio = original_image.get_width() / original_image.get_height()
            new_width = PLAYER_WIDTH * 1.5  # Reduced from 2x to make bunny smaller
            new_height = int(new_width / aspect_ratio)
            self.image = pygame.transform.scale(original_image, (int(new_width), int(new_height)))
        except:
            # Fallback to rectangle if image loading fails
            self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
            self.image.fill(BLUE)
            pygame.draw.rect(self.image, WHITE, (0, 0, PLAYER_WIDTH, PLAYER_HEIGHT), 2)
        
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.speed = PLAYER_SPEED
        
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

class Ball(pygame.sprite.Sprite):
    def __init__(self, level, is_bomb=False):
        super().__init__()
        self.level = level
        self.is_bomb = is_bomb
        self.time_to_bottom = 3.2  # seconds
        self.distance = SCREEN_HEIGHT + BALL_RADIUS * 2
        self.base_speed = self.distance / (self.time_to_bottom * FPS)
        
        # Load appropriate image based on whether it's a bomb or carrot
        try:
            if self.is_bomb:
                original_image = pygame.image.load('img/bomb__e3efbbb0-removebg-preview.png').convert_alpha()
                size = BALL_RADIUS * 2 * 1.5  # Slightly smaller than carrots
            else:
                original_image = pygame.image.load('img/carrot__d385da94-removebg-preview.png').convert_alpha()
                size = BALL_RADIUS * 2 * 2.0  # Make carrots larger
                
            self.image = pygame.transform.scale(original_image, (int(size), int(size)))
        except:
            # Fallback to colored circles if image loading fails
            self.image = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
            if self.is_bomb:
                pygame.draw.circle(self.image, BLACK, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
                pygame.draw.circle(self.image, RED, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS-3)
            else:
                color = RED if level == Level.HARD else ORANGE
                pygame.draw.circle(self.image, color, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
                pygame.draw.circle(self.image, WHITE, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS, 2)
        
        self.rect = self.image.get_rect()
        self.reset()
        
    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        
        if self.level == Level.HARD:
            if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
                self.speedx = -self.speedx
            
        if self.rect.top > SCREEN_HEIGHT:
            self.reset()
            return False
        return True
    
    def reset(self):
        self.rect.y = -BALL_RADIUS * 2
        
        if self.level == Level.EASY:
            self.speedy = self.base_speed
            self.speedx = 0
        else:
            self.speedy = self.base_speed * random.uniform(0.9, 1.1)
            max_horizontal_speed = (SCREEN_WIDTH / 2) / (self.time_to_bottom * FPS)
            self.speedx = random.uniform(-max_horizontal_speed, max_horizontal_speed)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bunny")
        self.clock = pygame.time.Clock()
        self.state = GameState.MENU
        self.level = Level.EASY
        self.running = True
        self.score = 0
        self.high_score = 0
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)
        
        # Load and scale background image
        try:
            self.background = pygame.image.load('img/green_land_and_sun_with_box_image__e2ef39bf.png').convert()
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.background = None
        
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.balls = pygame.sprite.Group()
        
        # Create player
        self.player = Player()
        self.all_sprites.add(self.player)
        
        # Game timing
        self.last_spawn_time = 0
        self.spawn_interval = BALL_SPAWN_INTERVAL
        
        # Menu buttons
        button_width, button_height = 240, 60
        self.easy_button = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 220, button_width, button_height)
        self.hard_button = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 320, button_width, button_height)
        self.play_again_button = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 420, button_width, button_height)
        
        # Sound effects and music
        self.catch_sound = None
        self.game_over_sound = None
        self.background_music = None
        
        # Initialize sound system if available
        if pygame.mixer.get_init():
            try:
                # Load sound effects if available
                self.catch_sound = pygame.mixer.Sound('sound/catch.wav')
                self.game_over_sound = pygame.mixer.Sound('sound/game_over.wav')
            except:
                pass
                
            try:
                # Load and play background music
                pygame.mixer.music.load('sound/Summer Dawn - Freedom Trail Studio.mp3')
                pygame.mixer.music.set_volume(0.5)  # 50% volume
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            except:
                print("Could not load background music")
    
    def start_game(self, level):
        self.state = GameState.PLAYING
        self.level = level
        self.score = 0  # Reset score when starting a new game
        self.balls.empty()
        self.all_sprites.empty()
        self.all_sprites.add(self.player)
        self.last_spawn_time = pygame.time.get_ticks()
        # Restart music when starting a new game
        if pygame.mixer.get_init():
            pygame.mixer.music.rewind()
            pygame.mixer.music.play(-1)
    
    def is_safe_to_spawn(self, x_pos):
        for ball in self.balls:
            if abs(ball.rect.centerx - x_pos) < MIN_BALL_DISTANCE:
                return False
        return True
    
    def spawn_ball(self):
        max_attempts = 10
        for _ in range(max_attempts):
            x_pos = random.randint(BALL_RADIUS * 2, SCREEN_WIDTH - BALL_RADIUS * 2)
            if self.is_safe_to_spawn(x_pos):
                # 15% chance to spawn a bomb, 85% chance to spawn a carrot
                is_bomb = random.random() < 0.15
                ball = Ball(self.level, is_bomb=is_bomb)
                ball.rect.centerx = x_pos
                ball.rect.y = -BALL_RADIUS * 2
                # Make bombs fall slightly faster
                if is_bomb:
                    ball.speedy *= 1.2
                self.all_sprites.add(ball)
                self.balls.add(ball)
                return True
        return False
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Stop music before quitting
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                self.running = False
            
            if self.state == GameState.MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.easy_button.collidepoint(mouse_pos):
                        self.start_game(Level.EASY)
                    elif self.hard_button.collidepoint(mouse_pos):
                        self.start_game(Level.HARD)
            
            elif self.state == GameState.GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.play_again_button.collidepoint(mouse_pos):
                        self.state = GameState.MENU
            
            elif self.state == GameState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_p:
                        self.state = GameState.PAUSED
            
            elif self.state == GameState.PAUSED:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        self.state = GameState.PLAYING
    
    def update(self):
        if self.state != GameState.PLAYING:
            return
            
        current_time = pygame.time.get_ticks()
        
        if current_time - self.last_spawn_time > self.spawn_interval:
            if len(self.balls) < MAX_BALLS_ON_SCREEN:
                self.spawn_ball()
                self.last_spawn_time = current_time
            elif current_time - self.last_spawn_time > self.spawn_interval * 2:
                self.spawn_ball()
                self.last_spawn_time = current_time
            
        self.all_sprites.update()
        
        hits = pygame.sprite.spritecollide(self.player, self.balls, True)
        for hit in hits:
            if hit.is_bomb:
                # Game over if bomb is caught
                if self.game_over_sound:
                    self.game_over_sound.play()
                self.state = GameState.GAME_OVER
                return
            else:
                # Score point for catching a carrot
                self.score += 1
                if self.high_score < self.score:
                    self.high_score = self.score
                if self.catch_sound:
                    self.catch_sound.play()
            
        # Check all balls and handle those that go off screen
        for ball in list(self.balls):  # Create a copy of the list to safely remove items
            if ball.rect.top > SCREEN_HEIGHT:
                # If it's a carrot that reaches the bottom, game over
                if not ball.is_bomb:
                    ball.kill()
                    if self.game_over_sound:
                        self.game_over_sound.play()
                    self.state = GameState.GAME_OVER
                    return
                else:
                    # If it's a bomb that reaches the bottom, just remove it
                    ball.kill()
    
    def draw(self):
        # Draw background or fill with black if background loading failed
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BLACK)
        
        if self.state == GameState.MENU:
            # Title
            title = self.big_font.render('Bunny Food', True, PURPLE)
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
            
            # Buttons
            pygame.draw.rect(self.screen, ORANGE, self.easy_button, border_radius=10)
            pygame.draw.rect(self.screen, ORANGE, self.easy_button, 3, border_radius=10)
            easy_text = self.font.render('Level 1 - Mudah', True, WHITE)
            self.screen.blit(easy_text, (self.easy_button.centerx - easy_text.get_width()//2, 
                                        self.easy_button.centery - easy_text.get_height()//2))
            
            pygame.draw.rect(self.screen, RED, self.hard_button, border_radius=10)
            pygame.draw.rect(self.screen, RED, self.hard_button, 3, border_radius=10)
            hard_text = self.font.render('Level 2 - Sulit', True, WHITE)
            self.screen.blit(hard_text, (self.hard_button.centerx - hard_text.get_width()//2, 
                                        self.hard_button.centery - hard_text.get_height()//2))
            
            # High score
            if self.high_score > 0:
                hs_text = self.font.render(f'High Score: {self.high_score}', True, GREEN)
                self.screen.blit(hs_text, (SCREEN_WIDTH//2 - hs_text.get_width()//2, 400))
            
            # Instructions
            instr1 = self.small_font.render('Gunakan tombol kiri dan kanan untuk bergerak', True, WHITE)
            instr2 = self.small_font.render('Tangkap bola yang jatuh untuk mendapatkan poin', True, WHITE)
            self.screen.blit(instr1, (SCREEN_WIDTH//2 - instr1.get_width()//2, 480))
            self.screen.blit(instr2, (SCREEN_WIDTH//2 - instr2.get_width()//2, 510))
            
        elif self.state == GameState.PLAYING:
            # Draw all sprites
            self.all_sprites.draw(self.screen)
            
            # Score display
            score_text = self.font.render(f'Score: {self.score}', True, WHITE)
            self.screen.blit(score_text, (20, 20))
            
            # High score
            if self.high_score > 0:
                hs_text = self.small_font.render(f'High: {self.high_score}', True, GREEN)
                self.screen.blit(hs_text, (20, 60))
            
            # Level indicator
            level_color = ORANGE if self.level == Level.EASY else RED
            level_text = self.font.render(f'Level: {self.level.name}', True, level_color)
            self.screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 20, 20))
            
        elif self.state == GameState.PAUSED:
            # Draw game elements first
            self.all_sprites.draw(self.screen)
            
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            # Pause text
            pause_text = self.big_font.render('PAUSE', True, WHITE)
            self.screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, 
                                         SCREEN_HEIGHT//2 - pause_text.get_height()//2))
            
            # Instructions
            instr = self.small_font.render('Tekan ESC atau P untuk melanjutkan', True, WHITE)
            self.screen.blit(instr, (SCREEN_WIDTH//2 - instr.get_width()//2, 
                                    SCREEN_HEIGHT//2 + pause_text.get_height()))
            
        elif self.state == GameState.GAME_OVER:
            # Game over text
            game_over = self.big_font.render('GAME OVER', True, RED)
            self.screen.blit(game_over, (SCREEN_WIDTH//2 - game_over.get_width()//2, 150))
            
            # Final score
            score_text = self.font.render(f'Skor Anda: {self.score}', True, WHITE)
            self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 250))
            
            # High score
            if self.score == self.high_score and self.score > 0:
                new_hs = self.font.render('High Score Baru!', True, YELLOW)
                self.screen.blit(new_hs, (SCREEN_WIDTH//2 - new_hs.get_width()//2, 300))
            
            # Play again button
            pygame.draw.rect(self.screen, GREEN, self.play_again_button, border_radius=10)
            pygame.draw.rect(self.screen, WHITE, self.play_again_button, 3, border_radius=10)
            again_text = self.font.render('Main Lagi', True, BLACK)
            self.screen.blit(again_text, (self.play_again_button.centerx - again_text.get_width()//2, 
                                         self.play_again_button.centery - again_text.get_height()//2))
            
            # Instructions
            instr = self.small_font.render('Klik tombol di atas atau kembali ke menu utama', True, WHITE)
            self.screen.blit(instr, (SCREEN_WIDTH//2 - instr.get_width()//2, 500))
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
        
        pygame.quit()
        #sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()