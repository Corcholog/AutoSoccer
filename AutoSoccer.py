import pygame, sys, threading, random, math
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

pygame.init()
font_size = 36 # rescalar dinamicamente
font = pygame.font.Font(None, font_size)
clock = pygame.time.Clock()
screen = pygame.display.set_mode((screen_width, screen_height))
ball_img = pygame.image.load("src/img/ball2.png")
player_1_img = pygame.image.load("src/img/player_1.jpg")

class Ball(pygame.sprite.Sprite): # Que sea un thread y en el while true haga el move() mientras la velocidad no sea 0 y cuando lo sea que se duerma y la despiertan con un hit
    def __init__(self, pos: list[float], coef) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.speed = 0.0
        self.x = pos[0]
        self.y = pos[1]
        self.coef = coef
        self.set_angle(0)
        self.vector = (self.angle, self.speed)
        self.last_touch = None
        self.image = ball_img
        self.scaled_ball = pygame.transform.scale(ball_img, (40, 35)) # to-do: rescalar dinamicamente
        self.img_rect = self.scaled_ball.get_rect(center=(self.x, self.y))

    def reposition(self, pos: list[float]) -> None:
        self.speed = 0
        self.x = pos[0]
        self.y = pos[1]
        self.img_rect = self.scaled_ball.get_rect(center=(self.x, self.y))

    def draw(self) -> None:
        self.update()
        screen.blit(self.scaled_ball, self.img_rect)
    
    def reset_speed(self) -> None:
        self.speed = 0
        self.vector = (self.angle, 0.0)

    def stop_ball(self, team_id) -> None:
        self.speed = [0.0,0.0]
        self.last_touch = team_id

    def get_pos(self) -> list[float]:
        return [self.x, self.y]

    def get_speed(self) -> list[float]:
        return self.speed

    def get_angle(self) -> float:
        return math.degrees(self.angle)

    def set_angle(self, angle : float):
        self.angle = math.radians(angle)

    def hit(self, angle, strength, last_touch) -> None:
        self.last_touch = last_touch
        self.set_angle(angle)
        self.speed = strength
        self.vector = (self.angle, strength)

    def apply_smooth_friction(self, vector):
        angle, z = vector
        z *= (1.059 - self.coef) # 1 es demasiado y 1.1 tambien
        return angle, z

    def update(self):
        newpos = self.calcnewpos(self.img_rect, self.vector)
        self.img_rect = newpos
        self.vector = self.apply_smooth_friction(self.vector)
        self.x, self.y = self.img_rect.center

    def get_rect(self):
        return self.img_rect

    def calcnewpos(self, rect, vector):
        (angle, z) = vector
        (dx, dy) = (z * math.cos(angle), z * math.sin(angle))
        return rect.move(dx, dy)

