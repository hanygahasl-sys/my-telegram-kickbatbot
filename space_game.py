import tkinter as tk
import random
from PIL import Image, ImageTk
import os # Для работы с путями
class SpaceGame:
    def __init__(self, root):
        # ... (твой существующий код)
        
        # Путь к картинке (если файл лежит в той же папке, что и код)
        image_path = "58c8107c4d6c015acd80659d.png" 
        patrick_path = "1488.png"
        # Загрузка и изменение размера
        self.gary_image = Image.open(image_path).resize((100, 80), Image.Resampling.LANCZOS)
        self.gary_photo = ImageTk.PhotoImage(self.gary_image)
        # В методе __init__
# Замени "patrick.png" на реальное имя твоего файла
        self.patrick_image = Image.open(patrick_path).resize((120, 100), Image.Resampling.LANCZOS)
        self.patrick_photo = ImageTk.PhotoImage(self.patrick_image)
        
        # ... (остальной твой код)
        self.root = root
        self.root.title("Губка Боб: Паника на кухне Красти Краб")
        self.root.resizable(False, False)
        
        self.width = 800
        self.height = 650
        
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#4fa4b8", highlightthickness=0)
        self.canvas.pack()
        
        self.score = 0
        self.max_lives = 3
        self.lives = self.max_lives
        self.game_over = False
        
        self.game_time = 0
        self.frame_counter = 0
        
        self.invulnerable = False
        self.invulnerable_timer = 0
        
        self.bob_w = 46
        self.bob_h = 60
        self.bob_x = self.width // 2 - self.bob_w // 2
        self.bob_y = self.height - 160
        self.bob_speed = 11  
        
        self.shoot_cooldown = 0
        self.shoot_delay = 6  
        self.shot_count = 0
        self.next_golden_shot = random.randint(1, 10)
        
        self.pressed_keys = {"Left": False, "Right": False, "Up": False, "Down": False, "space": False}
        
        self.bullets = []
        self.burgers = []
        self.coals = []
        
        self.plankton = None 
        self.laser_aim = None 
        self.laser_beam = None 
        self.plankton_spawn_cooldown = 350 
        self.plankton_timer = 0
        
        self.squidward = None
        self.squidward_timer = 0
        self.squidward_spawn_cooldown = 400  
        self.ink_drops = []                
        self.ink_puddles = []                
        
        self.patrick = None
        # --- ДОБАВЛЕНО ---
        self.gary = None 

        self.setup_background()
        self.setup_game()
        self.game_loop()

    # --- НОВЫЕ МЕТОДЫ ДЛЯ ГЭРИ ---
   

    def spawn_gary(self):
        if self.gary is not None: return
        side = random.choice([-60, self.width + 10])
        speed = 3 if side < 0 else -3
        # Создаем картинку
        img_id = self.canvas.create_image(side, self.height - 120, image=self.gary_photo, anchor="nw")
        self.gary = {"parts": [img_id], "x": side, "speed": speed}

    def process_gary_logic(self):
        if self.gary is None:
            if random.random() < 0.005: self.spawn_gary()
            return
        
        self.gary["x"] += self.gary["speed"]
        self.canvas.move(self.gary["parts"][0], self.gary["speed"], 0)
        
        # Логика замедления
        for sx in self.stove_positions:
            if abs(self.gary["x"] - (sx + 20)) < 60:
                if self.spawn_timer > 0: self.spawn_timer -= 2
        
        # Удаление
        if (self.gary["speed"] > 0 and self.gary["x"] > self.width) or (self.gary["speed"] < 0 and self.gary["x"] < -60):
            self.canvas.delete(self.gary["parts"][0])
            self.gary = None
    # --- ВСЕ ВАШИ ОСТАЛЬНЫЕ МЕТОДЫ (ОСТАЛИСЬ БЕЗ ИЗМЕНЕНИЙ) ---
    def setup_background(self):
        self.floor_y = self.height - 90
        self.canvas.create_rectangle(0, self.floor_y, self.width, self.height, fill="#94a3b8", outline="")
        for i in range(0, self.width, 40):
            self.canvas.create_line(i, self.floor_y, i, self.height, fill="#64748b")
        for i in range(self.floor_y, self.height, 25):
            self.canvas.create_line(0, i, self.width, i, fill="#64748b")
        self.canvas.create_rectangle(300, 80, 500, 220, fill="#334155", outline="#1e293b", width=4)
        self.canvas.create_rectangle(310, 90, 490, 210, fill="#e2e8f0", outline="")
        self.window_shelf_y = 210

    def draw_spongebob(self, x, y, w, h):
        parts = []
        parts.append(self.canvas.create_rectangle(x, y, x + w, y + h * 0.65, fill="#fff200", outline="#bfae00", width=1))
        parts.append(self.canvas.create_oval(x + 5, y + 8, x + 12, y + 15, fill="#d9c900", outline=""))
        parts.append(self.canvas.create_oval(x + w - 14, y + 10, x + w - 6, y + 18, fill="#d9c900", outline=""))
        parts.append(self.canvas.create_oval(x + 12, y + h*0.4, x + 18, y + h*0.5, fill="#d9c900", outline=""))
        parts.append(self.canvas.create_oval(x + w//2 - 14, y + 12, x + w//2 - 2, y + 24, fill="white", outline="black"))
        parts.append(self.canvas.create_oval(x + w//2 + 2, y + 12, x + w//2 + 14, y + 24, fill="white", outline="black"))
        parts.append(self.canvas.create_oval(x + w//2 - 10, y + 15, x + w//2 - 4, y + 21, fill="#00a2ed", outline=""))
        parts.append(self.canvas.create_oval(x + w//2 + 4, y + 15, x + w//2 + 10, y + 21, fill="#00a2ed", outline=""))
        parts.append(self.canvas.create_line(x + w//2 - 10, y + 28, x + w//2 + 10, y + 28, fill="black", width=2))
        parts.append(self.canvas.create_rectangle(x + w//2 - 4, y + 28, x + w//2 - 1, y + 32, fill="white", outline="black"))
        parts.append(self.canvas.create_rectangle(x + w//2 + 1, y + 28, x + w//2 + 4, y + 32, fill="white", outline="black"))
        parts.append(self.canvas.create_rectangle(x, y + h * 0.65, x + w, y + h * 0.78, fill="white", outline="black"))
        parts.append(self.canvas.create_polygon(x + w//2 - 3, y + h * 0.67, x + w//2 + 3, y + h * 0.67, x + w//2 + 5, y + h * 0.76, x + w//2, y + h * 0.82, x + w//2 - 5, y + h * 0.76, fill="red", outline=""))
        parts.append(self.canvas.create_rectangle(x, y + h * 0.78, x + w, y + h, fill="#603913", outline="black"))
        return parts

    def draw_squidward(self, x, y):
        parts = []
        parts.append(self.canvas.create_rectangle(x + 5, y + 50, x + 45, y + 95, fill="#b45309", outline="#78350f"))
        parts.append(self.canvas.create_rectangle(x + 18, y + 45, x + 32, y + 55, fill="#70a1a4", outline="#4d7275"))
        parts.append(self.canvas.create_oval(x, y, x + 50, y + 50, fill="#70a1a4", outline="#4d7275"))
        parts.append(self.canvas.create_oval(x + 8, y + 15, x + 24, y + 31, fill="white", outline="black"))
        parts.append(self.canvas.create_oval(x + 26, y + 15, x + 42, y + 31, fill="white", outline="black"))
        self.canvas.create_rectangle(x + 8, y + 15, x + 42, y + 22, fill="#70a1a4", outline="") 
        parts.append(self.canvas.create_oval(x + 14, y + 23, x + 18, y + 27, fill="#9333ea", outline="")) 
        parts.append(self.canvas.create_oval(x + 32, y + 23, x + 36, y + 27, fill="#9333ea", outline=""))
        parts.append(self.canvas.create_oval(x + 18, y + 25, x + 32, y + 48, fill="#70a1a4", outline="#4d7275"))
        parts.append(self.canvas.create_line(x + 15, y + 45, x + 35, y + 45, fill="#4d7275", width=2))
        return parts


    # Метод должен быть внутри класса (с отступом в 4 пробела)
    def spawn_patrick(self):
        if self.patrick is not None: return
        px = random.randint(50, self.width - 50)
        py = random.randint(100, self.floor_y - 60)
        img_id = self.canvas.create_image(px, py, image=self.patrick_photo, anchor="center")
        self.patrick = {"id": img_id, "x": px, "y": py, "dx": random.choice([-4, 4]), "dy": random.choice([-2, 2]), "life": 800}

    def process_patrick_logic(self):
        if self.patrick is None:
            if random.random() < 0.005: self.spawn_patrick()
            return
        self.patrick["x"] += self.patrick["dx"]
        self.patrick["y"] += self.patrick["dy"]
        self.canvas.move(self.patrick["id"], self.patrick["dx"], self.patrick["dy"])
        if self.patrick["x"] <= 40 or self.patrick["x"] >= self.width - 40: self.patrick["dx"] *= -1
        if self.patrick["y"] <= 100 or self.patrick["y"] >= self.floor_y - 40: self.patrick["dy"] *= -1
        self.patrick["life"] -= 1
        if self.patrick["life"] <= 0:
            self.canvas.delete(self.patrick["id"])
            self.patrick = None
    
    
    def setup_game(self):
        self.shelf_rect = self.canvas.create_rectangle(290, self.window_shelf_y, 510, self.window_shelf_y + 15, fill="#b45309", outline="black")
        for bx in [60, self.width - 60]:
            self.canvas.create_oval(bx-25, self.floor_y-15, bx+25, self.floor_y+10, fill="#78350f", outline="black")
            self.canvas.create_rectangle(bx-20, self.floor_y, bx+20, self.floor_y+50, fill="#92400e", outline="black")
        self.stove_w = 90
        self.stove_h = 65
        self.stove_positions = [30, 140, self.width - 230, self.width - 120] 
        for sx in self.stove_positions:
            self.canvas.create_rectangle(sx, self.height - self.stove_h, sx + self.stove_w, self.height, fill="#475569", outline="#0f172a", width=2)
            self.canvas.create_rectangle(sx + 10, self.height - self.stove_h, sx + self.stove_w - 10, self.height - self.stove_h + 6, fill="#ef4444", outline="")
            for rx in range(15, self.stove_w - 10, 20):
                self.canvas.create_oval(sx+rx, self.height-30, sx+rx+8, self.height-22, fill="#94a3b8", outline="black")
        self.bob_parts = self.draw_spongebob(self.bob_x, self.bob_y, self.bob_w, self.bob_h)
        self.score_text = self.canvas.create_text(70, 25, text=f"SCORE: {self.score}", fill="white", font=("Helvetica", 14, "bold"))
        self.timer_text = self.canvas.create_text(70, 50, text="TIME: 0s", fill="yellow", font=("Helvetica", 14, "bold"))
        self.lives_text = self.canvas.create_text(self.width - 80, 25, text=f"LIVES: {'❤️' * self.lives}", fill="#ff4500", font=("Helvetica", 14, "bold"))
        self.root.bind("<KeyPress-Left>", lambda e: self.set_key_state("Left", True))
        self.root.bind("<KeyPress-Right>", lambda e: self.set_key_state("Right", True))
        self.root.bind("<KeyPress-Up>", lambda e: self.set_key_state("Up", True))
        self.root.bind("<KeyPress-Down>", lambda e: self.set_key_state("Down", True))
        self.root.bind("<KeyPress-space>", lambda e: self.set_key_state("space", True))
        self.root.bind("<KeyRelease-Left>", lambda e: self.set_key_state("Left", False))
        self.root.bind("<KeyRelease-Right>", lambda e: self.set_key_state("Right", False))
        self.root.bind("<KeyRelease-Up>", lambda e: self.set_key_state("Up", False))
        self.root.bind("<KeyRelease-Down>", lambda e: self.set_key_state("Down", False))
        self.root.bind("<KeyRelease-space>", lambda e: self.set_key_state("space", False))
        self.root.bind("<Key-r>", lambda e: self.restart())
        self.spawn_timer = 0
        self.coal_timer = 0
        self.plankton_timer = 0
        self.squidward_timer = 0

    def set_key_state(self, key, state):
        self.pressed_keys[key] = state

    def update_bob_movement(self):
        if self.game_over: return
        dx, dy = 0, 0
        if self.pressed_keys["Left"]:  dx -= self.bob_speed
        if self.pressed_keys["Right"]: dx += self.bob_speed
        if self.pressed_keys["Up"]:    dy -= self.bob_speed
        if self.pressed_keys["Down"]:  dy += self.bob_speed
        if dx == 0 and dy == 0: return
        new_x = self.bob_x + dx
        new_y = self.bob_y + dy
        if 0 <= new_x <= self.width - self.bob_w:
            self.bob_x = new_x
            for part in self.bob_parts: self.canvas.move(part, dx, 0)
        if 0 <= new_y <= self.height - self.bob_h - self.stove_h:
            self.bob_y = new_y
            for part in self.bob_parts: self.canvas.move(part, 0, dy)

    def draw_burger(self, x, y, w, h):
        items = []
        items.append(self.canvas.create_oval(x, y + h*0.7, x + w, y + h, fill="#bf8f5f", outline=""))
        items.append(self.canvas.create_rectangle(x + 2, y + h*0.5, x + w - 2, y + h*0.75, fill="#5c4033", outline=""))
        items.append(self.canvas.create_polygon(x, y + h*0.55, x + w, y + h*0.55, x + w//2, y + h*0.65, fill="#ffcc00", outline=""))
        items.append(self.canvas.create_oval(x - 2, y + h*0.35, x + w + 2, y + h*0.5, fill="#3cd878", outline=""))
        items.append(self.canvas.create_oval(x, y, x + w, y + h*0.45, fill="#dca87a", outline=""))
        return items

    def draw_plankton(self, x, y):
        parts = []
        parts.append(self.canvas.create_oval(x, y + 15, x + 40, y + 35, fill="#78716c", outline="#44403c"))
        parts.append(self.canvas.create_rectangle(x + 10, y + 20, x + 30, y + 28, fill="#38bdf8", outline=""))
        parts.append(self.canvas.create_oval(x + 14, y, x + 26, y + 22, fill="#065f46", outline=""))
        parts.append(self.canvas.create_oval(x + 17, y + 4, x + 23, y + 10, fill="white", outline="black"))
        parts.append(self.canvas.create_oval(x + 19, y + 6, x + 21, y + 8, fill="red", outline=""))
        parts.append(self.canvas.create_line(x + 16, y, x + 10, y - 8, fill="#065f46", width=2))
        parts.append(self.canvas.create_line(x + 24, y, x + 30, y - 8, fill="#065f46", width=2))
        return parts

    def spawn_plankton_boss(self):
        if self.plankton is not None: return
        sx = random.choice(self.stove_positions)
        x = sx + (self.stove_w // 2) - 20
        y = self.height - self.stove_h - 40
        parts = self.draw_plankton(x, y)
        target_x = self.bob_x + (self.bob_w // 2)
        aim_id = self.canvas.create_line(target_x, 0, target_x, y, fill="#f43f5e", width=2, dash=(4, 4))
        self.plankton = {"parts": parts, "target_x": target_x, "state": "aiming", "timer": 150}
        self.laser_aim = aim_id

    def process_plankton_logic(self):
        if self.plankton is None: return
        self.plankton["timer"] -= 1
        if self.plankton["state"] == "aiming":
            if self.plankton["timer"] <= 0:
                self.canvas.delete(self.laser_aim)
                self.laser_aim = None
                lx = self.plankton["target_x"]
                self.laser_beam = self.canvas.create_line(lx, 0, lx, self.height - self.stove_h - 25, fill="#ef4444", width=18)
                self.plankton["state"] = "shooting"
                self.plankton["timer"] = 25 
                if (self.bob_x <= lx <= self.bob_x + self.bob_w) and not self.invulnerable:
                    self.take_damage()
        elif self.plankton["state"] == "shooting":
            if self.plankton["timer"] <= 0:
                self.canvas.delete(self.laser_beam)
                self.laser_beam = None
                self.plankton["state"] = "leaving"
                self.plankton["timer"] = 30 
        elif self.plankton["state"] == "leaving":
            for part in self.plankton["parts"]: self.canvas.move(part, 0, 3)
            if self.plankton["timer"] <= 0:
                for part in self.plankton["parts"]: self.canvas.delete(part)
                self.plankton = None

    def spawn_squidward_boss(self):
        if self.squidward is not None: return
        x = 375
        y = 215
        parts = self.draw_squidward(x, y)
        self.canvas.tag_raise(self.shelf_rect)
        self.squidward = {"parts": parts, "x": x, "y": y, "state": "rising", "timer": 45}

    def process_squidward_logic(self):
        if self.squidward is None: return
        self.squidward["timer"] -= 1
        if self.squidward["state"] == "rising":
            for part in self.squidward["parts"]: self.canvas.move(part, 0, -2.2)
            self.squidward["y"] -= 2.2
            if self.squidward["timer"] <= 0:
                self.squidward["state"] = "spraying"
                self.squidward["timer"] = 90
        elif self.squidward["state"] == "spraying":
            if self.squidward["timer"] % 20 == 0:
                sx = 400 
                sy = self.squidward["y"] + 35
                target_x = random.randint(40, self.width - 40)
                target_y = random.randint(180, self.floor_y - 10)
                distance_x = target_x - sx
                distance_y = target_y - sy
                steps = random.randint(30, 45)
                speed_x = distance_x / steps
                speed_y = distance_y / steps
                drop_id = self.canvas.create_oval(sx-7, sy-7, sx+7, sy+7, fill="#1e1b4b", outline="#312e81", width=1)
                self.ink_drops.append({"id": drop_id, "x": sx, "y": sy, "sx": speed_x, "sy": speed_y, "target_y": target_y})
            if self.squidward["timer"] <= 0:
                self.squidward["state"] = "hiding"
                self.squidward["timer"] = 45
        elif self.squidward["state"] == "hiding":
            for part in self.squidward["parts"]: self.canvas.move(part, 0, 2.2)
            self.squidward["y"] += 2.2
            if self.squidward["timer"] <= 0:
                for part in self.squidward["parts"]: self.canvas.delete(part)
                self.squidward = None

    def process_ink_physics(self):
        for drop in self.ink_drops[:]:
            self.canvas.move(drop["id"], drop["sx"], drop["sy"])
            drop["x"] += drop["sx"]
            drop["y"] += drop["sy"]
            if drop["sy"] >= 0 and drop["y"] >= drop["target_y"]:
                self.canvas.delete(drop["id"])
                puddle_id = self.canvas.create_oval(drop["x"]-15, drop["y"]-5, drop["x"]+15, drop["y"]+5, fill="#111827", outline="")
                self.ink_puddles.append({"id": puddle_id, "x": drop["x"], "y": drop["y"], "r": 15, "lifetime": 200})
                self.ink_drops.remove(drop)
            elif drop["y"] >= self.floor_y:
                self.canvas.delete(drop["id"])
                self.ink_drops.remove(drop)
        for puddle in self.ink_puddles[:]:
            puddle["lifetime"] -= 1
            if puddle["lifetime"] > 170 and puddle["r"] < 40:
                puddle["r"] += 1
                self.canvas.coords(puddle["id"], puddle["x"]-puddle["r"], puddle["y"]-5, puddle["x"]+puddle["r"], puddle["y"]+5)
            if puddle["lifetime"] < 30:
                self.canvas.itemconfig(puddle["id"], state="hidden" if puddle["lifetime"] % 4 == 0 else "normal")
            if puddle["lifetime"] <= 0:
                self.canvas.delete(puddle["id"])
                self.ink_puddles.remove(puddle)
                continue
            if not self.invulnerable:
                if (puddle["x"] - puddle["r"] < self.bob_x + self.bob_w and puddle["x"] + puddle["r"] > self.bob_x and puddle["y"] - 12 < self.bob_y + self.bob_h and puddle["y"] + 12 > self.bob_y):
                    if puddle["lifetime"] % 22 == 0: self.take_damage()
            for burger in self.burgers[:]:
                if (puddle["x"] - puddle["r"] < burger["x"] + burger["w"] and puddle["x"] + puddle["r"] > burger["x"] and puddle["y"] - 15 < burger["y"] + burger["h"] and puddle["y"] + 15 > burger["y"]):
                    if puddle["lifetime"] % 22 == 0:
                        burger["hp"] -= 1
                        if burger["hp"] <= 0:
                            self.score += burger["max_hp"]
                            self.canvas.itemconfig(self.score_text, text=f"SCORE: {self.score}")
                            for part in burger["parts"]: self.canvas.delete(part)
                            self.canvas.delete(burger["text"])
                            if burger in self.burgers: self.burgers.remove(burger)
                        else: self.canvas.itemconfig(burger["text"], text=str(burger["hp"]))

    def sample_fix_z_order(self):
        if self.game_over: return
        self.canvas.tag_raise(self.shelf_rect)

    def spawn_burger_enemy(self):
        burger_w, burger_h = 65, 50
        x = random.randint(20, self.width - burger_w - 20)
        y = -burger_h
        hp = random.randint(1, 10)
        burger_parts = self.draw_burger(x, y, burger_w, burger_h)
        text_id = self.canvas.create_text(x + burger_w // 2, y + burger_h // 2, text=str(hp), fill="white", font=("Helvetica", 14, "bold"))
        speed_x = random.uniform(-1.2, 1.2)
        self.burgers.append({"parts": burger_parts, "text": text_id, "hp": hp, "max_hp": hp, "x": x, "y": y, "w": burger_w, "h": burger_h, "speed_x": speed_x})

    def spawn_coal(self):
        stove_x = random.choice(self.stove_positions)
        coal_radius = random.randint(7, 12)
        x = stove_x + self.stove_w // 2
        y = self.height - self.stove_h - 5
        speed_y = random.uniform(-2.8, -4.5)
        speed_x = random.uniform(-1.5, 1.5)
        coal_id = self.canvas.create_oval(x - coal_radius, y - coal_radius, x + coal_radius, y + coal_radius, fill="#ff4500", outline="#ffcc00", width=1)
        self.coals.append({"id": coal_id, "x": x, "y": y, "r": coal_radius, "speed_y": speed_y, "speed_x": speed_x})

    def draw_spatula(self, x, y, is_golden=False):
        parts = []
        fill_color = "#FFD700" if is_golden else "#b45309"
        parts.append(self.canvas.create_rectangle(x - 2, y + 12, x + 2, y + 32, fill=fill_color, outline=""))
        head_color = "#EAB308" if is_golden else "#94a3b8"
        parts.append(self.canvas.create_rectangle(x - 8, y, x + 8, y + 12, fill=head_color, outline="#64748b"))
        for i in [-4, 0, 4]:
            parts.append(self.canvas.create_line(x + i, y + 3, x + i, y + 9, fill="#475569"))
        return parts

    def process_shooting_logic(self):
        if self.game_over: return
        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        if self.pressed_keys["space"] and self.shoot_cooldown == 0:
            self.shot_count += 1
            is_golden = False
            if self.shot_count >= self.next_golden_shot:
                is_golden = True
                self.shot_count = 0
                self.next_golden_shot = random.randint(1, 10)
            nose_x = self.bob_x + self.bob_w // 2
            nose_y = self.bob_y - 32
            spatula_parts = self.draw_spatula(nose_x, nose_y, is_golden)
            self.bullets.append({"parts": spatula_parts, "x": nose_x, "y": nose_y, "is_golden": is_golden})
            self.shoot_cooldown = self.shoot_delay

    def take_damage(self):
        if self.invulnerable: return
        self.lives -= 1
        self.canvas.itemconfig(self.lives_text, text=f"LIVES: {'❤️' * self.lives}")
        if self.lives <= 0:
            self.end_game()
        else:
            self.invulnerable = True
            self.invulnerable_timer = 75
            for coal in self.coals: self.canvas.delete(coal["id"])
            self.coals.clear()

    def game_loop(self):
        if not self.game_over:
            self.frame_counter += 1
            if self.frame_counter >= 50:
                self.game_time += 1
                self.frame_counter = 0
                self.canvas.itemconfig(self.timer_text, text=f"TIME: {self.game_time}s")
            self.update_bob_movement()
            self.process_shooting_logic()
            if self.invulnerable:
                self.invulnerable_timer -= 1
                state = "hidden" if (self.invulnerable_timer // 5) % 2 == 0 else "normal"
                for part in self.bob_parts: self.canvas.itemconfig(part, state=state)
                if self.invulnerable_timer <= 0:
                    self.invulnerable = False
                    for part in self.bob_parts: self.canvas.itemconfig(part, state="normal")
            self.process_plankton_logic()
            self.process_squidward_logic()
            self.process_patrick_logic()
            # --- ВЫЗОВ ЛОГИКИ ГЭРИ ---
            self.process_gary_logic()
            self.process_ink_physics()
            self.sample_fix_z_order()
            self.spawn_timer += 1
            if self.spawn_timer >= 45: 
                self.spawn_burger_enemy()
                self.spawn_timer = 0
            self.coal_timer += 1
            if self.coal_timer >= 40: 
                self.spawn_coal()
                self.coal_timer = 0
            self.plankton_timer += 1
            if self.plankton_timer >= self.plankton_spawn_cooldown:
                self.spawn_plankton_boss()
                self.plankton_timer = 0
            self.squidward_timer += 1
            if self.squidward_timer >= self.squidward_spawn_cooldown:
                self.spawn_squidward_boss()
                self.squidward_timer = 0
            # Движение объектов...
            for bullet in self.bullets[:]:
                for part in bullet["parts"]: self.canvas.move(part, 0, -25)
                bullet["y"] -= 25
                if bullet["y"] < -40:
                    for part in bullet["parts"]: self.canvas.delete(part)
                    self.bullets.remove(bullet)
            for coal in self.coals[:]:
                self.canvas.move(coal["id"], coal["speed_x"], coal["speed_y"])
                coal["x"] += coal["speed_x"]
                coal["y"] += coal["speed_y"]
                if coal["x"] - coal["r"] <= 0 or coal["x"] + coal["r"] >= self.width: coal["speed_x"] = -coal["speed_x"]
                if coal["y"] < -20:
                    self.canvas.delete(coal["id"])
                    self.coals.remove(coal)
                    continue
                if (coal["x"] - coal["r"] < self.bob_x + self.bob_w and coal["x"] + coal["r"] > self.bob_x and coal["y"] - coal["r"] < self.bob_y + self.bob_h and coal["y"] + coal["r"] > self.bob_y):
                    self.take_damage()
            for burger in self.burgers[:]:
                for part in burger["parts"]: self.canvas.move(part, burger["speed_x"], 1.5)
                self.canvas.move(burger["text"], burger["speed_x"], 1.5)
                burger["x"] += burger["speed_x"]
                burger["y"] += 1.5
                if burger["x"] <= 0 or burger["x"] + burger["w"] >= self.width: burger["speed_x"] = -burger["speed_x"]
                if burger["y"] > self.floor_y:
                    self.end_game()
                    return
                if (burger["x"] < self.bob_x + self.bob_w and burger["x"] + burger["w"] > self.bob_x and burger["y"] < self.bob_y + self.bob_h and burger["y"] + burger["h"] > self.bob_y):
                    self.take_damage()
                for bullet in self.bullets[:]:
                    if (burger["x"] < bullet["x"] < burger["x"] + burger["w"] and burger["y"] < bullet["y"] < burger["y"] + burger["h"]):
                        damage = 10 if bullet["is_golden"] else 2
                        for part in bullet["parts"]: self.canvas.delete(part)
                        if bullet in self.bullets: self.bullets.remove(bullet)
                        burger["hp"] -= damage
                        if burger["hp"] <= 0:
                            self.score += burger["max_hp"]
                            self.canvas.itemconfig(self.score_text, text=f"SCORE: {self.score}")
                            for part in burger["parts"]: self.canvas.delete(part)
                            self.canvas.delete(burger["text"])
                            self.burgers.remove(burger)
                            break
                        else: self.canvas.itemconfig(burger["text"], text=str(burger["hp"]))
            self.root.after(20, self.game_loop)

    def end_game(self):
        self.game_over = True
        for key in self.pressed_keys: self.pressed_keys[key] = False
        for part in self.bob_parts: self.canvas.itemconfig(part, state="normal")
        if self.laser_aim: self.canvas.delete(self.laser_aim)
        if self.laser_beam: self.canvas.delete(self.laser_beam)
        if self.plankton:
            for part in self.plankton["parts"]: self.canvas.delete(part)
            self.plankton = None
        if self.squidward:
            for part in self.squidward["parts"]: self.canvas.delete(part)
            self.squidward = None
        for drop in self.ink_drops: self.canvas.delete(drop["id"])
        for puddle in self.ink_puddles: self.canvas.delete(puddle["id"])
        self.ink_drops.clear()
        self.ink_puddles.clear()
        self.canvas.create_text(self.width//2, self.height//3, text="ИГРА ОКОНЧЕНА", fill="#ef4444", font=("Helvetica", 26, "bold"))
        self.canvas.create_text(self.width//2, self.height//2, text=f"Финальный счет: {self.score}", fill="white", font=("Helvetica", 16, "bold"))
        self.canvas.create_text(self.width//2, self.height//2 + 40, text="Нажмите 'R' для перезапуска", fill="#00ffff", font=("Helvetica", 12, "bold"))

    def restart(self):
        if not self.game_over: return
        self.canvas.delete("all")
        self.score, self.lives = 0, self.max_lives
        self.game_over = False
        self.invulnerable = False
        self.game_time, self.frame_counter, self.shot_count = 0, 0, 0
        self.bob_x = self.width // 2 - self.bob_w // 2
        self.bob_y = self.height - 160
        self.shoot_cooldown = 0
        for key in self.pressed_keys: self.pressed_keys[key] = False
        self.bullets.clear(); self.burgers.clear(); self.coals.clear()
        self.plankton = None; self.laser_aim = None; self.laser_beam = None
        self.squidward = None; self.ink_drops.clear(); self.ink_puddles.clear()
        # --- ОЧИСТКА ГЭРИ ---
        self.gary = None
        self.setup_background()
        self.setup_game()
        self.game_loop()

if __name__ == "__main__":
    root = tk.Tk()
    game = SpaceGame(root)
    root.mainloop()