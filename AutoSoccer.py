import pygame, sys, threading, random, math, time
from screeninfo import get_monitors

monitor = get_monitors()
screen_width = monitor[0].width
screen_height = monitor[0].height

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (54, 128, 45)

field_width = (screen_width * 120) / 140
field_height = (screen_height * 85) / 100

# numeric values that were constants 10 and 8 for a base resolution 1920x1080 rescalated for dynamic res.
grosor = int(screen_width * screen_height/ 207360)
grosor2 = int(screen_width * screen_height/ 259200)

penalty_area_height = (field_height * 55) / 85
penalty_area_width = (field_width * 16.50) / 120

goal_area_height = (field_height * 24.75) / 85
goal_area_width = (field_width * 5.50) / 120

arco_alto = (field_height * 24.75 * 7 / 18) / 85
arco_ancho = (field_width * 24.75 * 2 / 18)/ 85

area_padding = (15 * field_height) / 85
area_padding1 = area_padding + (15.125 * penalty_area_height) / 85
area_padding2 = area_padding1 + (7.5625 * goal_area_height) / 85

pygame.init()
font_size = 36 # rescalar dinamicamente
font = pygame.font.Font(None, font_size)
clock = pygame.time.Clock()
screen = pygame.display.set_mode((screen_width, screen_height), flags=pygame.SCALED, vsync=1)

ball_img = pygame.image.load("src/img/ball2.png")
player_3_img = pygame.image.load("src/img/ball3.png")
player_2_img = pygame.image.load("src/img/ball.png")
player_1_img = pygame.image.load("src/img/player_1.jpg")

class Ball(pygame.sprite.Sprite): # Que sea un thread y en el while true haga el move() mientras la velocidad no sea 0 y cuando lo sea que se duerma y la despiertan con un hit
    def __init__(self, pos: list[float], coef) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.lock = threading.Lock()
        self.pos = pos
        self.coef = coef
        self.vector = (0.0, 0.0)
        self.last_touch = None
        self.image = ball_img
        self.scaled_ball = pygame.transform.scale(ball_img, (40, 35)) # to-do: rescalar dinamicamente
        self.img_rect = self.scaled_ball.get_rect(center=(self.pos[0], self.pos[1]))

    def reposition(self, pos: list[float]) -> None:
        self.vector = (self.vector[0], 0.0)
        self.pos = pos
        self.img_rect = self.scaled_ball.get_rect(center=(self.pos[0], self.pos[1]))
        
    def draw(self) -> None:
        self.update()
        screen.blit(self.scaled_ball, self.img_rect)
    
    def reset_speed(self) -> None:
        self.vector = (self.vector[0], 0.0)

    def stop_ball(self, team_id, player) -> None:
        with self.lock:
            if(self.vector[1] != 0):
                A = player.get_pos()[0]
                B = player.get_pos()[1]
                final = (self.pos[0], self.pos[1])
                recta = (abs(final[0] - A), abs(final[1] - B))
                #print(recta)
                if(recta[0] < 10 and recta[1] < 10):
                    self.reset_speed()
                    self.last_touch = team_id

    def get_rect(self):
        return self.img_rect

    def get_pos(self) -> list[float]:
        return self.pos

    def get_speed(self) -> list[float]:
        with self.lock:
            return self.vector[1]

    def get_angle(self) -> float:
        with self.lock:
            return math.degrees(self.vector[0])

    def get_angle_to_pos(self, target_pos:list[float]) -> float:
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        radianes = math.atan2(-dy, dx)
        angulo = math.degrees(radianes)
        if(angulo == -0.0):
            angulo = 0.0
        if angulo < 0:
            angulo += 360
        angulo = -1*angulo + 360
        return angulo

    def set_angle(self, angle : float):
        self.vector = (math.radians(angle), self.vector[1])

    def hit(self, angle, strength, player) -> None:
        with self.lock:
            if(player != None):
                #print(self.vector[1])
                if(self.vector[1] == 0):
                    A = player.get_pos()[0]
                    B = player.get_pos()[1]
                    final = (self.pos[0], self.pos[1])
                    recta = (abs(final[0] - A), abs(final[1] - B))
                    if(recta[0] < 10 and recta[1] < 10):
                        self.last_touch = player.get_team().get_name()
                        self.set_angle(angle)
                        self.vector = (self.vector[0], strength)
            else:
                self.set_angle(angle)
                self.vector = (self.angle, strength)
            
    def apply_smooth_friction(self, vector):
        angle, z = vector
        z *= (1.059 - self.coef) # 1 es demasiado y 1.1 tambien
        if(int(z) == 0):
            return angle, 0.0
        return angle, z

    def update(self):
        newpos = self.calcnewpos(self.img_rect, self.vector)
        self.img_rect = newpos
        self.vector = self.apply_smooth_friction(self.vector)
        self.pos = self.img_rect.center

    def calcnewpos(self, rect, vector):
        (angle, z) = vector
        (dx, dy) = (z * math.cos(angle), z * math.sin(angle))
        return rect.move(dx, dy)

