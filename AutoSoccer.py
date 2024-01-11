import pygame, sys
from screeninfo import get_monitors
monitor = get_monitors()

screen_width = monitor[0].width
screen_height = monitor[0].height

WHITE = (255,255,255)
GREEN = (54,128,45)

field_width = (screen_width * 120) / 140
field_height = (screen_height * 85) / 100

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

clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
ball_img = pygame.image.load("src/img/ball.png")

class Ball: # Que sea un thread y en el while true haga el move() mientras la velocidad no sea 0 y cuando lo sea que se duerma y la despiertan con un hit
    def __init__(self, pos: list[float]) -> None:
        self.speed = [0.0, 0.0]
        self.x = pos[0]
        self.y = pos[1]
        self.last_touch = None
        self.image = ball_img
        self.scaled_ball = pygame.transform.scale(ball_img, (50, 50)) # to-do: rescalar dinamicamente
        self.img_rect = self.scaled_ball.get_rect(center=(self.x, self.y))

    def reposition(self, pos: list[float]) -> None:
        self.x = pos[0]
        self.y = pos[1]
        self.img_rect.topleft = (self.x, self.y)

    def draw(self) -> None:
        screen.blit(self.scaled_ball, self.img_rect)
    
    def reset_speed(self) -> None:
        self.speed = [0.0,0.0]

    def hit(self, speed, team_id) -> None:
        self.last_touch = team_id
        self.speed = speed
    
    def move(self, coef) -> None:
        if abs(self.speed[0]) > 0.005 or abs(self.speed[1] > 0.005): 
            self.x = self.x + self.speed[0]
            self.y = self.y + self.speed[1]
            self.reposition([self.x, self.y])
            self.speed[0] = self.speed[0] - self.speed[0] * coef
            self.speed[1] = self.speed[1] - self.speed[1] * coef
        else:
            self.speed[0] = 0
            self.speed[1] = 0

