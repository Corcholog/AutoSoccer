import pygame, sys, threading, random, math, time
from screeninfo import get_monitors

monitor = get_monitors()
screen_width = monitor[0].width
screen_height = monitor[0].height

line_color = (255, 0, 0, 128) 

line_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (54, 128, 45)

player_size = [(screen_width * screen_height * 50) / 2073600, (screen_width * screen_height * 50) / 2073600]
ball_size = [(screen_width * screen_height * 40) / 2073600, (screen_width * screen_height * 35) / 2073600]

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
player_1_img = pygame.image.load("src/img/player_1.png")

class Ball(pygame.sprite.Sprite): # Que sea un thread y en el while true haga el move() mientras la velocidad no sea 0 y cuando lo sea que se duerma y la despiertan con un hit
    def __init__(self, pos: list[float], coef) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.lock = threading.Lock()
        self.pos = pos
        self.coef = coef
        self.vector = (0.0, 0.0)
        self.last_touch = None
        self.image = ball_img
        self.scaled_ball = pygame.transform.scale(ball_img, ball_size) # to-do: rescalar dinamicamente
        self.img_rect = self.scaled_ball.get_rect(center=(self.pos[0], self.pos[1]))

    def get_vector(self):
        return self.vector

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
                if(recta[0] < 10 and recta[1] < 10):
                    self.reset_speed()
                    self.last_touch = team_id

    def get_last_touch(self):
        return self.last_touch

    def get_coef(self):
        return self.coef

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
                self.vector = (self.vector[0], strength)
            
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
            return self.team_2.get_players()
        else:
            return self.team_1.get_players()

    def get_team(self, team) -> None:
        if 0 == self.team_1.get_side():
            return self.team_1
        elif 1 == self.team_2.get_side():
            return self.team_2

    def draw(self):
        screen.blit(self.background, (0, 0))
        screen.blit(self.score_team_1, (int(self.middle_line[0][0]- (font_size*2) - (grosor/2)), int(self.top_left_corner[1]/2)))
        screen.blit(self.score_team_2, (int(self.middle_line[0][0]+ (font_size*2) - (grosor/2)), int(self.top_left_corner[1]/2)))

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
     
    def goal(self) -> int:
        if (self.ball.get_rect().midright[0] < self.ls_arco_area_bottom[0][0]) and (self.ball.get_rect().midright[1] > self.ls_arco_area_singlelane[0][1] and self.ball.get_rect().midright[1] < self.ls_arco_area_singlelane[1][1]):
            self.team_2_score += 1
            self.team_last_score = 1
            self.score_team_2 = font.render(f'{str(self.team_2_score)}', True, WHITE)
            self.ball.reset_speed()
            self.ball.reposition(self.ball_initial_pos)
            self.team_1.reposition()
            self.team_2.reposition()
            self.state = "Score"
            
        elif self.ball.get_rect().midleft[0] > self.rs_arco_area_bottom[0][0] and (self.ball.get_rect().midleft[1] > self.rs_arco_area_singlelane[0][1] and self.ball.get_rect().midright[1] < self.rs_arco_area_singlelane[1][1]):
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

        elif self.ball.get_rect().midtop[1] > self.bottom_sideline[0][1]:
            self.state = "Out of game"
            self.ball.reset_speed()
            self.ball.reposition([self.ball.pos[0], self.bottom_sideline[0][1]])

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

            elif self.ball.get_rect().midbottom[1] >= self.ls_arco_area_singlelane[1][1]:
                # corner abajo izquierda
                self.state = "Out of game"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_2):
                    self.ball.reposition(self.ls_penalty_kick_mark)
                else:
                    self.ball.reposition(self.bottom_left_corner)

        elif self.ball.get_rect().midleft[0] > self.top_right_corner[0]:
            if self.ball.get_rect().midtop[1] <= self.rs_arco_area_singlelane[0][1]:
                # corner arriba derecha
                self.state = "Out of game"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_1):
                    self.ball.reposition(self.rs_penalty_kick_mark)
                else:
                    self.ball.reposition(self.top_right_corner)

            elif self.ball.get_rect().midtop[1] >= self.rs_arco_area_singlelane[1][1]:
                # corner abajo derecha
                self.state = "Out of game"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_1):
                    self.ball.reposition(self.rs_penalty_kick_mark)
                else:
                    self.ball.reposition(self.bottom_right_corner)
                
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
        self.L = (screen_width * screen_height * 90) / 2073600
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
        pygame.draw.line(screen, (209, 209, 209), inicio, self.extremo, int(grosor*0.7))

        pygame.draw.line(screen, (209, 209, 209), inicio, self.extremo_resta, int(grosor*0.7))
        pygame.draw.line(screen, (209, 209, 209), inicio, self.extremo_suma, int(grosor*0.7))

        pygame.draw.line(screen, (209, 209, 209), self.extremo_resta, self.extremo, int(grosor*0.7))
        pygame.draw.line(screen, (209, 209, 209), self.extremo, self.extremo_suma, int(grosor*0.7))

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
        if(target.pos[1] == self.pos[1]) and (target.pos[0] == self.pos[0]):
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
        self.side = -1
        self.strength = strength
        self.image = img_path
        self.fov = Fov(0.0, self.pos)
        self.vector = (0.0, 0.0)
        self.scaled_player = pygame.transform.scale(self.image, player_size) # to-do: rescalar dinamicamente
        self.img_rect = self.scaled_player.get_rect(center=(self.pos))

    def get_side(self):
        return self.side

    def set_side(self, old_side, new_side): # side 0 lado izq 1 lado derecho
        if new_side == 0:
            self.set_angle(0)
            self.fov.set_angle(0)
            self.behaviour.set_arco_line([[field_width,  screen_height-field_height+area_padding2], [field_width, screen_height-field_height+area_padding+penalty_area_height-area_padding2]])
        
        elif new_side == 1:
            self.set_angle(180)
            self.fov.set_angle(180)
            self.behaviour.set_arco_line([[screen_width-field_width,  screen_height-field_height+area_padding2], [screen_width-field_width, screen_height-field_height+area_padding+penalty_area_height-area_padding2]])
        
        if old_side != new_side:
            self.set_pos([screen_width - self.behaviour.get_pos()[0], screen_height - self.behaviour.get_pos()[1]])
            self.behaviour.set_pos(self.get_pos())
            self.img_rect = self.scaled_player.get_rect(center=(self.pos[0], self.pos[1]))
            self.side = new_side
    
    def get_name(self):
        return self.name

    def get_fov(self) -> Fov:
        return self.fov
        
    def set_behaviour(self, behaviour):
        self.behaviour = behaviour
        self.initial_pos = behaviour.get_pos()
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
        self.side = self.team.get_side()

    def get_vector(self):
        return self.vector

    def get_team(self):
        return self.team

    def get_angle(self) -> float:
        return math.degrees(self.vector[0])

    def set_angle(self, angle : float):
        self.vector = (math.radians(angle), self.vector[1])
        self.fov.set_angle(self.get_angle())

    def reposition(self):
        #print("pos jugador antes de reposition: ", self.pos)
        self.pos = self.behaviour.get_pos()
        self.img_rect = self.scaled_player.get_rect(center=(self.pos[0], self.pos[1]))
        self.fov.set_pos(self.pos)
        #print("pos jugador despues de reposition: ", self.pos)
        if self.team.get_side() == 0:
            self.vector = (0.0, 0.0)
            self.fov.set_angle(0)
        else:
            self.vector = (180.0, 0.0)
            self.fov.set_angle(180)

    def draw(self) -> None:
        self.update()
        self.fov.draw()
        screen.blit(self.scaled_player, self.img_rect)

    def set_speed(self, speed):
        self.vector = (self.vector[0], speed)

    def get_speed(self) -> float:
        return self.speed

    def get_strength(self) -> float:
        return self.strength

    def run(self) -> None:
        while True:
            if type(self.behaviour) == GoalkeeperBehaviour:
                self.behaviour.metodo_magico()
            else:
                if self.behaviour.player_has_ball():
                    target_pass = self.behaviour.free_teammate()
                    if target_pass == None:
                        self.behaviour.hold_ball()
                    else:
                        self.behaviour.aim_and_pass(target_pass)
                else:
                    self.behaviour.intercept(self.speed)

    def move(self, angle, speed):
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

    def stop_ball(self):
        self.player.get_team().get_field().get_ball().stop_ball(self.player.get_side(), self.player)

    def spin(self, angle) -> bool:
        z = 6 # 360grados en 1s
        my_angle = self.player.get_angle()
        y = angle
        x = my_angle
        diferencia = (y - x) % 360  # Calcula la diferencia entre y y x
        if diferencia <= z or diferencia >= 360 - z:
            self.player.set_angle(y)
            return True # Devuelve True y el ángulo final si es posible llegar
        else:
            diferencia_corta = min(diferencia, 360 - diferencia)  # Calcula la distancia más corta
            if diferencia == diferencia_corta:
                self.player.set_angle(y)
                return True # Devuelve True y el ángulo final si es la distancia más corta
            else:
                if y > x:
                    nuevo_y = (x + z) % 360  # Calcula el nuevo ángulo sumando el límite al ángulo inicial
                else:
                    nuevo_y = (x - z) % 360  # Calcula el nuevo ángulo restando el límite al ángulo inicial
                self.player.set_angle(nuevo_y)
                return False  # Devuelve False y el nuevo ángulo

    def player_has_ball(self) -> bool:
        A = self.player.get_pos()[0]
        B = self.player.get_pos()[1]
        final = (self.player.get_team().get_field().get_ball().get_pos()[0], self.player.get_team().get_field().get_ball().get_pos()[1])
        recta = (abs(final[0] - A), abs(final[1] - B))
        if(recta[0] < player_size[0]*0.1 and recta[1] < player_size[0]*0.1): # TO TEST!!
            return True
        return False
    
    def free_path(self, pos:list[float]) -> bool:
        my_angle = self.player.get_fov().get_angle_to_pos(pos)
        while not self.spin(my_angle):
            pass

        for player in self.player.get_team().get_field().get_players_team(0):
            if(self.player.get_fov().is_sprite_at_view(player) and self.player is not player):
                player_angle = self.player.get_fov().get_angle_to_pos(player.get_pos())
                if(abs(my_angle - player_angle) < 6):
                    return False

        for player in self.player.get_team().get_field().get_players_team(1):
            if(self.player.get_fov().is_sprite_at_view(player) and self.player is not player):
                player_angle = self.player.get_fov().get_angle_to_pos(player.get_pos())
                if(abs(my_angle - player_angle) < 6):
                    return False
        
        return True
    
    def free_teammate(self) -> Player:
        teammates_at_view = list()
        for teammate in self.player.get_team().get_players():
            if(self.player.get_fov().is_sprite_at_view(teammate)):
                teammates_at_view.append(teammate)
        
        if self.player.get_side() == 0:
            enemy_team = 1
        else:
            enemy_team = 0

        enemies_at_view = list()
        for enemy in self.player.get_team().get_field().get_players_team(enemy_team):
            if(self.player.get_fov().is_sprite_at_view(enemy)):
                enemies_at_view.append(enemy)

        nearest =  None
        nearest_distance = 1920
        for free in teammates_at_view:
            if free is not self.player:
                flag = True
                distance = math.sqrt(((self.get_pos()[0] - free.get_pos()[0])**2 + (self.get_pos()[1] - free.get_pos()[1])**2))
                for enemy in enemies_at_view:
                    if(abs(self.player.get_fov().get_angle_to_pos(free.get_pos()) - self.player.get_fov().get_angle_to_pos(enemy.get_pos())) < 6):
                        enemy_distance = math.sqrt(((self.get_pos()[0] - enemy.get_pos()[0])**2 + (self.get_pos()[1] - enemy.get_pos()[1])**2))
                        if(distance >= enemy_distance):
                            flag = False
                            break

                if((nearest == None or distance < nearest_distance) and flag):
                    nearest = free
                    nearest_distance = distance

        return nearest
    
    def aim_and_kick(self):
        if self.player.get_side() == 0:
            enemy_team = 1
        else:
            enemy_team = 0
        goalkeeper = self.player.get_team().get_field().get_team(enemy_team).get_player(0)
        angle =  self.player.get_fov().get_angle_to_object(goalkeeper)
        upper_angle = self.player.get_fov().get_angle_to_pos(self.get_arco_line()[0])
        bottom_angle = self.player.get_fov().get_angle_to_pos(self.get_arco_line()[1])


        distance_to_upper = abs(angle - upper_angle)
        distance_to_bottom = abs(angle - bottom_angle)

        self.player.set_speed(0.0)
        self.player.stop_ball()
        if (distance_to_upper < distance_to_bottom):
            self.player.kick_with_angle(bottom_angle + 10, self.player.get_strength())
        else:
            self.player.kick_with_angle(upper_angle - 10, self.player.get_strength())

    def aim_and_pass(self, target):
        angle = self.player.get_fov().get_angle_to_object(target)
        self.player.set_speed(0.0)
        self.player.stop_ball()
        self.player.kick_with_angle(angle, self.player.get_strength())

    def team_posession(self) -> bool:
        return self.player.get_team().get_field().get_ball().get_last_touch() == self.player.get_side()

    def hold_ball(self):
        move_right = [self.player.get_pos()[0] + 2*player_size[0], self.player.get_pos()[1] + random.choice([2*player_size[0], -2*player_size[0]])]
        move_left = [self.player.get_pos()[0] - 2*player_size[0], self.player.get_pos()[1] + random.choice([2*player_size[0], -2*player_size[0]])]
        if(self.player.get_side() == 0):
            if(self.free_path(move_right)):
                self.move_with_ball(self.player.get_fov().get_angle_to_pos(move_right))
            self.move_with_ball(self.player.get_fov().get_angle_to_pos(move_left))
        else:
            if(self.free_path(move_left)):
                self.move_with_ball(self.player.get_fov().get_angle_to_pos(move_left))
            self.move_with_ball(self.player.get_fov().get_angle_to_pos(move_right))

    def intercept(self, speed):
        ball = self.player.get_team().get_field().get_ball()
        ball_pos = ball.get_pos()
        ball_angle = ball.get_angle()
        ball_speed = ball.get_speed()
        player_speed = speed

        ball_speed *= (1.059 - ball.get_coef())

        if (int(ball_speed) == 0):
            ball_speed = 0

        new_ball_x = ball_pos[0] + ball_speed * math.cos(math.radians(ball_angle))
        new_ball_y = ball_pos[1] + ball_speed * math.sin(math.radians(ball_angle))

        old_distance = math.sqrt(((self.player.get_pos()[0] - ball_pos[0])**2 + (self.get_pos()[1] - ball_pos[1])**2))
        new_distance = math.sqrt(((self.player.get_pos()[0] - new_ball_x)**2 + (self.get_pos()[1] - new_ball_y)**2))
        if (old_distance > new_distance and new_distance < 4 * player_size[0]):
            self.player.move(self.player.fov.get_angle_to_pos([new_ball_x, new_ball_y]), player_speed)
        if(self.player_has_ball()):
            self.player.set_speed(0.0)
            self.player.stop_ball()
    
    def action_blind(self):
        return None
    
    def out_of_game(self):
        return None
    
    def pos_in_goal_area_rs(self, pos:list[float]) -> bool:
        return (pos[0] >= self.player.get_team().get_field().rs_penalty_box_arc[0] and 
            ((pos[1] >= self.player.get_team().get_field().rs_goal_area_upper[0][1]) and 
            (pos[1] <= self.player.get_team().get_field().rs_goal_area_bottom[0][1])) ) 
            
    def pos_in_goal_area_ls(self, pos:list[float]) -> bool: 
        return (pos[0] <= self.player.get_team().get_field().ls_penalty_box_arc[0] and 
            ((pos[1] >= self.player.get_team().get_field().ls_goal_area_upper[0][1]) and 
            (pos[1] <= self.player.get_team().get_field().ls_goal_area_bottom[0][1])))
    