class SoccerField:
    def __init__(self, team_1, team_2, score:list[int]) -> None:
        self.μ = 0.15 # ???
        self.state = "Running" # throw_in | corner
        self.team_1 = team_1
        self.team_2 = team_2
        self.team_1_score = score[0]
        self.team_2_score = score[1]
        #self.ball_initial_pos = [screen_width/2, screen_height/2 - grosor]
        self.ball_initial_pos = [screen_width-field_width+ grosor*3, screen_height-field_height+area_padding+penalty_area_height-area_padding2]
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

    def set_state(self, state):
        self.state = state

    def get_state(self, state):
        return self.state

    def get_ball(self) -> Ball:
        return self.ball

    def get_team(self, team) -> None:
        if team.get_name() == self.team_1.get_name():
            return self.team_1
        elif team.get_name() == self.team_2.get_name():
            return self.team_2

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
        
        screen.blit(self.score_line, (int(self.middle_line[0][0] - (grosor/2)), int(self.top_left_corner[1]/2)))
        screen.blit(self.score_team_1, (int(self.middle_line[0][0]- (font_size*2) - (grosor/2)), int(self.top_left_corner[1]/2)))
        screen.blit(self.score_team_2, (int(self.middle_line[0][0]+ (font_size*2) - (grosor/2)), int(self.top_left_corner[1]/2)))
        self.ball.draw()
        self.team_1.draw()

    def goal(self) -> int:
        if (self.ball.get_rect().midright[0] < self.ls_arco_area_bottom[0][0]) and (self.ball.get_rect().midright[1] > self.ls_arco_area_singlelane[0][1] and self.ball.get_rect().midright[1] < self.ls_arco_area_singlelane[1][1]):
            print(" GOL DEL LADO IZQUIERDO ")
            self.team_2_score += 1
            self.score_team_2 = font.render(f'{str(self.team_2_score)}', True, WHITE)
            self.ball.reset_speed()
            self.ball.reposition(self.ball_initial_pos)
            # reposicionar jugadores
            
        elif self.ball.get_rect().midleft[0] > self.rs_arco_area_bottom[0][0] and (self.ball.get_rect().midleft[1] > self.rs_arco_area_singlelane[0][1] and self.ball.get_rect().midright[1] < self.rs_arco_area_singlelane[1][1]):
            print(" GOL DEL LADO DERECHO ")
            self.team_1_score += 1
            self.score_team_1 = font.render(f'{str(self.team_1_score)}', True, WHITE)
            self.ball.reset_speed()
            self.ball.reposition(self.ball_initial_pos)
            # reposicionar jugadores

    def throw_in(self) -> None:
        if self.ball.get_rect().midbottom[1] < self.upper_sideline[0][1]: 
            self.state = "Stopped"
            self.ball.reset_speed()
            self.ball.reposition([self.ball.x, self.upper_sideline[0][1]])
            # mandar jugador atras de la pelota y hacer player.throw_in()

        elif self.ball.get_rect().midtop[1] > self.bottom_sideline[0][1]:
            self.state = "Stopped"
            self.ball.reset_speed()
            self.ball.reposition([self.ball.x, self.bottom_sideline[0][1]])
            # mandar jugador atras de la pelota y hacer player.throw_in()

    def corner(self) -> None:
        if self.ball.get_rect().midright[0] < field.top_left_corner[0]:
            if self.ball.get_rect().midbottom[1] <= self.ls_arco_area_singlelane[0][1]:
                # corner arriba izquierda
                self.state = "Stopped"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_2):
                    self.ball.reposition(self.ls_penalty_kick_mark)
                else:
                    self.ball.reposition(self.top_left_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

            elif self.ball.get_rect().midbottom[1] >= self.ls_arco_area_singlelane[1][1]:
                # corner abajo izquierda
                self.state = "Stopped"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_2):
                    self.ball.reposition(self.ls_penalty_kick_mark)
                else:
                    self.ball.reposition(self.bottom_left_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

        elif self.ball.get_rect().midleft[0] > self.top_right_corner[0]:
            if self.ball.get_rect().midtop[1] <= self.rs_arco_area_singlelane[0][1]:
                # corner arriba derecha
                self.state = "Stopped"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_1):
                    self.ball.reposition(self.rs_penalty_kick_mark)
                else:
                    self.ball.reposition(self.top_right_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()

            elif self.ball.get_rect().midtop[1] >= self.rs_arco_area_singlelane[1][1]:
                # corner abajo derecha
                self.state = "Stopped"
                self.ball.reset_speed()
                if (self.ball.last_touch == self.team_1):
                    self.ball.reposition(self.rs_penalty_kick_mark)
                else:
                    self.ball.reposition(self.bottom_right_corner)
                # mandar jugador atras de la pelota y hacer player.corner() creo q es similar a player.thrown_in()
                
        return

    def palo(self) -> None:
        # funciona :D
        if (self.ball.get_rect().midleft[1] <= self.ls_arco_area_upper[0][1]+10 and self.ball.get_rect().midleft[1] >= self.ls_arco_area_upper[0][1]-10):
            if ((self.ball.get_rect().midleft[0] < self.ls_arco_area_upper[0][0]+10 and self.ball.get_rect().midleft[0] > self.ls_arco_area_upper[0][0]-35)) or ((self.ball.get_rect().midright[0] > self.rs_arco_area_upper[0][0]-10 and self.ball.get_rect().midright[0] < self.rs_arco_area_upper[0][0]+35)):
                print("PALO")
                self.ball.hit(self.ball.get_angle()*-1, self.ball.get_speed(), self.ball.last_touch)
        elif (self.ball.get_rect().midleft[1] <= self.ls_arco_area_bottom[0][1]+10 and self.ball.get_rect().midleft[1] >= self.ls_arco_area_bottom[0][1]-10):
            if ((self.ball.get_rect().midleft[0] < self.ls_arco_area_upper[0][0]+10 and self.ball.get_rect().midleft[0] > self.ls_arco_area_upper[0][0]-35)) or ((self.ball.get_rect().midleft[1] > self.rs_arco_area_upper[0][0]-10 and self.ball.get_rect().midleft[1] < self.rs_arco_area_upper[0][0]+35)):
                print("PALO")
                self.ball.hit(self.ball.get_angle()*-1, self.ball.get_speed(), self.ball.last_touch)
    
    def begin(self) -> None:
        print()


class Player(threading.Thread, pygame.sprite.Sprite):
    def __init__(self, speed, strength):
        pygame.sprite.Sprite.__init__(self)
        threading.Thread.__init__(self)
        self.pos = [0.0,0.0]
        self.speed = speed
        self.strength = strength
        self.angle = 0.0
        self.image = player_1_img
        self.vector = (self.angle, self.speed)
        self.scaled_player = pygame.transform.scale(self.image, (50, 50)) # to-do: rescalar dinamicamente
        self.img_rect = self.scaled_player.get_rect(center=(self.pos))

    def set_behavior(self, behavior):
        self.behavior = behavior
        self.initial_pos = behavior.get_pos()
        self.img_rect = self.scaled_player.get_rect(center=(self.pos[0], self.pos[1]))
    
    def get_pos(self) -> list[float]:
        return self.pos

    def set_pos(self, pos:list[float]):
        self.pos = pos

    def set_team(self, team):
        self.team = team

    def draw(self) -> None:
        self.update()
        screen.blit(self.scaled_player, self.img_rect)

    def get_speed(self) -> float:
        return self.speed

    def get_strength(self) -> float:
        return self.strength

    def run(self) -> None:
        while True:
            self.set_vector(vector=(self.angle, self.speed))
            
            #if(self.pos == self.team.get_field().get_ball().get_pos()):
             #   print("hola")
              #  self.kick([field_width-goal_area_width-((penalty_area_width-goal_area_width)/2), screen_height/2])
    
    def set_vector(self, vector):
        self.vector = vector

    def update(self):
        newpos = self.calcnewpos(self.img_rect, self.vector)
        self.img_rect = newpos

    def calcnewpos(self, rect, vector):
        (angle, z) = vector
        (dx, dy) = (z * math.cos(angle), z * math.sin(angle))
        return rect.move(dx, dy)

    def kick(self, target_pos) -> None:
        if(self.team.get_field().get_ball().get_pos() != target_pos):
            #print("pos pelota: ", self.pos, " target pos: ", target_pos)

            # Calculate the direction vector towards the target position
            direction = [target_pos[0] - self.team.get_field().get_ball().get_pos()[0], target_pos[1] - self.team.get_field().get_ball().get_pos()[1]]
            #print(direction)

            # Calculate the magnitude (length) of the direction vector
            magnitude = math.sqrt(direction[0]**2 + direction[1]**2)
            #print(magnitude)

            # Normalize the direction vector to get a unit vector
            normalized_direction = [direction[0] / magnitude, direction[1] / magnitude]
            print("vector normalizado: ", normalized_direction)

            # Update the player's position based on the normalized direction and speed
            
            new_x = normalized_direction[0] * self.strength
            new_y = normalized_direction[1] * self.strength
            self.team.get_field().get_ball().hit([new_x, new_y], self.team.get_name())
            # Check if the player has reached the target position
            if math.dist(self.team.get_field().get_ball().get_pos(), target_pos) < self.strength:
                self.team.get_field().get_ball().get_pos().hit(target_pos, self.team.get_name())

    def stop_ball(self):
        self.team.get_field().get_ball().stop_ball()

    def look(self):
        print()

class Behavior():
    def __init__(self, pos:list[float]) -> None:
        super().__init__()
        self.pos = pos

    def get_pos(self) -> list[float]:
        return self.pos

    def set_player(self, player):
        self.player = player

    def run(self):
        while True:
            self.player.move([screen_width-field_width,screen_height-field_height])

class Team:
    def __init__(self, name, goalkeeper, behavior):
        self.name = name
        goalkeeper.set_behavior(behavior)
        goalkeeper.start()
        behavior.set_player(goalkeeper)
        self.player_list = [goalkeeper]
    
    def set_field(self, field) -> None:
        self.field = field

    def get_field(self) -> SoccerField:
        return self.field

    def add_player(self, player, behavior):
        player.set_behavior(behavior)
        behavior.set_player(player)
        self.plaver.start()
        self.player_list.append(player)

    def get_name(self) -> str:
        return self.name

    def draw(self):
        for player in self.player_list:
            player.draw()

    def get_player(self, number) -> Player:
        return self.player_list[number]

    def get_players(self) -> list:
        return self.player_list
        

goalkeeper = Player(5, 5)
goalkeeper_thread = threading.Thread(target=goalkeeper.run)

behavior = Behavior([screen_width/2,screen_height/2])

team_1 = Team("", goalkeeper, behavior)
goalkeeper.set_team(team_1)

'''
player1 = Player(1,1)
behavior1 = Behavior([100,100])
team_1.add_player(player1, behavior1)

player2 = Player(1,1)
behavior2 = Behavior([200,200])
team_1.add_player(player2, behavior2)

player3 = Player(1,1)
behavior3 = Behavior([300,300])
team_1.add_player(player3, behavior3)

player4 = Player(1,1)
behavior4 = Behavior([400,400])
team_1.add_player(player4, behavior4)
'''
field = SoccerField(team_1, team_1, [0,0])
team_1.set_field(field)
print([ field.rs_arco_area_upper[0][0] - field.rs_penalty_kick_mark[0], field.rs_arco_area_upper[0][1] - field.rs_penalty_kick_mark[1]])

field.get_ball().hit(-45, 20, 1)
# Game start time (in milliseconds)
start_time = pygame.time.get_ticks()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    
    screen.fill(GREEN)
    field.draw()
    field.throw_in()
    field.goal()
    field.palo()
    field.corner()


    # Calculate the elapsed time in seconds
    elapsed_time = (pygame.time.get_ticks() - start_time) // 1000

    # Calculate minutes and seconds
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60

    # Format the time as "00:00"
    current_time = f"{minutes:02d}:{seconds:02d}"

    # Render the time on the screen
    time_surface = font.render(current_time, True, (255, 255, 255))


    # Draw the time on the screen
    screen.blit(time_surface, (int(field.middle_line[0][0] - (5*font_size/6)), int(field.top_left_corner[1]/2) - (font_size)))


    clock.tick(60)  # limits FPS to 60
    pygame.display.flip()