class SoccerField:
    def __init__(self, team_1, team_2, players) -> None:
        self.μ = 0.05 # ???
        self.state = "Begin" # throw_in | corner
        self.team_1 = team_1
        self.team_2 = team_2
        self.center_circle = [screen_width/2,screen_height/2]
        self.middle_line = ([screen_width/2, screen_height-field_height], [screen_width/2, field_height])
        self.bottom_sideline = ([screen_width-field_width,field_height], [field_width,field_height])
        self.upper_sideline = ([screen_width-field_width,screen_height-field_height], [field_width,screen_height-field_height])
        self.left_endline = ([field_width, screen_height-field_height], [field_width, field_height])
        self.right_endline = ([screen_width-field_width, screen_height-field_height], [screen_width-field_width, field_height])
        
        self.top_left_corner = [screen_width-field_width,screen_height-field_height]
        self.top_right_corner = [field_width,screen_height-field_height]
        self.bottom_left_corner = [screen_width-field_width,field_height]
        self.bottom_right_corner = [field_width,field_height]

        self.ls_penalty_area_upper = ([screen_width-field_width, screen_height-field_height+area_padding], [screen_width-field_width+penalty_area_width,screen_height-field_height+area_padding])
        self.ls_penalty_area_bottom = ([screen_width-field_width, field_height-area_padding], [screen_width-field_width+penalty_area_width,field_height-area_padding])
        self.ls_penalty_area_singleline = ([screen_width-field_width+penalty_area_width, screen_height-field_height+area_padding], [screen_width-field_width+penalty_area_width,field_height-area_padding])
        self.ls_goal_area_upper = ([screen_width-field_width,  screen_height-field_height+area_padding1], [screen_width-field_width+goal_area_width,  screen_height-field_height+area_padding1])
        self.ls_goal_area_bottom = ([screen_width-field_width,  screen_height-field_height+area_padding+penalty_area_height-area_padding1], [screen_width-field_width+goal_area_width, screen_height-field_height+area_padding+penalty_area_height-area_padding1])
        self.ls_goal_area_singleline = ([screen_width-field_width+goal_area_width,screen_height-field_height+area_padding1], [screen_width-field_width+goal_area_width,screen_height-field_height+area_padding+penalty_area_height-area_padding1])
        self.ls_arco_area_upper = ([screen_width-field_width,  screen_height-field_height+area_padding2], [screen_width-field_width-arco_ancho,  screen_height-field_height+area_padding2])
        self.ls_arco_area_bottom = ([screen_width-field_width, screen_height-field_height+area_padding+penalty_area_height-area_padding2], [screen_width-field_width-arco_ancho, screen_height-field_height+area_padding+penalty_area_height-area_padding2])
        self.ls_arco_area_singlelane = ([screen_width-field_width-arco_ancho, screen_height-field_height+area_padding2], [screen_width-field_width-arco_ancho, screen_height-field_height+area_padding+penalty_area_height-area_padding2])
        self.ls_penalty_box_arc = [screen_width-field_width+penalty_area_width, screen_height/2]
        self.ls_penalty_kick_mark = [screen_width-field_width+goal_area_width+((penalty_area_width-goal_area_width)/2), screen_height/2]


        self.ball_initial_pos = [screen_width/2,screen_height-field_height+area_padding2]
        self.ball = Ball(self.ball_initial_pos)

        self.rs_penalty_area_upper = ([field_width, screen_height-field_height+area_padding], [field_width-penalty_area_width,screen_height-field_height+area_padding])
        self.rs_penalty_area_bottom = ([field_width, field_height-area_padding], [field_width-penalty_area_width,field_height-area_padding])
        self.rs_penalty_area_singleline = ([field_width-penalty_area_width, screen_height-field_height+area_padding], [field_width-penalty_area_width,field_height-area_padding])
        self.rs_goal_area_upper = ([field_width,  screen_height-field_height+area_padding1], [field_width-goal_area_width,  screen_height-field_height+area_padding1])
        self.rs_goal_area_bottom = ([field_width,  screen_height-field_height+area_padding+penalty_area_height-area_padding1], [field_width-goal_area_width, screen_height-field_height+area_padding+penalty_area_height-area_padding1])
        self.rs_goal_area_singleline = ([field_width-goal_area_width,screen_height-field_height+area_padding1], [field_width-goal_area_width,screen_height-field_height+area_padding+penalty_area_height-area_padding1])
        self.rs_arco_area_upper = ([field_width,  screen_height-field_height+area_padding2], [field_width+arco_ancho,  screen_height-field_height+area_padding2])
        self.rs_arco_area_bottom = ([field_width, screen_height-field_height+area_padding+penalty_area_height-area_padding2], [field_width+arco_ancho, screen_height-field_height+area_padding+penalty_area_height-area_padding2])
        self.rs_arco_area_singlelane = ([field_width+arco_ancho, screen_height-field_height+area_padding2], [field_width+arco_ancho, screen_height-field_height+area_padding+penalty_area_height-area_padding2])
        self.rs_penalty_box_arc = [field_width-penalty_area_width, screen_height/2]
        self.rs_penalty_kick_mark = [field_width-goal_area_width-((penalty_area_width-goal_area_width)/2), screen_height/2]

    def draw(self) -> None:

        # center circle
        pygame.draw.circle(screen, WHITE, self.center_circle, penalty_area_width/2, grosor)

        # middlefield band
        pygame.draw.line(screen, WHITE, self.middle_line[0], self.middle_line[1], grosor)

        # field sidelines
        pygame.draw.line(screen, WHITE, self.upper_sideline[0], self.upper_sideline[1], grosor)
        pygame.draw.line(screen, WHITE, self.bottom_sideline[0], self.bottom_sideline[1], grosor)

        # field endlines
        pygame.draw.line(screen, WHITE, self.left_endline[0], self.left_endline[1], grosor)
        pygame.draw.line(screen, WHITE, self.right_endline[0], self.right_endline[1], grosor)

       

        # LEFT SIDE

        # penalty area

        pygame.draw.line(screen, (203,203,203), self.ls_penalty_area_upper[0], self.ls_penalty_area_upper[1], grosor)
        pygame.draw.line(screen, (203,203,203), self.ls_penalty_area_bottom[0], self.ls_penalty_area_bottom[1], grosor)

        pygame.draw.line(screen, (203,203,203), self.ls_penalty_area_singleline[0], self.ls_penalty_area_singleline[1], grosor)


        # goal area
        pygame.draw.line(screen, (166,166,166), self.ls_goal_area_upper[0], self.ls_goal_area_upper[1], grosor)
        pygame.draw.line(screen, (166,166,166), self.ls_goal_area_bottom[0], self.ls_goal_area_bottom[1], grosor)

        pygame.draw.line(screen,  (166,166,166), self.ls_goal_area_singleline[0], self.ls_goal_area_singleline[1], grosor)


        # arco 
        pygame.draw.line(screen, (129,129,129), self.ls_arco_area_upper[0], self.ls_arco_area_upper[1], grosor2)
        pygame.draw.line(screen, (129,129,129), self.ls_arco_area_bottom[0], self.ls_arco_area_bottom[1], grosor2)

        pygame.draw.line(screen, (129,129,129), self.ls_arco_area_singlelane[0], self.ls_arco_area_singlelane[1], grosor)

        # penalty box arc
        pygame.draw.circle(screen, (221,221,221), self.ls_penalty_box_arc, penalty_area_width/2, grosor, True, False, False, True)

        # penalty kick mark
        pygame.draw.circle(screen, (0,0,0), self.ls_penalty_kick_mark, grosor, grosor)

        # corner marks
        pygame.draw.circle(screen, WHITE, self.top_left_corner, int(goal_area_width/2), grosor, False, False, False, True)
        pygame.draw.circle(screen, WHITE, self.top_right_corner, int(goal_area_width/2), grosor, False, False, True, False)
        pygame.draw.circle(screen, WHITE, self.bottom_left_corner, int(goal_area_width/2), grosor, True, False, False, False)
        pygame.draw.circle(screen, WHITE, self.bottom_right_corner, int(goal_area_width/2), grosor, False, True, False, False)


        # RIGHT SIDE

        # penalty area

        pygame.draw.line(screen, (203,203,203), self.rs_penalty_area_upper[0], self.rs_penalty_area_upper[1], grosor)
        pygame.draw.line(screen, (203,203,203), self.rs_penalty_area_bottom[0], self.rs_penalty_area_bottom[1], grosor)

        pygame.draw.line(screen, (203,203,203), self.rs_penalty_area_singleline[0], self.rs_penalty_area_singleline[1], grosor)

        # goal area
        pygame.draw.line(screen, (166,166,166), self.rs_goal_area_upper[0], self.rs_goal_area_upper[1], grosor)
        pygame.draw.line(screen, (166,166,166), self.rs_goal_area_bottom[0], self.rs_goal_area_bottom[1], grosor)

        pygame.draw.line(screen,  (166,166,166), self.rs_goal_area_singleline[0], self.rs_goal_area_singleline[1], grosor)

        # arco 
        pygame.draw.line(screen, (129,129,129), self.rs_arco_area_upper[0], self.rs_arco_area_upper[1], grosor2)
        pygame.draw.line(screen, (129,129,129), self.rs_arco_area_bottom[0], self.rs_arco_area_bottom[1], grosor2)

        pygame.draw.line(screen, (129,129,129), self.rs_arco_area_singlelane[0], self.rs_arco_area_singlelane[1], grosor)

        # penalty kick mark
        pygame.draw.circle(screen, (0,0,0), self.rs_penalty_kick_mark, grosor, grosor)

        # penalty box arc
        pygame.draw.circle(screen, (221,221,221), self.rs_penalty_box_arc, penalty_area_width/2, grosor, False, True, True, False)
        
        self.ball.draw()

    def goal(self) -> int:
        
        if (self.ball.x < self.ls_arco_area_singlelane[0][0]) and (self.ball.y > self.ls_arco_area_singlelane[0][1] and self.ball.y < self.ls_arco_area_singlelane[1][1]):
            print(" GOL DEL LADO IZQUIERDO ")
            self.ball.reset_speed()
            self.ball.reposition(self.ball_initial_pos)
            # reposicionar jugadores
            
        elif self.ball.x > self.rs_arco_area_singlelane[0][0] and (self.ball.y > self.rs_arco_area_singlelane[0][1] and self.ball.y < self.rs_arco_area_singlelane[1][1]):
            print(" GOL DEL LADO DERECHO ")
            self.ball.reset_speed()
            self.ball.reposition(self.ball_initial_pos)
            # reposicionar jugadoress

    def throw_in(self) -> None:

        if self.ball.y < self.upper_sideline[0][1]: 
            self.ball.reset_speed()
            self.ball.reposition([self.ball.x, self.upper_sideline[0][1]])
            
            # mandar jugador atras de la pelota y hacer player.throw_in()

        elif self.ball.y > self.bottom_sideline[0][1]:
            self.ball.reset_speed()
            self.ball.reposition([self.ball.x, self.bottom_sideline[0][1]])
            # mandar jugador atras de la pelota y hacer player.throw_in()
            
        return
    
    def corner(self) -> None:
        if field.ball.x < self.ls_arco_area_singlelane[0][0]:
            if self.ball.y < self.ls_arco_area_singlelane[0][1]:
                # corner arriba izquierda
                self.ball.reset_speed()
                self.ball.reposition(self.top_left_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

            elif self.ball.y < self.ls_arco_area_singlelane[1][1]:
                # corner abajo izquierda
                self.ball.reset_speed()
                self.ball.reposition(self.bottom_left_corner())
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

        elif self.ball.x > self.rs_arco_area_singlelane[0][0]:
            if self.ball.y < self.rs_arco_area_singlelane[0][1]:
                # corner arriba derecha
                self.ball.reset_speed()
                self.ball.reposition(self.top_right_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

            elif self.ball.y < self.rs_arco_area_singlelane[1][1]:
                # corner abajo derecha
                self.ball.reset_speed()
                self.ball.reposition(self.bottom_right_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()
                
        return

    def begin(self) -> None:
        self.ball.move(self.μ)

    def palo(self) -> None:
        # funciona :D
        if (self.ball.x < self.ls_arco_area_upper[0][0] and self.ball.y == self.ls_arco_area_upper[0][1]) or (self.ball.x > self.rs_arco_area_upper[0][0] and self.ball.y == self.rs_arco_area_upper[0][1]):
            print("uwu")

field = SoccerField(1,1,15)
field.ball.hit([39,0], 1)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    
    screen.fill(GREEN)
    field.draw()
    field.throw_in()
    field.goal()
    field.palo()
    field.begin()
    
    clock.tick(60)  # limits FPS to 60
    pygame.display.flip()