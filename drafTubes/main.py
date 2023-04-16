import pygame
import random
import math
from pygame import mixer

# initialize the pygame
pygame.init()

# create the screen
screen = pygame.display.set_mode((800,600))

# background
background = pygame.image.load("pixel-bg-fixed.png")
# background sound
mixer.music.load("background-music.wav")
mixer.music.play(-1)

# Title and Icon
pygame.display.set_caption("boxU")
icon = pygame.image.load("iconGame.png")
pygame.display.set_icon(icon)

# Player 
playerImg = pygame.image.load("player.png")
playerX = 370
playerY = 480
playerX_change = 0

# Enemy 
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
num_of_enemies = 6


for i in range(num_of_enemies):
    enemyImg.append(pygame.image.load("enemy.png"))
    enemyX.append(random.randint(0,500))
    enemyY.append(random.randint(30,50))
    enemyX_change.append(4)
    enemyY_change.append(40) 

# bullet 
# ready - you can't see the bullet on the screen
# fire - the bullet is currently moving
bulletImg = pygame.image.load("bullet-pixel.png")
bulletX = 0
bulletY = 480
bulletX_change = 0
bulletY_change = 2 # <- ini untuk mengatur kecepatan peluru
bullet_state = "ready"

# score
score_value = 0
font = pygame.font.Font("ConsolaMono-Bold.ttf",32)
textX = 10
textY = 10

# game over text
over_font = pygame.font.Font("ConsolaMono-Bold.ttf",64)

def show_score(x,y):
    score = font.render("Score : " + str(score_value),True, (255,255,255))
    screen.blit(score, (x,y))
    
def game_over_text():
    over_text = over_font.render("GAME OVER",True, (255,255,255))
    screen.blit(over_text, (200,250))
    
    

def player(x,y):
    screen.blit(playerImg, (x,y))

def enemy(x,y,i):
    screen.blit(enemyImg[i], (x,y))

def fire_bullet(x,y):
    global bullet_state
    bullet_state = "fire"
    screen.blit(bulletImg, (x+16,y+10))
    
def isCollision(enemyX, enemyY, bulletX, bulletY):
    distance = math.sqrt((math.pow(enemyX - bulletX,2)) + (math.pow(enemyY-bulletY,2))) 
    if distance < 27:
        return True
    else:
        return False

    
    

# ----- ini agar windows tidak no responding aka Game Loop -----
running = True
while running:
    # RGB - Red, Green, Blue
    screen.fill((0,0,0))
    # background image
    screen.blit(background, (0,0))
    
            
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # if keystroke is pressed check wheter its right or left
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playerX_change = -0.6
            if event.key == pygame.K_RIGHT:
                playerX_change = 0.6
            if event.key == pygame.K_SPACE:
                if bullet_state == "ready":
                    # suara bullet ketika nembak
                    bullet_Sound = mixer.Sound("laserGun-effect.wav")
                    bullet_Sound.play()
                    # Get the current x coordinate of the spaceship 
                    bulletX = playerX
                    fire_bullet(playerX,bulletY)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                playerX_change = 0 #ini yg bikin gerak kanan kiri sendiri
    
    # 5 = 5 + -0.1 -> 5 = 5 - 0.1            
    playerX += playerX_change
    
    # agar player tidak melebihi border
    if playerX <= 0:
        playerX = 0
    elif playerX >= 736:
        playerX = 736
    
    # enemy movement
    for i in range(num_of_enemies):
        # Game Over !!! ADA bug
        if enemyY[i] > 200:
            for j in range(num_of_enemies):
                enemyY[j] = 5
            game_over_text()
            break
        
        enemyX[i] += enemyX_change[i]
        if enemyX[i] <= 0:
            enemyX_change[i] = 0.4
            enemyY[i] += enemyY_change[i]
        elif enemyX[i] >= 736:
            enemyX_change[i] = -0.4
            enemyY[i] += enemyY_change[i]
        
        # Collision
        collision = isCollision(enemyX[i], enemyY[i], bulletX, bulletY)
        if collision:
            # suara ketika musuh kena peluru
            # bullet_Sound = mixer.Sound("laserGun-effect.wav")
            # bullet_Sound.play()
            
            bulletY = 480
            bullet_state = "ready"
            score_value += 1
            # print(score_value)
            enemyX[i] = random.randint(0,735)
            enemyY[i] = random.randint(50,150)
            
        enemy(enemyX[i], enemyY[i], i)
        
    # Bullet movement
    if bulletY <=0:
        bulletY = 480
        bullet_state = "ready"
        
    if bullet_state is "fire":
        fire_bullet(bulletX, bulletY)
        bulletY -= bulletY_change
        
    player(playerX,playerY)
    show_score(textX,textY)
    # enemy(enemyX,enemyY)
    pygame.display.update()
# ----- #################################### -----