class SoccerField:
    def __init__(self, team_1, team_2, score:list[int]) -> None:
        self.μ = 0.15 # ???
        self.state = "Playing" # throw_in | corner
        self.team_1 = team_1
        self.team_1.set_side(0)
        self.team_2 = team_2
        self.team_2.set_side(1)
        self.team_last_score = -1
        self.team_1_score = score[0]
        self.team_2_score = score[1]
        self.ball_initial_pos = [screen_width/2, screen_height/2]
        self.ball = Ball(self.ball_initial_pos, self.μ)
        self.score_line = font.render("-", True, WHITE)
        self.score_team_1 = font.render(f'{self.team_1_score}', True, WHITE)
        self.score_team_2 = font.render(f'{self.team_2_score}', True, WHITE)
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
        self.background = pygame.Surface((screen_width, screen_height))
        self.draw_on_screen(self.background)


    def change_gametime(self):
        if (self.team_1.get_side() == 0):
            self.team_1.set_side(1)
            self.team_2.set_side(0)
        else:
            self.team_1.set_side(0)
            self.team_2.set_side(1)

        self.team_1.reposition()
        self.team_2.reposition()
        self.ball.reposition(self.ball_initial_pos)
        
        aux = self.team_1_score
        self.team_1_score = self.team_2_score
        self.team_2_score = aux
        self.score_team_1 = font.render(f'{str(self.team_1_score)}', True, WHITE)
        self.score_team_2 = font.render(f'{str(self.team_2_score)}', True, WHITE)

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def get_ball(self) -> Ball:
        return self.ball

    def get_players(self) -> list():
        players = list()
        for player in self.get_players_team(1):
            players.append(player)
        for player in self.get_players_team(2):
            players.append(player)
        return players

    def get_players_team(self, team) -> list():
        if(team == 1):
            return self.team_1.get_players()
        else:
            return self.team_2.get_players()

    def get_team(self, team) -> None:
        if team.get_name() == self.team_1.get_name():
            return self.team_1
        elif team.get_name() == self.team_2.get_name():
            return self.team_2

    def draw(self):
        screen.blit(self.background, (0, 0))

    def draw_on_screen(self, screen) -> None:
        screen.fill(GREEN)
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

        # rects for collision
        self.ls_palo_upper = pygame.Rect(self.ls_arco_area_upper[1][0], self.ls_arco_area_upper[0][1], abs(self.ls_arco_area_upper[1][0] - self.ls_arco_area_upper[0][0]), grosor2)
        self.ls_palo_bottom = pygame.Rect(self.ls_arco_area_bottom[1][0], self.ls_arco_area_bottom[0][1], abs(self.ls_arco_area_bottom[1][0] - self.ls_arco_area_bottom[0][0]), grosor2)
        
        pygame.draw.rect(screen, (129,129,129), self.ls_palo_upper, grosor2)
        pygame.draw.rect(screen, (129,129,129), self.ls_palo_bottom, grosor2)

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

        # rects for collision
        self.rs_palo_upper = pygame.Rect(self.rs_arco_area_upper[0][0], self.rs_arco_area_upper[0][1], abs(self.rs_arco_area_upper[1][0] - self.rs_arco_area_upper[0][0]), grosor2)
        self.rs_palo_bottom = pygame.Rect(self.rs_arco_area_bottom[0][0], self.rs_arco_area_bottom[0][1], abs(self.rs_arco_area_bottom[1][0] - self.rs_arco_area_bottom[0][0]), grosor2)
        
        pygame.draw.rect(screen, (129,129,129), self.rs_palo_upper, grosor2)
        pygame.draw.rect(screen, (129,129,129), self.rs_palo_bottom, grosor2)

        pygame.draw.line(screen, (129,129,129), self.rs_arco_area_singlelane[0], self.rs_arco_area_singlelane[1], grosor)

        # penalty kick mark
        pygame.draw.circle(screen, (0,0,0), self.rs_penalty_kick_mark, grosor, grosor)

        # penalty box arc
        pygame.draw.circle(screen, (221,221,221), self.rs_penalty_box_arc, penalty_area_width/2, grosor, False, True, True, False)
        
        screen.blit(self.score_line, (int(self.middle_line[0][0] - (grosor/2)), int(self.top_left_corner[1]/2)))
        screen.blit(self.score_team_1, (int(self.middle_line[0][0]- (font_size*2) - (grosor/2)), int(self.top_left_corner[1]/2)))
        screen.blit(self.score_team_2, (int(self.middle_line[0][0]+ (font_size*2) - (grosor/2)), int(self.top_left_corner[1]/2)))

        

    def goal(self) -> int:
        if (self.ball.get_rect().midright[0] < self.ls_arco_area_bottom[0][0]) and (self.ball.get_rect().midright[1] > self.ls_arco_area_singlelane[0][1] and self.ball.get_rect().midright[1] < self.ls_arco_area_singlelane[1][1]):
            #print(" GOL DEL LADO IZQUIERDO ")
            self.team_2_score += 1
            self.team_last_score = 1
            self.score_team_2 = font.render(f'{str(self.team_2_score)}', True, WHITE)
            self.ball.reset_speed()
            self.ball.reposition(self.ball_initial_pos)
            self.team_1.reposition()
            self.team_2.reposition()
            self.state = "Score"
            
        elif self.ball.get_rect().midleft[0] > self.rs_arco_area_bottom[0][0] and (self.ball.get_rect().midleft[1] > self.rs_arco_area_singlelane[0][1] and self.ball.get_rect().midright[1] < self.rs_arco_area_singlelane[1][1]):
            #print(" GOL DEL LADO DERECHO ")
            self.team_1_score += 1
            self.team_last_score = 0
            self.score_team_1 = font.render(f'{str(self.team_1_score)}', True, WHITE)
            self.ball.reset_speed()
            self.ball.reposition(self.ball_initial_pos)
            self.get_ball().get_angle_to_pos([self.rs_arco_area_bottom[0][0], self.rs_penalty_kick_mark[1]])
            self.team_1.reposition()
            self.team_2.reposition()
            self.state = "Score"

    def throw_in(self) -> None:
        if self.ball.get_rect().midbottom[1] < self.upper_sideline[0][1]: 
            self.state = "Out of game"
            self.ball.reset_speed()
            self.ball.reposition([self.ball.pos[0], self.upper_sideline[0][1]])
            # mandar jugador atras de la pelota y hacer player.throw_in()

        elif self.ball.get_rect().midtop[1] > self.bottom_sideline[0][1]:
            self.state = "Out of game"
            self.ball.reset_speed()
            self.ball.reposition([self.ball.pos[0], self.bottom_sideline[0][1]])
            # mandar jugador atras de la pelota y hacer player.throw_in()

    def corner(self) -> None:
        if self.ball.get_rect().midright[0] < field.top_left_corner[0]:
            if self.ball.get_rect().midbottom[1] <= self.ls_arco_area_singlelane[0][1]:
                # corner arriba izquierda
                self.state = "Out of game"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_2):
                    self.ball.reposition(self.ls_penalty_kick_mark)
                else:
                    self.ball.reposition(self.top_left_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

            elif self.ball.get_rect().midbottom[1] >= self.ls_arco_area_singlelane[1][1]:
                # corner abajo izquierda
                self.state = "Out of game"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_2):
                    self.ball.reposition(self.ls_penalty_kick_mark)
                else:
                    self.ball.reposition(self.bottom_left_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

        elif self.ball.get_rect().midleft[0] > self.top_right_corner[0]:
            if self.ball.get_rect().midtop[1] <= self.rs_arco_area_singlelane[0][1]:
                # corner arriba derecha
                self.state = "Out of game"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_1):
                    self.ball.reposition(self.rs_penalty_kick_mark)
                else:
                    self.ball.reposition(self.top_right_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

            elif self.ball.get_rect().midtop[1] >= self.rs_arco_area_singlelane[1][1]:
                # corner abajo derecha
                self.state = "Out of game"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_1):
                    self.ball.reposition(self.rs_penalty_kick_mark)
                else:
                    self.ball.reposition(self.bottom_right_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()
                
        return

    def palo(self) -> None:
        # arco derecho lado izquierdo ambos palos
        if any(self.ball.get_rect().collidepoint(self.rs_palo_bottom.left, y) for y in range(self.rs_palo_bottom.top, self.rs_palo_bottom.bottom + 1)) or any(self.ball.get_rect().collidepoint(self.rs_palo_upper.left, y) for y in range(self.rs_palo_upper.top, self.rs_palo_upper.bottom + 1)):
            if(self.ball.get_angle() > 270):
                self.ball.hit(-1*(self.ball.get_angle()) + 540, self.ball.get_speed() + 1, None)
            else:
                self.ball.hit(-1*(self.ball.get_angle() - 180), self.ball.get_speed() + 1, None)

        # arco izquierdo lado derecho ambos palos
        elif any(self.ball.get_rect().collidepoint(self.ls_palo_bottom.right, y) for y in range(self.ls_palo_bottom.top, self.ls_palo_bottom.bottom + 1)) or any(self.ball.get_rect().collidepoint(self.ls_palo_upper.right, y) for y in range(self.ls_palo_upper.top, self.ls_palo_upper.bottom + 1)):
            if(self.ball.get_angle() <= 180):
                self.ball.hit(-1*(self.ball.get_angle() - 180), self.ball.get_speed() + 1, None)
            else:
                self.ball.hit(-1*(self.ball.get_angle()) + 540, self.ball.get_speed() + 1, None)

        # ambos arcos ambos palos arriba abajo
        elif any(self.ball.get_rect().collidepoint(x, self.ls_palo_bottom.top) for x in range(self.ls_palo_bottom.left, self.ls_palo_bottom.right + 1)) or any(self.ball.get_rect().collidepoint(x, self.ls_palo_upper.top) for x in range(self.ls_palo_upper.left, self.ls_palo_upper.right + 1)) or any(self.ball.get_rect().collidepoint(x, self.ls_palo_bottom.bottom) for x in range(self.ls_palo_bottom.left, self.ls_palo_bottom.right + 1)) or any(self.ball.get_rect().collidepoint(x, self.ls_palo_upper.bottom) for x in range(self.ls_palo_upper.left, self.ls_palo_upper.right + 1)) or any(self.ball.get_rect().collidepoint(x, self.rs_palo_bottom.top) for x in range(self.rs_palo_bottom.left, self.rs_palo_bottom.right + 1)) or any(self.ball.get_rect().collidepoint(x, self.rs_palo_upper.top) for x in range(self.rs_palo_upper.left, self.rs_palo_upper.right + 1)) or any(self.ball.get_rect().collidepoint(x, self.rs_palo_bottom.bottom) for x in range(self.rs_palo_bottom.left, self.rs_palo_bottom.right + 1)) or any(self.ball.get_rect().collidepoint(x, self.rs_palo_upper.bottom) for x in range(self.rs_palo_upper.left, self.rs_palo_upper.right + 1)) :
            self.ball.hit(-1*self.ball.get_angle() + 360, self.ball.get_speed() + 1, None)

    def begin(self) -> None:
        self.team_1.start()
        self.team_2.start()


class Fov:
    def __init__(self, angle, pos:list[float]) -> None:
        self.angle = angle
        self.pos = pos
    
    def draw(self):
        # punto inicial x
        A = self.pos[0]

        # punto inicial y
        B = self.pos[1]

        inicio = (A,B)
        # grado de vision osea miro al grado
        z = self.angle
        zrad = math.radians(z)
        RestaSumaRad = math.radians(50)

        #distancia cono
        self.L = 90
        extremo_x = A + self.L * math.cos(zrad)
        extremo_y = B + self.L * math.sin(zrad)

        # recta de esos grados desde el punto inicial
        self.extremo = [extremo_x, extremo_y]

        #recta de grados menos
        if(z < 50):
            calculo = z - 50 + 360
            calculoRad = math.radians(calculo)
            extremo_resta_x = A + self.L * math.cos(calculoRad)
            extremo_resta_y = B + self.L * math.sin(calculoRad)
        else:
            extremo_resta_x = A + self.L * math.cos(zrad - RestaSumaRad)
            extremo_resta_y = B + self.L * math.sin(zrad - RestaSumaRad)
        self.extremo_resta = [extremo_resta_x, extremo_resta_y]

        #recta de grados mas
        if(z >= 310):
            calculo = z - 360 + 50
            calculoRad = math.radians(calculo)
            extremo_suma_x = A + self.L * math.cos(calculoRad)
            extremo_suma_y = B + self.L * math.sin(calculoRad)
        else:
            extremo_suma_x = A + self.L * math.cos(zrad + RestaSumaRad)
            extremo_suma_y = B + self.L * math.sin(zrad + RestaSumaRad)
        self.extremo_suma = [extremo_suma_x, extremo_suma_y]

        pygame.draw.line(screen, WHITE, inicio, self.extremo, 5)

        pygame.draw.line(screen, WHITE, inicio, self.extremo_resta, 5)
        pygame.draw.line(screen, WHITE, inicio, self.extremo_suma, 5)

        pygame.draw.line(screen, WHITE, self.extremo_resta, self.extremo, 5)
        pygame.draw.line(screen, WHITE, self.extremo, self.extremo_suma, 5)

    def set_pos(self, pos:list[float]):
        self.pos = pos

    def set_angle(self, angle):
        self.angle = angle

    def is_sprite_at_view(self, sprite):
        # cambiar nombre a bottom_right
        fov_rect = pygame.Rect(0, 0, field_width/3, field_height/2)
        original_surface = pygame.Surface((field_width/3, field_height/2), pygame.SRCALPHA)
        bottom_right_rect = original_surface.get_rect(center=fov_rect.center)
        bottom_right_rect.topleft = [self.pos[0], self.pos[1]]
        #screen.blit(original_surface, bottom_right_rect.topleft)

        if 50 >= self.angle >= 40:
            #print("cuadrante 1")
            return bottom_right_rect.colliderect(sprite.get_rect())
        
        elif 140 >= self.angle >= 130:
            #print("cuadrante 2")
            bottom_left_rect = bottom_right_rect.move(-bottom_right_rect.width, 0)
            return bottom_left_rect.colliderect(sprite.get_rect())
        
        elif 230 >= self.angle >= 220:
            #print("cuadrante 3")
            upper_left_rect = bottom_right_rect.move(-bottom_right_rect.width, -bottom_right_rect.height)
            return upper_left_rect.colliderect(sprite.get_rect())
         
        elif 320 >= self.angle >= 310:
            #print("cuadrante 4")
            upper_right_rect = bottom_right_rect.move(0, -bottom_right_rect.height)
            return upper_right_rect.colliderect(sprite.get_rect())

        elif 45 < self.angle < 135:
            #print("cuadrante 1 y 2")
            bottom_left_rect = bottom_right_rect.move(-bottom_right_rect.width, 0)
            #print("¿Hay colisión con el rectángulo 1?", bottom_right_rect.colliderect(sprite.get_rect()))
            #print("¿Hay colisión con el rectángulo 2?", bottom_left_rect.colliderect(sprite.get_rect()))
            return bottom_right_rect.colliderect(sprite.get_rect()) or bottom_left_rect.colliderect(sprite.get_rect())
            
        elif 225 > self.angle > 135:
            #print("cuadrante 2 y 3")
            bottom_left_rect = bottom_right_rect.move(-bottom_right_rect.width, 0)
            upper_left_rect = bottom_right_rect.move(-bottom_right_rect.width, -bottom_right_rect.height)
            #print("¿Hay colisión con el rectángulo 2?", bottom_left_rect.colliderect(sprite.get_rect()))
            #print("¿Hay colisión con el rectángulo 3?", upper_left_rect.colliderect(sprite.get_rect()))
            return bottom_left_rect.colliderect(sprite.get_rect()) or upper_left_rect.colliderect(sprite.get_rect())

        elif 315 > self.angle > 225:
            #print("cuadrante 3 y 4")
            upper_left_rect = bottom_right_rect.move(-bottom_right_rect.width, -bottom_right_rect.height)
            upper_right_rect = bottom_right_rect.move(0, -bottom_right_rect.height)
            #print("¿Hay colisión con el rectángulo 3?", upper_left_rect.colliderect(sprite.get_rect()))
            #print("¿Hay colisión con el rectángulo 4?", upper_right_rect.colliderect(sprite.get_rect()))
            return upper_left_rect.colliderect(sprite.get_rect()) or upper_right_rect.colliderect(sprite.get_rect())
            
        elif 45 > self.angle or self.angle > 315:
            #print("cuadrante 4 y 1")
            upper_right_rect = bottom_right_rect.move(0, -bottom_right_rect.height)
            #print("¿Hay colisión con el rectángulo 1?", bottom_right_rect.colliderect(sprite.get_rect()))
            #print("¿Hay colisión con el rectángulo 4?", upper_right_rect.colliderect(sprite.get_rect()))
            return bottom_right_rect.colliderect(sprite.get_rect()) or upper_right_rect.colliderect(sprite.get_rect())
        else:
            return False

    def get_ball_pos(self, SoccerField) -> None | Ball:
        if (self.is_sprite_at_view(SoccerField.get_ball())):
            return SoccerField.get_ball()
        else:
            return None

    def get_teammates_at_view(self, team):
        teammates = list()
        for teammate in team.get_players():
            if(self.pos != teammate.fov.pos):
                if (self.is_sprite_at_view(teammate)):
                    teammates.append(teammate)
        return teammates

    def get_angle_to_object(self, target) -> float:
        if(target.pos[1] == self.pos[1]):
            return 0
        else:
            dx = target.pos[0] - self.pos[0]
            dy = target.pos[1] - self.pos[1]
            radianes = math.atan2(-dy, dx)
            angulo = math.degrees(radianes)
            if angulo < 0:
                angulo += 360
            angulo = -1*angulo + 360
            return angulo
        
    def get_angle_to_pos(self, target_pos:list[float]) -> float:
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        radianes = math.atan2(-dy, dx)
        angulo = math.degrees(radianes)
        if angulo < 0:
            angulo += 360
        angulo = -1*angulo + 360
        return angulo

class Player(threading.Thread, pygame.sprite.Sprite):
    def __init__(self, name, speed, strength, img_path):
        pygame.sprite.Sprite.__init__(self)
        threading.Thread.__init__(self)
        self.name = name
        self.pos = [0.0,0.0]
        self.speed = speed
        self.strength = strength
        self.image = img_path
        self.fov = Fov(0.0, self.pos)
        self.vector = (0.0, 0.0)
        self.scaled_player = pygame.transform.scale(self.image, (50, 50)) # to-do: rescalar dinamicamente
        self.img_rect = self.scaled_player.get_rect(center=(self.pos))

    def set_side(self, old_side, new_side): # side 0 lado izq 1 lado derecho
        if new_side == 0:
            self.fov.set_angle(0)
            self.vector = (0.0, self.vector[1])
            self.Behaviour.set_arco_line([[screen_width-field_width,  screen_height-field_height+area_padding2], [screen_width-field_width, screen_height-field_height+area_padding+penalty_area_height-area_padding2]])
        else:
            self.vector = (180.0, self.vector[1])
            self.fov.set_angle(180)
            self.Behaviour.set_arco_line([[field_width,  screen_height-field_height+area_padding2], [field_width, screen_height-field_height+area_padding+penalty_area_height-area_padding2]])
        
        if old_side != new_side:
            self.set_pos([screen_width - self.Behaviour.get_pos()[0], screen_height - self.Behaviour.get_pos()[1]])
            self.Behaviour.set_pos(self.get_pos())
            self.img_rect = self.scaled_player.get_rect(center=(self.pos[0], self.pos[1]))

    def get_name(self):
        return self.name

    def set_Behaviour(self, Behaviour):
        self.Behaviour = Behaviour
        self.initial_pos = Behaviour.get_pos()
        self.set_pos(self.initial_pos)
        self.img_rect = self.scaled_player.get_rect(center=(self.pos[0], self.pos[1]))

    def get_rect(self):
        return self.img_rect

    def get_pos(self) -> list[float]:
        return self.pos

    def set_pos(self, pos:list[float]):
        self.pos = pos
        self.fov.set_pos(self.pos)

    def set_team(self, team):
        self.team = team

    def get_team(self):
        return self.team

    def get_angle(self) -> float:
        return math.degrees(self.angle)

    def set_angle(self, angle : float):
        self.angle = math.radians(angle)

    def reposition(self):
        #print("pos jugador antes de reposition: ", self.pos)
        self.pos = self.Behaviour.get_pos()
        self.img_rect = self.scaled_player.get_rect(center=(self.pos[0], self.pos[1]))
        self.fov.set_pos(self.pos)
        #print("pos jugador despues de reposition: ", self.pos)
        if self.team.get_side() == 0:
            self.vector = (0.0, self.vector[1])
            self.fov.set_angle(0)
        else:
            self.vector = (180.0, self.vector[1])
            self.fov.set_angle(180)

    def draw(self) -> None:
        self.update()
        self.fov.draw()
        screen.blit(self.scaled_player, self.img_rect)

    def get_speed(self) -> float:
        return self.speed

    def get_strength(self) -> float:
        return self.strength

    def run(self) -> None:
        while True:
            if(self.fov.is_sprite_at_view(self.team.get_field().get_ball())):
                self.move(self.team.get_field().get_ball().get_pos(), self.speed)
                if(self.team.get_side() == 1):
                    self.kick([self.team.get_field().ls_arco_area_bottom[0][0], self.team.get_field().rs_penalty_kick_mark[1]], 2*self.speed)         
                else:
                    self.kick([self.team.get_field().rs_arco_area_bottom[0][0], self.team.get_field().rs_penalty_kick_mark[1]], 2*self.speed)         


    def move(self, target_pos, speed):
        angle = self.fov.get_angle_to_pos(target_pos)
        self.set_vector(vector=(angle, speed))

    def set_vector(self, vector):
        self.fov.set_angle(vector[0])
        if(vector[1] <= self.speed):
                self.vector = (math.radians(vector[0]), vector[1])
        else:
            self.vector = (math.radians(vector[0]), self.speed)

    def update(self):
        newpos = self.calcnewpos(self.img_rect, self.vector)
        self.img_rect = newpos
        self.fov.set_pos([self.img_rect.centerx, self.img_rect.centery])
        self.pos = [self.img_rect.centerx, self.img_rect.centery]

    def calcnewpos(self, rect, vector):
        (angle, z) = vector
        (dx, dy) = (z * math.cos(angle), z * math.sin(angle))
        return rect.move(dx, dy)

    def kick_with_angle(self, angle, strength):
        if(strength <= self.strength):
            self.team.get_field().get_ball().hit(angle, strength, self)
        else:
            self.team.get_field().get_ball().hit(angle, self.strength, self)

    def kick(self, target_pos, strength):
        angle = self.team.get_field().get_ball().get_angle_to_pos(target_pos)
        self.kick_with_angle(angle, strength)

    def stop_ball(self):
        self.team.get_field().get_ball().stop_ball(self.team.get_name(), self)


class Behaviour():
    def __init__(self, pos:list[float]) -> None:
        self.pos = pos

    def get_pos(self) -> list[float]:
        return self.pos

    def get_arco_line(self):
        return self.arco_line

    def set_arco_line(self, rect):
        self.arco_line = rect

    def set_pos(self, pos):
        self.pos = pos

    def set_player(self, player):
        self.player = player

    def metodo_magico(self):
        return None

    def player_has_ball(self) -> bool:
        return False
    
    def free_path(self, pos:list[float]) -> bool:
        return False
    
    def free_teammate(self) -> Player:
        return None
    
    def aim_and_kick(self, pos:list[float]):
        return None
    
    def hold_ball(self):
        return None
    
    def team_posession(self) -> bool:
        return True
    
    def intercept(self):
        return None
    
    def action_blind(self):
        return None
    
    def out_of_game(self):
        return None

class GoalkeeperBehaviour(Behaviour):
    def move_in_range(self):
        return None

class FieldPlayerBehaviour(Behaviour):
    def metodo_magico(self):
        if(self.player.get_team().get_field().get_state() == "Out of Game"):
            self.out_of_game()
        elif (self.player.get_team().get_field().get_state() == "Score"):
            self.score()
        else:
            if(self.player_has_ball()):
                if(self.free_path(self.arco_line)):
                    self.aim_and_kick(self.arco_line)
                else:
                    target_pass = self.free_teammate()
                    if target_pass == None:
                        self.hold_ball()
                    else:
                        self.aim_and_kick(self.target_pass.get_pos())
            else:
                if(self.search_ball()):
                    if(self.team_posession()):
                        self.unmark()
                    else:
                        if(self.ball_taken()):
                            self.mark()
                        else:
                            self.intercept()
                else:
                    self.action_blind()
    
    def score(self):
        return None

    def ball_taken(self) -> bool:
        return False

    def move_with_ball(self, angle):
        self.player.kick(angle, 2*self.player.get_speed())
        return None

    def unmark(self):
        return None
    
    def mark(self):
        return None
    
    def search_ball(self) -> bool:
        return False

class Team:
    def __init__(self, name, goalkeeper, Behaviour):
        self.name = name
        self.side = 0
        goalkeeper.set_Behaviour(Behaviour)
        goalkeeper.set_team(self)
        Behaviour.set_player(goalkeeper)
        self.player_list = list()
        self.player_list.append(goalkeeper)
    
    def set_field(self, field) -> None:
        self.field = field

    def get_field(self) -> SoccerField:
        return self.field

    def add_player(self, player, Behaviour):
        player.set_team(self)
        player.set_Behaviour(Behaviour)
        Behaviour.set_player(player)
        self.player_list.append(player)

    def get_name(self) -> str:
        return self.name

    def reposition(self):
        for player in self.player_list:
            player.reposition()
        
    def set_side(self, side):
        for player in self.player_list:
            player.set_side(self.side, side)
        self.side = side

    def draw(self):
        for player in self.player_list:
            player.draw()

    def get_side(self):
        return self.side

    def start(self):
        for player in self.player_list:
            player.start()

    def get_player(self, number) -> Player:
        return self.player_list[number]

    def get_players(self) -> list:
        return self.player_list.copy()
        
goalkeeper = Player("JUNINHO PERNAMBUCANO", 1, 20, player_1_img)
behaviour = FieldPlayerBehaviour([screen_width/3, screen_height/3])
team_1 = Team("", goalkeeper, behaviour)

player1 = Player("GIANNI", 1, 10, player_3_img)
Behaviour1 = FieldPlayerBehaviour([screen_width/3 + 100, screen_height/3 - 200])
team_2 = Team("", player1, Behaviour1)

player2 = Player("GIANNI2", 4, 20, player_3_img)
Behaviour2 = FieldPlayerBehaviour([screen_width/3, (screen_height/3) + 100])

player3 = Player("GIANNI3", 2, 10, player_3_img)
Behaviour3 = FieldPlayerBehaviour([screen_width/3 - 100, (screen_height/3) + 200])

player4 = Player("GIANNI4", 2, 10, player_3_img)
Behaviour4 = FieldPlayerBehaviour([screen_width/3, (screen_height/3) + 300])


player5 = Player("GIANNI5", 2, 10, player_3_img)
Behaviour5 = FieldPlayerBehaviour([screen_width/3, (screen_height/3) + 400])

player6 = Player("GIANNI5", 2, 10, player_3_img)
Behaviour6 = FieldPlayerBehaviour([screen_width/3, (screen_height/3) + 500])

player7 = Player("GIANNI5", 2, 10, player_3_img)
Behaviour7 = FieldPlayerBehaviour([screen_width/3, (screen_height/3) + 600])

team_2.add_player(player2, Behaviour2)
team_2.add_player(player3, Behaviour3)
team_2.add_player(player4, Behaviour4)
team_2.add_player(player5, Behaviour5)
team_2.add_player(player6, Behaviour6)
team_2.add_player(player7, Behaviour7)





field = SoccerField(team_1, team_2, [0,0])
team_1.set_field(field)
team_2.set_field(field)

field.begin()

start_time = pygame.time.get_ticks()
first_set = True


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    
    field.draw()
    team_1.draw()
    team_2.draw()
    field.get_ball().draw()
    field.throw_in()
    field.goal()
    field.palo()
    field.corner()
    elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    current_time = f"{minutes:02d}:{seconds:02d}"

    if current_time == "00:30" and first_set:
        field.change_gametime()
        first_set = False
    
    time_surface = font.render(current_time, True, (255, 255, 255))
    screen.blit(time_surface, (int(field.middle_line[0][0] - (5*font_size/6)), int(field.top_left_corner[1]/2) - (font_size)))

    clock.tick(60)  # limits FPS to 60
    pygame.display.flip()