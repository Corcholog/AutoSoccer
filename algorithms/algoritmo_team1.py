from AutoSoccer import GoalkeeperBehaviour, FieldPlayerBehaviour, Player
# añadir prefijo o sufijo con nombre tuyo a la clase para diferenciar metodos entre nosotros
    
class DefenderBehaviour(FieldPlayerBehaviour):
    def __init__(self, pos: list[float], forwarding) -> None:
        super().__init__(pos, forwarding)
    
    def reventar(self):
        return None

    def try_move_forward(self) -> bool:
        return super().try_move_forward()

    def unmark(self):
        return super().unmark()
    
    def action_blind(self): # forwarding de defensor debe ser menos
        return super().action_blind()

    def flow(self):
        if(self.player.get_team().get_field().get_state() == "Playing"):
            ball = self.player.get_team().get_field().get_ball()
            nearest_to_ball = self.player_has_ball()
            if (nearest_to_ball[0] == self.player):
                target_pass = self.free_teammate(True)
                if(target_pass == None):
                    ######### 
                    if(not self.try_move_forward()): #chequear distancia, maso mitad cancha 
                        target_pass = self.free_teammate(False)
                        if target_pass == None:
                            ### Reventarla para algun lado ###, if abajo mitad de cancha en (y) pateo hacia corner topr_right sino bottom_right
                            self.reventar()
                        else:
                            self.aim_and_pass(target_pass)
                    ########
                else:
                    self.aim_and_pass(target_pass) 
            elif (nearest_to_ball[0] != None) and (nearest_to_ball[0].get_side() == self.player.get_side()):
                # no tienen que pasar mitad de cancha
                self.unmark()
            elif (nearest_to_ball[0] != None) and (nearest_to_ball[0].get_side() != self.player.get_side()):
                if(nearest_to_ball[1] == self.player):
                    angle = self.player.get_fov().get_angle_to_object(ball)
                    self.player.move(angle, self.player.get_speed())
                else:
                    self.mark()
            elif (nearest_to_ball[0] == None) and ((self.player.get_side() == 0 and ball.get_pos()[0] < half_width) or (self.player.get_side() == 1 and ball.get_pos()[0] > half_width)):
                if(nearest_to_ball[1] == self.player and ball.get_speed() != 0):
                    self.intercept(self.player.get_speed())
                elif (nearest_to_ball[1] == self.player and ball.get_speed() == 0):
                    angle = self.player.get_fov().get_angle_to_object(ball)
                    self.player.move(angle, self.player.get_speed())
                else:
                    # redefinir para q vuelvan a posicion inicial, chequear mitad de cancha no posesión del team
                    self.action_blind()
        elif(self.player.get_team().get_field().get_state() == "Out of Game"):
            self.out_of_game()
        else:
            self.score()

class StrikerBehaviour(FieldPlayerBehaviour):
    def __init__(self, pos: list[float], forwarding, strike_pos: list[float]) -> None:
        super().__init__(pos, forwarding)
        self.strike_pos = strike_pos
    
    def free_teammate(self, forward_pass: bool) -> Player:
        return super().free_teammate(forward_pass)
    
    def action_blind(self):
        return super().action_blind()
    
    def flow(self):
        if(self.player.get_team().get_field().get_state() == "Playing"):
            ball = self.player.get_team().get_field().get_ball()
            nearest_to_ball = self.player_has_ball()
            if (nearest_to_ball[0] == self.player):
                if(self.try_score()):
                    self.aim_and_kick()
                else:
                    if(not self.try_move_forward()): 
                        target_pass = self.free_teammate(True) # para adelante o costados
                        if(target_pass == None):
                            # si esta en el area (agregar if acá o que pegue igual) probar pegarle sin chequear area
                            self.aim_and_kick()
                        else:
                            self.aim_and_pass(target_pass) 
            elif (nearest_to_ball[0] != None) and (nearest_to_ball[0].get_side() == self.player.get_side()):
                self.unmark()
            elif (nearest_to_ball[0] != None) and (nearest_to_ball[0].get_side() != self.player.get_side()):
                if(nearest_to_ball[1] == self.player):
                    angle = self.player.get_fov().get_angle_to_object(ball)
                    self.player.move(angle, self.player.get_speed())
                else:
                    # debe chequear mitad de cancha, se mueve desde striker en base a forwarding + o -
                    self.action_blind()
            elif (nearest_to_ball[0] == None):
                if(nearest_to_ball[1] == self.player and ball.get_speed() != 0):
                    self.intercept(self.player.get_speed())
                elif (nearest_to_ball[1] == self.player and ball.get_speed() == 0):
                    angle = self.player.get_fov().get_angle_to_object(ball)
                    self.player.move(angle, self.player.get_speed())
                else:
                    # debe chequear mitad de cancha, se mueve desde striker en base a forwarding + o -
                    self.action_blind()
        elif(self.player.get_team().get_field().get_state() == "Out of Game"):
            self.out_of_game()
        else:
            self.score()