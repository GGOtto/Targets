# Name: Targets
# Author: G.G.Otto
# Date: 1/14/2021
# Version 2.0

# Soundtrack from freemusicarchives.com
# Sound effects from soundbible.com
# Graphics made by G.G.Otto

import pygame, random, time, math
from pygame.locals import *
import os.path as path

class TargetSound(pygame.mixer.Sound):
    '''represents a sound object with attribute self.played and method self.is_playing'''

    def __init__(self, file, volume, game):
        '''TargetSound(file, volume, game) -> TargetSound
        constructs the sound object'''
        pygame.mixer.Sound.__init__(self, file)
        self.playable = True
        self.game = game
        self.game.add_sound(self)
        self.originVolume = volume
        self.set_volume(volume)

    def is_playable(self):
        '''TargetSound.is_playable() -> bool
        returns whether the target sound is playing or not'''
        return self.playable

    def set_origin_volume(self, newVolume):
        '''TargetSound.set_origin_volumne(newVolume) -> None
        sets the original volume'''
        self.originVolume = newVolume

        if self.get_volume() != 0:
            self.set_volume(newVolume)

    def set_playable(self, boolean):
        '''TargetSound.set_playable(boolean) -> None
        sets the playable the playable option'''
        self.playable = boolean

    def restore_volume(self):
        '''TargetSound.restore_volume() -> None
        restores the volume to its original state'''
        self.set_volume(self.originVolume)

    def play(self, loops=0):
        '''TargetSound.play(loops) -> None
        plays the sound'''
        pygame.mixer.Sound.play(self, loops=loops)
        self.played = time.time()

