import pygame, sys
from screeninfo import get_monitors
monitor = get_monitors()

screen_width = monitor[0].width
screen_height = monitor[0].height

WHITE = (255,255,255)
GREEN = (54,128,45)

field_width = (screen_width * 120) / 140
field_height = (screen_height * 85) / 100

# ??? unused
cancha_centro = (screen_width * 9.15) / 120

# numeric values that were constants 10 and 8 for a base resolution 1920x1080 rescalated for dynamic res.
grosor = int(screen_width * screen_height/ 207360)
grosor2 = int(screen_width * screen_height/ 259200)

penalty_area_height = (field_height * 55) / 85
penalty_area_width = (field_width * 16.50) / 120

goal_area_height = (field_height * 24.75) / 85
goal_area_width = (field_width * 5.50) / 120

arco_alto = (field_height * 24.75*7/18) / 85
arco_ancho = (field_width * 24.75*2/18)/ 85

area_padding = (15*field_height)/85
area_padding1 = area_padding + (15.125*penalty_area_height)/85
area_padding2 = area_padding1 + (7.5625 * goal_area_height)/85


the_capricious = (screen_width * screen_height) / 110000

FIELD_TOP_LEFT = [screen_width-field_width,screen_height-field_height]
FIELD_TOP_RIGHT = [field_width,screen_height-field_height]
FIELD_BOTTOM_LEFT = [screen_width-field_width,field_height]
FIELD_BOTTOM_RIGHT = [field_width,field_height]

clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))

#pygame.mixer.music.load("bg_music.mp3")
#pygame.mixer.music.play()