class GoalkeeperBehaviour(Behaviour):
    def __init__(self, pos: list[float]) -> None:
        super().__init__(pos)
        self.cont = 0

    def metodo_magico(self):
        if((self.player.get_fov().is_sprite_at_view(self.player.get_team().get_field().get_ball())) and 
            not self.player_has_ball()):
            if(self.player.get_side() == 0):
                if(self.pos_in_goal_area_ls(self.player.get_team().get_field().get_ball().get_pos())):
                    self.follow_ball()
            if(self.player.get_side() == 1):
                if(self.pos_in_goal_area_rs(self.player.get_team().get_field().get_ball().get_pos())):
                    self.follow_ball()
        elif self.player_has_ball():
            self.player.set_speed(0.0)
            self.player.stop_ball()
            target = self.free_teammate()
            if target is not None:
                self.aim_and_pass(target)
                self.cont = 0
            else:
                self.cont +=1
                if(self.cont == 120):
                    self.player.kick_with_angle(random.choice([45, 315]), self.player.get_strength())
                    self.cont = 0
        else:
            self.action_blind()

    def action_blind(self):
        if(self.player.get_pos()[1] != screen_height/2):
            self.player.move(self.player.get_fov().get_angle_to_pos([self.player.get_pos()[0], screen_height/2]), self.player.get_speed())
        else:
            self.player.set_speed(0.0)
            self.player.set_angle(self.player.get_fov().get_angle_to_object(self.player.get_team().get_field().get_ball()))
        return 

    def follow_ball(self):
        ball = self.player.get_team().get_field().get_ball()
        if(self.get_arco_line()[1][1] > self.player.get_pos()[1] > self.get_arco_line()[0][1]):
            if(self.get_arco_line()[1][1] > ball.get_pos()[1] > self.get_arco_line()[0][1]):
                if(self.player.get_pos()[1] < ball.get_pos()[1]):
                    self.player.move(90, ball.get_speed())
                elif(self.player.get_pos()[1] > ball.get_pos()[1]):
                    self.player.move(270, ball.get_speed())
        else:
            self.player.set_speed(0.0)
            self.player.set_angle(self.player.get_fov().get_angle_to_object(self.player.get_team().get_field().get_ball()))