class Target:
    '''moves and manipulates the target'''

    def __init__(self, game, pos, size):
        '''Target(game, pos, size) -> Target
        constructs the target for game as pos with size'''
        # image and sounds
        self.origin = pygame.image.load("target2.png")
        self.breakingSound = TargetSound("breaking.wav", 0.55, game)
        self.missSound = TargetSound("miss.wav", 0.4, game)
        self.spawnSound = TargetSound("target_spawn.wav", 0.55, game)
        self.noise = TargetSound("target_noise.wav", 1, game)

        # attributes
        self.game = game
        self.pos = pos
        self.size = 0
        self.speed = 1.5
        self.hideTime = 0
        self.hideWait = 0
        self.breaking = False
        self.randomize()

    def is_hit(self, pos):
        '''Target.is_hit(pos) -> bool
        returns if the target has been hit or not'''
        return not self.breaking and ((self.pos[0]-pos[0])**2+(self.pos[1]-pos[1])**2)**(1/2) < 42*self.size

    def is_off(self):
        '''Target.is_off() -> bool
        returns if the target is off screen or not'''
        return not -80 < self.pos[0] < 980 or not -80 < self.pos[1] < 700 or self.size > 0.8

    def get_worth(self):
        '''Target.get_worth() -> int
        returns how much the target is worth'''
        return int(10-self.size//0.08)

    def add_speed(self, plusSpeed):
        '''Target.add_speed(plusSpeed) -> None
        adds some speed to the target'''
        if self.speed < 5:
            self.speed += plusSpeed

    def randomize(self, wait=0):
        '''Target.randomize(wait=0) -> None
        randomizes the target'''
        self.hideWait = time.time()
        self.hideTime = wait/1000
        
        self.pos = random.randint(400,500), random.randint(300,400)
        self.size = random.randint(0,10)/100
        self.dir = random.randrange(360)
        self.spawnSound.set_playable(True)
        self.noise.stop()
        self.noise.set_playable(True)

    def break_to_pieces(self):
        '''Target.break_to_pieces() -> None
        breaks the target'''
        self.breakingSound.set_playable(True)
        self.breaking = True
        self.breakTime = time.time()
            
    def update(self):
        '''Target.update() -> None
        updates the whole target'''
        if self.game.is_over():
            return
        
        if self.breaking:
            timing = time.time()-self.breakTime
            
            # crack sound
            if self.breakingSound.is_playable() and timing < 0.2:
                self.breakingSound.set_playable(False)
                self.breakingSound.play()

            # crack image
            if timing < 0.4:
                image = pygame.transform.rotozoom(pygame.image.load("target_break1.png"), 0, self.size)
            else:
                self.breaking = False
                self.game.add_bubble(NumberBubble(self.game.get_screen(), self.pos, self.get_worth(), 5))
                self.randomize(1500)

        if time.time() - self.hideWait > self.hideTime:
            # grow and move
            if not self.breaking:
                self.size += 0.003*(self.speed-0.5)
                self.pos = self.pos[0]+self.speed*math.cos(self.dir), self.pos[1]+self.speed*math.sin(self.dir)
                image = pygame.transform.rotozoom(self.origin, 0, self.size)
            self.game.get_screen().blit(image, (self.pos[0]-image.get_rect().width/2, self.pos[1]-image.get_rect().height/2))

            # target noise
            if self.noise.is_playable():
                self.noise.play(loops=2)
                self.noise.set_playable(False)
            self.noise.set_origin_volume(self.size/2+0.2)

        # spawn sound
        elif time.time() - self.hideWait > self.hideTime - 0.2:
            if self.spawnSound.is_playable():
                self.spawnSound.play()
                self.spawnSound.set_playable(False)

        if self.is_off():
            self.game.get_stats().get_lights().flash("red", 8, 0.2)
            self.randomize(2000)
            self.game.get_stats().add_miss()
            self.missSound.play()

            # reset crosshair
            self.game.get_crosshair().stop_shooting()

class Crosshair:
    '''represents the crosshair view for gun sights'''

    def __init__(self, game):
        '''Crosshair(game) -> Crosshair
        constructs the crosshair with game and size'''
        self.game = game
        self.pos = (450,350)

        # directions for event types
        speed = 9
        self.directions = {K_UP: (0,-speed), K_DOWN: (0,speed), K_LEFT: (-speed, 0), K_RIGHT: (speed, 0)}
        self.gunPos = ((40*2**(1/2), 40*2**(1/2)), (40*2**(1/2),-40*2**(1/2)),
            (-40*2**(1/2), 40*2**(1/2)), (-40*2**(1/2), -40*2**(1/2)))
        self.moving = []

        self.laser = Laser(self, (0,255,0))

    def get_gun_pos(self):
        '''Crosshair.get_gun_pos() -> tuple
        returns the positions of the guns'''
        output = []
        for gunPos in self.gunPos:
            output.append((self.pos[0]+gunPos[0], self.pos[1]+gunPos[1]))
        return tuple(output)

    def get_pos(self):
        '''Crosshair.get_pos() -> None
        returns the position of the crosshair'''
        return self.pos

    def set_pos(self, pos):
        '''Crosshair.set_pos(pos) -> None
        sets the postion of the crosshair'''
        self.pos = pos

    def get_game(self):
        '''Crosshair.get_game() -> TargetsGame
        returns the game'''
        return self.game
        
    def fire(self):
        '''Crosshair.fire() -> None
        fires the laser'''
        if not self.game.is_over():
            self.laser.fire()

    def can_fire(self):
        '''Crosshair.can_fire() -> None
        returns whether player can fire or not'''
        return not self.laser.is_running()

    def check_shot(self):
        '''Crosshair.check_shot() -> bool
        returns if hit is true and checks if the shot has hit a target'''
        for target in self.game.get_targets():
            if target.is_hit(self.pos):
                self.game.get_stats().get_lights().flash("green", 8, 0.2)
                target.break_to_pieces()
                target.add_speed(0.135)
                self.game.get_stats().add_hit(target.get_worth())
                return True
            
        self.game.get_stats().get_lights().flash("yellow", 8, 0.2)
        return False

    def stop_shooting(self):
        '''Crosshair.stop_shooting() -> None
        stops shooting the laser'''
        self.laser.stop_shooting()
    
    def start(self, eventType):
        '''Crosshair.start(eventType) -> None
        starts the movement in direction according to eventType'''
        # check if valid
        if eventType not in self.directions:
            return
        if self.directions[eventType] in self.moving:
            return

        self.moving.append(self.directions[eventType])

    def stop(self, eventType):
        '''Crosshair.stop(eventType) -> None
        stops the movement in direction according to eventType'''
        # check if valid
        if eventType not in self.directions:
            return
        if self.directions[eventType] not in self.moving:
            return

        self.moving.remove(self.directions[eventType])

    def update(self):
        '''Crosshair.update() -> None
        updates the crosshair'''        
        # move crosshair
        for move in self.moving:
            if not self.laser.is_running() and 20 <= self.pos[0]+move[0] <= 880 and 20 < self.pos[1]+move[1] < 605:
               self.pos = self.pos[0]+move[0], self.pos[1]+move[1]

        greyFilter = pygame.image.load("gray_filter.png")
        # draw crosshair
        pygame.draw.circle(greyFilter, 0, self.pos, 80)
        self.laser.update(greyFilter)
        pygame.draw.circle(greyFilter, (0,0,0), self.pos, 80, 5)
        pygame.draw.line(greyFilter, (0,0,0), (self.pos[0], self.pos[1]-30), (self.pos[0], self.pos[1]+30))
        pygame.draw.line(greyFilter, (0,0,0), (self.pos[0]-30, self.pos[1]), (self.pos[0]+30, self.pos[1]))

        # draw guns
        for pos in self.get_gun_pos():
            pygame.draw.circle(greyFilter, (0,0,0), pos, 5)
        
        self.game.get_screen().blit(greyFilter, (0,0))
        
class Laser:
    '''represents the laser for the gun'''

    def __init__(self, crosshair, color):
        '''Laser(crosshair, color) -> Laser
        creates a laser for crosshair with color'''
        self.crosshair = crosshair
        self.color = color
        self.running = False
        self.checked = False
        self.hit = False
        self.progress = 0

        # sound for laser
        self.laserSound = TargetSound("laser.wav", 0.4, crosshair.get_game())

    def is_running(self):
        '''Laser.is_running() -> bool
        returns if the laser if firing or not'''
        return self.running

    def fire(self):
        '''Laser.fire() -> None
        fires the laser'''
        self.laserSound.set_playable(True)
        self.running = True
        self.progress = 0

    def stop_shooting(self):
        '''Laser.stop_shooting() -> None
        stops the laser while shooting'''
        self.running = False

    def update(self, surface):
        '''Laser.update(surface) -> None
        updates the laser on surface'''
        if not self.running:
            return

        # update laser length
        if self.progress < 100:
            if self.laserSound.is_playable() and self.progress > 30:
                self.laserSound.set_playable(False)
                self.laserSound.play()
                
            self.progress += 20
            self.endTime = time.time()
            
        elif self.endTime != None and (time.time() - self.endTime > 1 or \
            (self.hit and time.time() - self.endTime > 0.3)):
            self.running = False
            self.endTime = None
            self.checked = False
            self.hit = False
            
        elif not self.checked:
            self.checked = True
            self.hit = self.crosshair.check_shot()            
            
        for pos in self.crosshair.get_gun_pos():
            # distance on axises to crosshair
            crosshair = self.crosshair.get_pos()
            xslope = crosshair[0]-pos[0]
            yslope = crosshair[1]-pos[1]            
            pygame.draw.line(surface, self.color, pos, (pos[0]+xslope*self.progress/100, pos[1]+yslope*self.progress/100), 5)

class Stats:
    '''represents all of the stats for the game'''

    def __init__(self, game):
        '''Stats(game) -> Stats
        constructs the stat bar'''
        self.surface = pygame.image.load("statbar.png")
        self.game = game

        # stat components
        self.lights = Lights(self.surface, (self.surface.get_rect().width/2, 40), 10)
        self.font = pygame.font.SysFont("Arial", 25, bold=True)

        self.score = 0
        self.misses = 0

    def get_lights(self):
        '''Stats.get_lights() -> Lights
        returns the lights for the stat bar'''
        return self.lights

    def get_score(self):
        '''Stats.get_score() -> int
        returns the score'''
        return self.score

    def add_miss(self):
        '''Stats.add_miss() -> None
        adds a miss to the stat bar'''
        if self.misses < 3:
            self.misses += 1
            if self.misses == 3:
                self.game.end_game()

    def add_high(self, high):
        '''add_high(high) -> None
        adds the high to its proper place'''
        high = self.font.render(f"High: {high}", True, (180,180,180))
        self.surface.blit(high, (20,20-high.get_rect().height/2))
        self.game.get_screen().blit(self.surface, (0,700-self.surface.get_rect().height))

    def add_hit(self, score):
        '''Stats.add_hit(score) -> None
        adds a hit to the stat bar'''
        self.score += score

    def update(self):
        '''Stats.update() -> None
        updates the stat bar'''
        # clear all
        self.surface.blit(pygame.image.load("statbar.png"), (0,0))

        # update stat components
        self.lights.update()

        # update text
        score = self.font.render(f"Score: {self.score}", True, (180,180,180))
        self.surface.blit(score, (20,50-score.get_rect().height/2))
        misses = self.font.render(f"Missed: {self.misses}/3", True, (180,180,180))
        self.surface.blit(misses, (880-misses.get_rect().width, 50-misses.get_rect().height/2))

        # sound indicator
        if self.game.is_playing_sound():
            self.surface.blit(pygame.transform.rotozoom(pygame.image.load("sound_on.png"), 0, 0.3), (840,7))
        else:
            self.surface.blit(pygame.transform.rotozoom(pygame.image.load("sound_off.png"), 0, 0.3), (840,7))
                           
        self.game.get_screen().blit(self.surface, (0,700-self.surface.get_rect().height))

class Lights:
    '''represents the row of light indicators'''

    def __init__(self, surface, pos, numLights):
        '''Lights(surface, pos, numLights) -> Lights
        constructs the row of lights'''
        self.lights = [pygame.image.load("light_black.png") for i in range(numLights)]
        self.pos = pos
        self.surface = surface
        self.animations = None
        self.finished = []
        self.animationCount = 0
        self.animationTime = 0

    def is_finished(self, animationId):
        '''Lights.is_finished(animationId) -> bool
        returns whether animation is finished or not'''
        return animationId in self.finished

    def is_animation(self):
        '''Lights.is_animation() -> bool
        returns if lights are animating'''
        return self.animations != None

    def stop(self, clear=True):
        '''Lights.stop(clear) -> None
        stops all animations'''
        self.animations = None
        if clear:
            self.light("all", "black")

    def light(self, lights, color):
        '''Lights.light(lights, color)
        lights up all lights in interval lights to color'''
        # convert to proper form
        if lights == "all":
            lights = (0, len(self.lights))
        elif isinstance(lights, int):
            lights = (lights, lights+1)
        elif isinstance(lights, str):
            if lights.isdigit():
                lights = (int(lights), int(lights)+1)
            else:
                lights = lights.replace("(","").replace(")","")
                lights = (int(lights.split(",")[0]), int(lights.split(",")[1]))
            
        for light in range(lights[0], lights[1]):
            self.lights[light] = pygame.image.load(f"light_{color}.png")

    def flash(self, color, flashAmt=6, speed=0.5):
        '''Lights.flash(color, flashAmt) -> int
        flashes the lights with color for flashAmt times
        returns the animation id'''
        animate = []
        for i in range(flashAmt):
            if i%2 == 0:
                animate.append((f"all, {color}", speed))
            else:
                animate.append(("all, black", speed))

        return self.animate(*tuple(animate))

    def animate(self, *animate):
        '''Lights.animate(animate) -> int
        starts an animation for animate list
        animation in form of ('light_range, light_color', ect, time shown)
        returns the animation id'''
        # if already animating
        if self.animations != None:
            self.finished.append(self.animations[1])
            
        self.animationCount += 1
        self.animations = [list(animate), self.animationCount, time.time()]
        self.animationTime = animate[0][-1]
        return self.animationCount

    def update(self):
        '''Lights.update() -> None
        updates the row of lights'''
        # deal with flash
        if self.animations != None:
            if time.time()-self.animations[-1] > self.animationTime:
                # light lights
                for light in self.animations[0][0][:-1]:
                    light = light.split(", ")
                    self.light(light[0], light[1])
                self.animations[-1] = time.time()
                self.animationTime = self.animations[0][0][-1]
                self.animations[0].pop(0)

                # end flash
                if len(self.animations[0]) == 0:
                    self.finished.append(self.animations[1])
                    self.animations = None
                        
        xpos = self.pos[0]-self.lights[0].get_rect().width*len(self.lights)/2
        for light in self.lights:
            self.surface.blit(light, (xpos,self.pos[1]))
            xpos += light.get_rect().width

class NumberBubble:
    '''number bubble that rises and then fades'''

    def __init__(self, surface, pos, number, timeToFade):
        '''NumberBubble(surface, pos, number, timeToFade) -> NumberBubble
        constructs the number bubble on surface at pos with number'''
        self.surface = surface
        self.pos = pos
        self.timeToFade = timeToFade
        self.start = time.time()
        self.number = number
        self.radius = 40
        self.kill = False
        self.font = pygame.font.SysFont("Arial", 43)

    def set_bubble_list(self, bubbleList):
        '''NumberBubble.set_bubble_list(bubbleList) -> None
        sets the bubbleList to bubbleList'''
        self.bubbleList = bubbleList
        
    def update(self):
        '''NumberBubble.update() -> None
        updates the number bubble'''
        if self.kill:
            return

        self.pos = self.pos[0], self.pos[1]-2
        grey = ((time.time()-self.start)/self.timeToFade)*200
        if grey > 255:
            grey = 255
            
        pygame.draw.circle(self.surface, (grey,grey,grey), self.pos, self.radius, 4)
        text = self.font.render("+"+str(self.number), True, (grey,grey,grey))
        self.surface.blit(text, (self.pos[0]-text.get_rect().width/2, self.pos[1]-text.get_rect().height/2))

        if time.time()-self.start > self.timeToFade:
            self.bubbleList.remove(self)
            self.kill = True    
        
class TargetsGame:
    '''represents the game for targets'''

    def __init__(self):
        '''TargetsGame() -> TargetsGame
        constructs the game of targets'''
        # set up display
        pygame.display.set_caption("Targets")
        pygame.display.set_icon(pygame.image.load("logo.png"))
        self.screen = pygame.display.set_mode((900, 700))
        self.sounds = []

        # setup game objects and attributes
        self.targets = [Target(self, (0,0), 0.5)]
        self.crosshair = Crosshair(self)
        self.stats = Stats(self)
        self.beep = TargetSound("beep3.wav", 0.3, self)
        self.bubbles = []
        self.finalEnd = None
        self.gameOver = False
        self.lastLight = self.targets[0].get_worth()
        self.highScore = self.get_high_score()

        # sound track
        self.soundTrack = TargetSound("track2.mp3", 0.2, self)
        self.soundTrack.play(loops=100)

        # sound volume
        if not self.sound:
            for sound in self.sounds:
                sound.set_volume(0)
        # start game
        self.mainloop()
        pygame.quit()

    def get_screen(self):
        '''TargetsGame.get_screen() -> Surface
        returns the screen for the game'''
        return self.screen

    def get_targets(self):
        '''TargetsGame.get_targets() -> list
        returns a list of all targets'''
        return self.targets

    def get_stats(self):
        '''TargetsGame.get_stats() -> Stats
        returns the stat bar'''
        return self.stats

    def get_crosshair(self):
        '''TargetsGame.get_crosshair() -> Crosshair
        returns the crosshair'''
        return self.crosshair

    def is_over(self):
        '''TargetsGame.is_over() -> bool
        returns if the game is over or not'''
        return self.gameOver

    def is_playing_sound(self):
        '''TargetsGame.is_playing_sound() -> bool
        returns whether the game is playing sound or not'''
        return self.sound

    def add_sound(self, sound):
        '''TargetsGame.add_sound(sound) -> None
        adds a sound to the game'''
        self.sounds.append(sound)

    def add_bubble(self, bubble):
        '''TargetsGame.add_bubble(bubble) -> None
        adds bubble to the bubble list'''
        self.bubbles.append(bubble)
        bubble.set_bubble_list(self.bubbles)

    def update(self):
        '''TargetsGame.update() -> None
        updates a single frame of the game'''
        # update all
        if self.started:
            for bubble in self.bubbles[:]:
                bubble.update()
            for target in self.targets:
                target.update()
            self.crosshair.update()

        # update stats
        self.stats.update()
        if not self.started and self.highScore > 0:
            self.stats.add_high(self.highScore)

        # end game
        if self.finalEnd != None and time.time() - self.finalEnd > 2:
            self.started = False
            self.screen.blit(pygame.image.load("end.png"), (0,0))
            self.stats.get_lights().stop()

            if self.stats.get_score() > self.highScore:
                self.highScore = self.stats.get_score()
                self.save_high_score(self.stats.get_score())
                self.screen.blit(pygame.image.load("high.png"), (0,0))

        # light indicator
        if self.started and not self.stats.get_lights().is_animation() and self.finalEnd == None:
            self.stats.get_lights().light("all", "red")
            self.stats.get_lights().light((10-self.targets[0].get_worth(),10), "green")

        # play sound
        if self.lastLight != self.targets[0].get_worth():
            self.beep.play()
        self.lastLight = self.targets[0].get_worth()
                
    def end_game(self):
        '''Target.end_game() -> None
        ends the game when called'''
        self.gameOver = True
        self.finalEnd = time.time()
        self.soundTrack.fadeout(5000)

    def restart(self):
        '''Target.restart() -> None
        restarts the game'''
        self.sounds = [self.soundTrack, self.beep]
        
        self.gameOver = False
        self.finalEnd = None
        self.targets[0].__init__(self, (0,0), 0.5)
        self.crosshair.__init__(self)
        self.stats.__init__(self)

        if not self.sound:
            for sound in self.sounds:
                sound.set_volume(0)
        
    def mainloop(self):
        '''TargetsGame.mainloop() -> None
        starts the mainloop for the game'''
        # background
        self.background = pygame.image.load("background.png")
        self.started = False

        # title page
        self.screen.blit(self.background, (-1,-65))
        self.screen.blit(pygame.image.load("title.png"), (0,0))

        # main while loop
        running = True
        while running:
            # event loop
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        if not self.started:
                            self.started = True
                            self.animationNum = None
                            self.soundTrack.stop()
                            self.soundTrack.play(loops=100)
                            if self.gameOver:
                                self.restart()
                        elif self.crosshair.can_fire():
                            self.crosshair.fire()
                    elif self.started:
                        self.crosshair.start(event.key)
                if event.type == KEYUP:
                    self.crosshair.stop(event.key)
                if event.type == MOUSEBUTTONDOWN and 840 <= event.pos[0] <= 876 and 627 <= event.pos[1] <= 650:
                    self.sound = not self.sound
                    
                    # stop or start sounds
                    for sound in self.sounds:
                        if self.sound:
                            sound.restore_volume()
                        else:
                            sound.set_volume(0)

                        # save file
                        file = open("targets_high.txt", "w")
                        file.write(str(self.highScore)+" "+str(self.sound))
                        file.close()

            # update game
            if self.started:
                self.screen.blit(self.background, (-1,-65))
                
            self.update()
            pygame.display.update()
            pygame.time.wait(10)

    def get_high_score(self):
        '''TargetsGame.get_high_score() -> int
        returns the high score of the game'''
        if not path.isfile("targets_high.txt"):
            self.sound = True
            return 0
        
        file = open("targets_high.txt")
        content = file.read().split()
        score = int(content[0])

        # sound on
        if len(content) == 2:
            self.sound = content[1] == "True"
        else:
            self.sound = True
            
        file.close()
        return score

    def save_high_score(self, score):
        '''TargetsGame.save_high_score(score) -> None
        saves the high score of the game'''
        file = open("targets_high.txt", "w")
        file.write(str(score)+" "+str(self.sound))
        file.close()

pygame.init()
TargetsGame()