class SoccerField:
    def draw(self) -> None:
        # center circle
        pygame.draw.circle(screen, WHITE, [screen_width/2,screen_height/2], penalty_area_width/2, grosor)

        # half field band
        pygame.draw.line(screen, WHITE, [screen_width/2, screen_height-field_height], [screen_width/2, field_height], grosor)

        # field sidelines
        pygame.draw.line(screen, WHITE, [screen_width-field_width,field_height], [field_width,field_height], grosor)
        pygame.draw.line(screen, WHITE, [screen_width-field_width,screen_height-field_height], [field_width,screen_height-field_height], grosor)

        # field endlines
        pygame.draw.line(screen, WHITE, [field_width, screen_height-field_height], [field_width, field_height], grosor)
        pygame.draw.line(screen, WHITE, [screen_width-field_width, screen_height-field_height], [screen_width-field_width, field_height], grosor)

        # ball
        pygame.draw.circle(screen, WHITE, [screen_width/2,screen_height/2], the_capricious)

        # LEFT SIDE

        # penalty area

        pygame.draw.line(screen, (203,203,203), [screen_width-field_width, screen_height-field_height+area_padding], [screen_width-field_width+penalty_area_width,screen_height-field_height+area_padding], grosor)
        pygame.draw.line(screen, (203,203,203), [screen_width-field_width, field_height-area_padding], [screen_width-field_width+penalty_area_width,field_height-area_padding], grosor)

        pygame.draw.line(screen, (203,203,203), [screen_width-field_width+penalty_area_width, screen_height-field_height+area_padding], [screen_width-field_width+penalty_area_width,field_height-area_padding], grosor)


        # goal area
        pygame.draw.line(screen, (166,166,166), [screen_width-field_width,  screen_height-field_height+area_padding1], [screen_width-field_width+goal_area_width,  screen_height-field_height+area_padding1], grosor)
        pygame.draw.line(screen, (166,166,166), [screen_width-field_width,  screen_height-field_height+area_padding+penalty_area_height-area_padding1], [screen_width-field_width+goal_area_width, screen_height-field_height+area_padding+penalty_area_height-area_padding1], grosor)

        pygame.draw.line(screen,  (166,166,166), [screen_width-field_width+goal_area_width,screen_height-field_height+area_padding1], [screen_width-field_width+goal_area_width,screen_height-field_height+area_padding+penalty_area_height-area_padding1], grosor)


        # arco 
        pygame.draw.line(screen, (129,129,129), [screen_width-field_width,  screen_height-field_height+area_padding2], [screen_width-field_width-arco_ancho,  screen_height-field_height+area_padding2], grosor2)
        pygame.draw.line(screen, (129,129,129), [screen_width-field_width, screen_height-field_height+area_padding+penalty_area_height-area_padding2], [screen_width-field_width-arco_ancho, screen_height-field_height+area_padding+penalty_area_height-area_padding2], grosor2)

        pygame.draw.line(screen, (129,129,129), [screen_width-field_width-arco_ancho, screen_height-field_height+area_padding2], [screen_width-field_width-arco_ancho, screen_height-field_height+area_padding+penalty_area_height-area_padding2], grosor)

        # penalty box arc
        pygame.draw.circle(screen, (221,221,221), [screen_width-field_width+penalty_area_width, screen_height/2], penalty_area_width/2, grosor, True, False, False, True)

        # penalty kick mark
        pygame.draw.circle(screen, (0,0,0), [screen_width-field_width+goal_area_width+((penalty_area_width-goal_area_width)/2), screen_height/2], grosor, grosor)

        # corner marks
        pygame.draw.circle(screen, WHITE, FIELD_TOP_LEFT, int(goal_area_width/2), grosor, False, False, False, True)
        pygame.draw.circle(screen, WHITE, FIELD_TOP_RIGHT, int(goal_area_width/2), grosor, False, False, True, False)
        pygame.draw.circle(screen, WHITE, FIELD_BOTTOM_LEFT, int(goal_area_width/2), grosor, True, False, False, False)
        pygame.draw.circle(screen, WHITE, FIELD_BOTTOM_RIGHT, int(goal_area_width/2), grosor, False, True, False, False)


        # RIGHT SIDE

        # penalty area

        pygame.draw.line(screen, (203,203,203), [field_width, screen_height-field_height+area_padding], [field_width-penalty_area_width,screen_height-field_height+area_padding], grosor)
        pygame.draw.line(screen, (203,203,203), [field_width, field_height-area_padding], [field_width-penalty_area_width,field_height-area_padding], grosor)

        pygame.draw.line(screen, (203,203,203), [field_width-penalty_area_width, screen_height-field_height+area_padding], [field_width-penalty_area_width,field_height-area_padding], grosor)

        # goal area
        pygame.draw.line(screen, (166,166,166), [field_width,  screen_height-field_height+area_padding1], [field_width-goal_area_width,  screen_height-field_height+area_padding1], grosor)
        pygame.draw.line(screen, (166,166,166), [field_width,  screen_height-field_height+area_padding+penalty_area_height-area_padding1], [field_width-goal_area_width, screen_height-field_height+area_padding+penalty_area_height-area_padding1], grosor)

        pygame.draw.line(screen,  (166,166,166), [field_width-goal_area_width,screen_height-field_height+area_padding1], [field_width-goal_area_width,screen_height-field_height+area_padding+penalty_area_height-area_padding1], grosor)

        # arco 
        pygame.draw.line(screen, (129,129,129), [field_width,  screen_height-field_height+area_padding2], [field_width+arco_ancho,  screen_height-field_height+area_padding2], grosor2)
        pygame.draw.line(screen, (129,129,129), [field_width, screen_height-field_height+area_padding+penalty_area_height-area_padding2], [field_width+arco_ancho, screen_height-field_height+area_padding+penalty_area_height-area_padding2], grosor2)

        pygame.draw.line(screen, (129,129,129), [field_width+arco_ancho, screen_height-field_height+area_padding2], [field_width+arco_ancho, screen_height-field_height+area_padding+penalty_area_height-area_padding2], grosor)

        # penalty kick mark
        pygame.draw.circle(screen, (0,0,0), [field_width-goal_area_width-((penalty_area_width-goal_area_width)/2), screen_height/2], grosor, grosor)

        # penalty box arc
        pygame.draw.circle(screen, (221,221,221), [field_width-penalty_area_width, screen_height/2], penalty_area_width/2, grosor, False, True, True, False)

player_1 = pygame.image.load("PLAYER_1.png")
scaled_player = pygame.transform.scale(player_1, (100,100))
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    
    screen.fill(GREEN)
    field = SoccerField()
    field.draw()
    screen.blit(scaled_player, [screen_width/3, screen_height/3])
    screen.blit(scaled_player, [screen_width/3, 2*screen_height/3])
    screen.blit(scaled_player, [screen_width/3, screen_height/2])
    screen.blit(scaled_player, [2*screen_width/3, screen_height/3])
    screen.blit(scaled_player, [2*screen_width/3, 2*screen_height/3])
    screen.blit(scaled_player, [2*screen_width/3, screen_height/2])
    clock.tick(60)  # limits FPS to 60
    pygame.display.flip()
