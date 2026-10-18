import pygame


pygame.init()
screen = pygame.display.set_mode((1200, 800))
run = True

pic = pygame.image.load('assets/maze/blue_wl.png')
new_pic = pygame.transform.scale(pic, (500, 500))

while run:

        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                        run = False
        screen.blit(pic, (100, 20))
        pygame.display.update()
