import math
import threading


from AutoSoccer import Behaviour, Player, player_size, half_height


class Graph:
    def __init__(self):
        self.graph = {}
        self.lock = threading.Lock()

    def add_edge(self, vertex1, vertex2):
        player1_pos = vertex1.get_pos()
        player2_pos = vertex2.get_pos()
        distance = math.sqrt((player2_pos[0] - player1_pos[0])**2 + (player2_pos[1] - player1_pos[1])**2)
        self.graph[vertex1][vertex2] = distance
        self.graph[vertex2][vertex1] = distance

    def add_vertex(self, vertex):
        if vertex not in self.graph:
            self.graph[vertex] = {}

    def display(self):
        for vertex, neighbors in self.graph.items():
            neighbors_str = ', -> '.join([f"{neighbor.get_name()}: {weight:.2f}" for neighbor, weight in neighbors.items()])
            print(f"Player {vertex.get_name()} -> {neighbors_str}")

    def get_min_weight_edges(self, player):
        with self.lock:
            edges = [(player, neighbor, weight) for neighbor, weight in self.graph[player].items()]
            return sorted(edges, key=lambda x: x[2])  # Sort by weight

    def update_weights(self, player):
        with self.lock:
            new_pos = player.get_pos()
            for other_player, distance in self.graph[player].items():
                updated_distance = math.sqrt((new_pos[0] - other_player.get_pos()[0])**2 + (new_pos[1] - other_player.get_pos()[1])**2)
                self.graph[player][other_player] = updated_distance
                self.graph[other_player][player] = updated_distance

    def set_all(self):
        with self.lock:
            vertexs = list(self.graph.keys())
            for i in range(len(vertexs)):
                for j in range(i + 1, len(vertexs)):
                    self.add_edge(vertexs[i], vertexs[j])