class FieldPlayerBehaviour(Behaviour):
    def try_score(self) -> bool:
        if (
            (self.player.get_side() == 0 and self.pos_in_goal_area_rs(self.player.get_pos())) 
            or 
            (self.player.get_side() == 1 and self.pos_in_goal_area_ls(self.player.get_pos()))
        ):
            angle_to_arco = self.player.get_fov().get_angle_to_pos([self.get_arco_line()[0][0], screen_height / 2])

            while not self.spin(angle_to_arco):
                pass

            upper_angle = self.player.get_fov().get_angle_to_pos(self.get_arco_line()[0])
            bottom_angle = self.player.get_fov().get_angle_to_pos(self.get_arco_line()[1])

            if(upper_angle > bottom_angle):
                greatest_angle = upper_angle
                least_angle = bottom_angle
            else:
                greatest_angle = bottom_angle
                least_angle = upper_angle

            side = self.player.get_side()
            if side == 0:
                enemy_side = 1
            else:
                enemy_side = 0
            teammates = self.player.get_team().get_field().get_players_team(side)
            enemies = self.player.get_team().get_field().get_players_team(enemy_side)
            for i in range(1, len(teammates)):
                teammate = teammates[i]
                enemy = enemies[i]
                if(self.player != teammate):
                    my_angle = self.player.get_fov().get_angle_to_object(teammate)
                    if(greatest_angle >= my_angle >= least_angle):
                        return False
                        
                my_angle = self.player.get_fov().get_angle_to_object(enemy)
                if(greatest_angle >= my_angle >= least_angle):
                    return False
            self.player.set_speed(0.0)
            return True
        
        
        return False

    def metodo_magico(self):
        if(self.player.get_team().get_field().get_state() == "Out of Game"):
            self.out_of_game()
        elif (self.player.get_team().get_field().get_state() == "Score"):
            self.score()
        else:
            if(self.player_has_ball()):
                if(self.try_score()):
                    self.aim_and_kick(self.arco_line)
                else:
                    target_pass = self.free_teammate()
                    if target_pass == None:
                        self.hold_ball()
                    else:
                        self.aim_and_pass(target_pass)
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

    def ball_taken(self) -> bool: # la tiene el enemigo A SU ALCANCE, NO PUEDO INTERCEPTAR (la veo)
        return False

    def move_with_ball(self, angle):
        self.player.stop_ball()
        self.player.move(angle, self.player.get_speed())
        self.player.kick_with_angle(angle, 2*self.player.get_speed())
        return None

    def unmark(self):
        return None
    
    def mark(self):
        return None
    
    def search_ball(self) -> bool: # girar buscando la pelota, moviendose o no.
        return False