class CorchoBehaviour(Behaviour):
    def __init__(self, pos: list[float], forwarding, team_graph: Graph) -> None:
        super().__init__(pos)
        self.forwarding = forwarding
        self.graph = team_graph

    def set_player(self, player):
        super().set_player(player)
        self.graph.add_vertex(self.player)

    def update(self):
        self.graph.update_weights(self.player)

    def free_teammate(self, forward_pass:bool) -> Player:
        side = self.player.get_side()
        if  side == 0:
            enemy_team = 1
        else:
            enemy_team = 0

        target = None
        teammates = self.graph.get_min_weight_edges(self)
        enemies = self.player.get_team().get_field().get_players_team(enemy_team)
        player_x = self.player.get_pos()[0]
        if(forward_pass):
            if side == 0:
                for teammate in teammates:
                    if(teammate.get_pos()[0] > player_x):
                        if(self.player.get_fov().is_sprite_at_view(teammate)):
                            angle_to_teammate = self.player.get_fov().get_angle_to_pos(teammate.get_pos())
                            for enemy in enemies:
                                if(self.player.get_fov().is_sprite_at_view(enemy)):
                                    if(abs(angle_to_teammate - self.player.get_fov().get_angle_to_pos(enemy.get_pos())) < 6):
                                        target = teammate
                                        return target
            else:
                for teammate in teammates:
                    if(teammate.get_pos()[0] < player_x):
                        if(self.player.get_fov().is_sprite_at_view(teammate)):
                            angle_to_teammate = self.player.get_fov().get_angle_to_pos(teammate.get_pos())
                            for enemy in enemies:
                                if(self.player.get_fov().is_sprite_at_view(enemy)):
                                    if(abs(angle_to_teammate - self.player.get_fov().get_angle_to_pos(enemy.get_pos())) < 6):
                                        target = teammate
                                        return target

        if side == 0:
            for teammate in teammates:
                if(teammate.get_pos()[0] < player_x):
                    if(self.player.get_fov().is_sprite_at_view(teammate)):
                        angle_to_teammate = self.player.get_fov().get_angle_to_pos(teammate.get_pos())
                        for enemy in enemies:
                            if(self.player.get_fov().is_sprite_at_view(enemy)):
                                if(abs(angle_to_teammate - self.player.get_fov().get_angle_to_pos(enemy.get_pos())) < 6):
                                    target = teammate
                                    return target
        else:
            for teammate in teammates:
                if(teammate.get_pos()[0] > player_x):
                    if(self.player.get_fov().is_sprite_at_view(teammate)):
                        angle_to_teammate = self.player.get_fov().get_angle_to_pos(teammate.get_pos())
                        for enemy in enemies:
                            if(self.player.get_fov().is_sprite_at_view(enemy)):
                                if(abs(angle_to_teammate - self.player.get_fov().get_angle_to_pos(enemy.get_pos())) < 6):
                                    target = teammate
                                    return target
        return None

    def try_score(self) -> bool:
        if (
            (self.player.get_side() == 0 and self.pos_in_goal_area_rs(self.player.get_pos())) 
            or 
            (self.player.get_side() == 1 and self.pos_in_goal_area_ls(self.player.get_pos()))
        ):
            angle_to_arco = self.player.get_fov().get_angle_to_pos([self.get_arco_line()[0][0], half_height])

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
                enemy = enemies[i]
                my_angle = self.player.get_fov().get_angle_to_object(enemy)
                if(side == 0):
                    if(greatest_angle >= 270) and (my_angle >= greatest_angle):
                        if(least_angle >= 270 and my_angle <= least_angle) or (least_angle <= 270 and my_angle >= least_angle):
                            return False
                    if(greatest_angle >= my_angle >= least_angle) and greatest_angle < 270:
                        return False
            self.player.set_speed(0.0)
            return True
        return False

    def try_move_forward(self) -> bool:
        player_pos = self.player.get_pos()
        if(self.player.get_side() == 0):
            next_move = [player_pos[0] + 2*player_size[0], player_pos[1]]
            if(self.free_path(next_move)):
                self.move_with_ball(self.player.get_fov().get_angle_to_pos(next_move))
                return True
            else:
                next_move = [player_pos[0] - 2*player_size[0], player_pos[1]]
                if(self.free_path(next_move)):
                    self.move_with_ball(self.player.get_fov().get_angle_to_pos(next_move))
                    return True
        else:
            next_move = [player_pos[0] - 2*player_size[0], player_pos[1]]
            if(self.free_path(next_move)):
                self.move_with_ball(self.player.get_fov().get_angle_to_pos(next_move))
                return True
            else:
                next_move = [player_pos[0] + 2*player_size[0], player_pos[1]]
                if(self.free_path([next_move[0], player_pos[1]])):
                    self.move_with_ball(self.player.get_fov().get_angle_to_pos([next_move[0], player_pos[1]]))
                    return True
        return False

    def flow(self):
        if(self.player.get_team().get_field().get_state() == "Playing"):
            ball = self.player.get_team().get_field().get_ball()
            nearest_to_ball = self.player_has_ball()
            if (nearest_to_ball[0] == self.player):
                if(self.try_score()):
                    self.aim_and_kick()
                else:
                    self.update()
                    target_pass = self.free_teammate(True)
                    if(target_pass == None):
                        if(not self.try_move_forward()):
                            target_pass = self.free_teammate(False)
                            if target_pass == None:
                                self.hold_ball()
                            else:
                                self.aim_and_pass(target_pass)
                    else:
                        self.aim_and_pass(target_pass) 
            elif (nearest_to_ball[0] != None) and (nearest_to_ball[0].get_side() == self.player.get_side()):
                self.unmark()
            elif (nearest_to_ball[0] != None) and (nearest_to_ball[0].get_side() != self.player.get_side()):
                if(nearest_to_ball[1] == self.player):
                    angle = self.player.get_fov().get_angle_to_object(ball)
                    self.player.move(angle, self.player.get_speed())
                else:
                    self.mark()
            elif (nearest_to_ball[0] == None):
                if(nearest_to_ball[1] == self.player and ball.get_speed() != 0):
                    self.intercept(self.player.get_speed())
                elif (nearest_to_ball[1] == self.player and ball.get_speed() == 0):
                    angle = self.player.get_fov().get_angle_to_object(ball)
                    self.player.move(angle, self.player.get_speed())
                else:
                    self.action_blind()
        elif(self.player.get_team().get_field().get_state() == "Out of Game"):
            self.out_of_game()
        elif(self.player.get_team().get_field().get_state() == "Goal Kick"):
            self.goal_kick()
        else:
            self.score()
             
    def action_blind(self):
        if(self.team_posession()):
            if self.player.get_side() == 0:
                self.player.move(self.player.get_fov().get_angle_to_pos([self.player.get_pos()[0] + self.forwarding, self.player.get_pos()[1]]), self.player.get_speed())
            else:
                self.player.move(self.player.get_fov().get_angle_to_pos([self.player.get_pos()[0] - self.forwarding, self.player.get_pos()[1]]), self.player.get_speed())
        else:
            self.player.move(self.player.get_fov().get_angle_to_pos(self.pos), self.player.get_speed())

    def move_with_ball(self, angle):
        with self.lock:
            self.player.kick_with_angle(angle, 2*self.player.get_speed())
            self.player.move(angle, 0.5*self.player.get_speed())

    def goal_kick(self):
        side = self.player.get_side()
        if (
            (side == 0 and self.pos_in_goal_area_rs(self.player.get_pos())) 
            or 
            (side == 1 and self.pos_in_goal_area_ls(self.player.get_pos()))
        ):
            self.player.move(self.player.get_fov().get_angle_to_pos(self.pos), self.player.get_speed())
        else:
            self.player.set_speed(0)

    def out_of_game(self):
        last_touch = self.player.get_team().get_field().get_ball().get_last_touch()
        nearest = self.player_has_ball()
        ball = self.player.get_team().get_field().get_ball()
        if(nearest[1] == self.player) and (self.player.get_side() != last_touch):
            angle = self.player.get_fov().get_angle_to_object(ball)
            self.player.move(angle, self.player.get_speed())

            if(self.player.get_side() == 0):
                while(self.player.get_pos()[1] < ball.get_pos()[1]):
                    pass
                self.player.set_speed(0.0)
            else:
                while(self.player.get_pos()[1] > ball.get_pos()[1]):
                    pass
                self.player.set_speed(0.0)
            
            self.player.set_speed(0.0)
            pass_forward = self.free_teammate(True)
            pass_backwards = self.free_teammate(False)
            if(pass_forward == None):
                if(pass_backwards == None):
                    self.player.kick_with_angle(self.player.get_fov().get_angle_to_pos([self.arco_line[0][0], half_height]), self.player.get_strength())
                else:
                    self.aim_and_pass(pass_backwards)
            else:
                self.aim_and_pass(pass_forward)    

            self.player.get_team().get_field().set_state("Playing")
        else:
            self.player.move(self.player.get_fov().get_angle_to_object(ball), 0.0)
            
    def score(self):
        team_scored = self.player.get_team().get_field().get_last_score()
        nearest = self.player_has_ball()
        self.player.set_speed(0.0)
        team_side = self.player.get_side()
        if(team_side != team_scored):
            if(nearest[1] == self.player):
                ball = self.player.get_team().get_field().get_ball()
                angle = self.player.get_fov().get_angle_to_object(ball)
                self.player.move(angle, self.player.get_speed())
                
                if(team_side == 0):
                    while(self.player.get_pos()[0] < ball.get_pos()[0]):
                        #print(self.player.get_pos(), " ", ball.get_pos())
                        pass
                else:
                    while(self.player.get_pos()[0] > ball.get_pos()[0]):
                        #print(self.player.get_pos(), " ", ball.get_pos())
                        pass
                
                teammate_list = self.player.get_team().get_players()
                for i in range(1, len(teammate_list)):
                    teammate = teammate_list[i]
                    if (self.player != teammate):
                        self.aim_and_pass(teammate)
                        break
                
                self.player.get_team().get_field().set_state("Playing")

    def unmark(self):
        side = self.player.get_side()
        pos = self.player.get_pos()
        if(side == 0):
            move_up_right = (pos[0] + 2*player_size[0], pos[1] + 5*player_size[0])
            move_down_right = (pos[0] + 2*player_size[0], pos[1] - 5*player_size[0])
            move_backwards = (pos[0] - 2*player_size[0], pos[1])
            move_forward = (pos[0] + 2*player_size[0], pos[1])
            
            if ((move_forward[0] < self.player.get_team().get_field().rs_goal_area_singleline[0][0])):
                if(self.free_path(move_forward)):
                    self.player.move(self.player.get_fov().get_angle_to_pos(move_forward), self.player.get_speed())
                elif(self.free_path(move_up_right)):
                    self.player.move(self.player.get_fov().get_angle_to_pos(move_up_right), self.player.get_speed())
                elif (self.free_path(move_down_right)):
                    self.player.move(self.player.get_fov().get_angle_to_pos(move_down_right), self.player.get_speed())
            else:
                self.player.move(self.player.get_fov().get_angle_to_pos(move_backwards), self.player.get_speed())
        else:
            move_up_right = (pos[0] - 2*player_size[0], pos[1] + 5*player_size[0])
            move_down_right = (pos[0] - 2*player_size[0], pos[1] - 5*player_size[0])
            move_backwards = (pos[0] + 2*player_size[0], pos[1])
            move_forward = (pos[0] - 2*player_size[0], pos[1])

            if ((move_forward[0] > self.player.get_team().get_field().ls_goal_area_singleline[0][0])):
                if(self.free_path(move_forward)):
                    self.player.move(self.player.get_fov().get_angle_to_pos(move_forward), self.player.get_speed())
                elif(self.free_path(move_up_right)):
                    self.player.move(self.player.get_fov().get_angle_to_pos(move_up_right), self.player.get_speed())
                elif (self.free_path(move_down_right)):
                    self.player.move(self.player.get_fov().get_angle_to_pos(move_down_right), self.player.get_speed())
            else:
                self.player.move(self.player.get_fov().get_angle_to_pos(move_backwards), self.player.get_speed())

    def mark(self):
        side = self.player.get_side()
        pos = self.player.get_pos()
        if(side == 0):
            move_backwards = (pos[0] - 2*player_size[0], half_height)         
            self.player.move(self.player.get_fov().get_angle_to_pos(move_backwards), self.player.get_speed())
        else:
            move_backwards = (pos[0] + 2*player_size[0], half_height)
            self.player.move(self.player.get_fov().get_angle_to_pos(move_backwards), self.player.get_speed())
    
    def search_ball(self) -> bool:
        ball = self.player.get_team().get_field().get_ball()
        angle_to_ball = self.player.get_fov().get_angle_to_object(ball)
        while not self.player.get_fov().is_sprite_at_view(ball):
            self.spin(angle_to_ball)
            if(self.player.get_angle() == angle_to_ball):
                return False

        distance = math.sqrt(((self.player.get_pos()[0] - ball.get_pos()[0])**2 + (self.player.get_pos()[1] - ball.get_pos()[1])**2))
        return distance < 6*player_size[0]