class Team:
    def __init__(self, name, goalkeeper, behaviour):
        self.name = name
        self.side = 0
        goalkeeper.set_behaviour(behaviour)
        goalkeeper.set_team(self)
        behaviour.set_player(goalkeeper)
        self.player_list = list()
        self.player_list.append(goalkeeper)
    
    def set_field(self, field) -> None:
        self.field = field

    def get_field(self) -> SoccerField:
        return self.field

    def get_side(self):
        return self.side

    def add_player(self, player, behaviour):
        player.set_team(self)
        player.set_behaviour(behaviour)
        behaviour.set_player(player)
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

# arqueros   
goalkeeper = Player("JUNINHO PERNAMBUCANO", 4, 45, player_1_img)
behaviour = GoalkeeperBehaviour([screen_width-field_width, screen_height/2])
team_1 = Team("", goalkeeper, behaviour)

player2 = Player("GIANNI", 4, 45, player_3_img)
behaviour2 = GoalkeeperBehaviour([screen_width-field_width, screen_height/2])
team_2 = Team("", player2, behaviour2)


# jugadores team 2

player1 = Player("GIANNI2", 4, 25, player_3_img)
behaviour1 = FieldPlayerBehaviour([screen_width/2, screen_height/2])
team_2.add_player(player1, behaviour1)

player4 = Player("GIANNI3", 4, 25, player_3_img)
behaviour4 = FieldPlayerBehaviour([screen_width/2 + 250, screen_height/2 + 200])
team_2.add_player(player4, behaviour4)

# jugadores team 1

player3 = Player("FERRO2", 0, 25, player_1_img)
behaviour3 = FieldPlayerBehaviour([screen_width/2 - 250, (screen_height/2) - 100])
team_1.add_player(player3, behaviour3)

player5 = Player("FERRO3", 3, 25, player_1_img)
behaviour5 = FieldPlayerBehaviour([screen_width/2 - 200, (screen_height/2)])
team_1.add_player(player5, behaviour5)


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

    if current_time == "00:50" and first_set:
        field.change_gametime()
        first_set = False
    
    time_surface = font.render(current_time, True, (255, 255, 255))
    screen.blit(time_surface, (int(field.middle_line[0][0] - (5*font_size/6)), int(field.top_left_corner[1]/2) - (font_size)))

    clock.tick(60)  # limits FPS to 60
    pygame.display.flip()