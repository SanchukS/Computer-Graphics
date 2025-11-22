import tkinter as tk
from tkinter import messagebox
import time
import math

class RasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лаб. работа №3: Растровые алгоритмы")
        self.root.geometry("1200x800")

        # Храним масштаб как float для плавности, но используем как int при рисовании
        self.scale = 20.0  
        
        # История рисования для восстановления при зуме
        # Формат: {'func': string_name, 'args': [x1, y1, x2, y2]}
        self.history = [] 

        self.setup_ui()
        self.draw_grid()
        
        # Привязка зума
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom) # Linux скролл вверх
        self.canvas.bind("<Button-5>", self.on_zoom) # Linux скролл вниз

    def setup_ui(self):
        panel = tk.Frame(self.root, padx=10, pady=10, width=250)
        panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(panel, text="Координаты / Радиус", font=("Arial", 10, "bold")).pack(pady=5)
        
        frame_in = tk.Frame(panel)
        frame_in.pack(pady=5)
        
        tk.Label(frame_in, text="X1:").grid(row=0, column=0)
        self.ent_x1 = tk.Entry(frame_in, width=5)
        self.ent_x1.grid(row=0, column=1)
        self.ent_x1.insert(0, "0")

        tk.Label(frame_in, text="Y1:").grid(row=0, column=2)
        self.ent_y1 = tk.Entry(frame_in, width=5)
        self.ent_y1.grid(row=0, column=3)
        self.ent_y1.insert(0, "0")

        tk.Label(frame_in, text="X2:").grid(row=1, column=0)
        self.ent_x2 = tk.Entry(frame_in, width=5)
        self.ent_x2.grid(row=1, column=1)
        self.ent_x2.insert(0, "8")

        tk.Label(frame_in, text="Y2(R):").grid(row=1, column=2)
        self.ent_y2 = tk.Entry(frame_in, width=5)
        self.ent_y2.grid(row=1, column=3)
        self.ent_y2.insert(0, "5")

        tk.Label(panel, text="Алгоритм:", font=("Arial", 10, "bold")).pack(pady=10)
        self.algo_var = tk.StringVar(value="step")
        
        modes = [
            ("1. Пошаговый", "step"),
            ("2. ЦДА", "dda"),
            ("3. Брезенхем (отрезок)", "bres_line"),
            ("4. Брезенхем (окружность)", "bres_circle"),
            ("5. Кастла-Питвея", "castle"),
            ("6. Ву (сглаживание)", "wu")
        ]
        
        for txt, val in modes:
            tk.Radiobutton(panel, text=txt, variable=self.algo_var, value=val, anchor="w").pack(fill=tk.X)

        btn_box = tk.Frame(panel)
        btn_box.pack(pady=15)
        tk.Button(btn_box, text="Построить", command=self.on_build, bg="#ddd", width=15).pack(pady=2)
        tk.Button(btn_box, text="Очистить", command=self.clear_all, width=15).pack(pady=2)

        tk.Label(panel, text="Масштаб (скролл):", font=("Arial", 10, "bold")).pack(pady=5)
        self.lbl_scale = tk.Label(panel, text=f"Scale: {int(self.scale)}")
        self.lbl_scale.pack()

        tk.Label(panel, text="Трассировка:", font=("Arial", 10, "bold")).pack(pady=5)
        self.log_area = tk.Text(panel, height=15, width=32, font=("Consolas", 8))
        self.log_area.pack()

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def on_zoom(self, event):
        # Мультипликативное масштабирование (плавное)
        # Windows: event.delta, Linux: event.num
        factor = 1.1
        if event.num == 5 or event.delta < 0:
            self.scale /= factor
        else:
            self.scale *= factor
        
        # Ограничиваем разумными пределами
        if self.scale < 2.0: self.scale = 2.0
        if self.scale > 200.0: self.scale = 200.0
        
        self.lbl_scale.config(text=f"Scale: {int(self.scale)}")
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        self.draw_grid()
        
        # Перерисовываем историю (silent=True чтобы не спамить в лог при зуме)
        for item in self.history:
            func_name = item['func']
            args = item['args']
            
            if func_name == "step": self.step_algo(*args, silent=True)
            elif func_name == "dda": self.dda_algo(*args, silent=True)
            elif func_name == "bres_line": self.bres_line(*args, silent=True)
            elif func_name == "bres_circle": self.bres_circle(*args, silent=True)
            elif func_name == "castle": self.castle_algo(*args, silent=True)
            elif func_name == "wu": self.wu_algo(*args, silent=True)

    def draw_grid(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx, cy = w // 2, h // 2
        s = int(self.scale)
        
        # Сетка
        for i in range(0, w, s):
            self.canvas.create_line(cx + i, 0, cx + i, h, fill="#f0f0f0")
            self.canvas.create_line(cx - i, 0, cx - i, h, fill="#f0f0f0")
        for i in range(0, h, s):
            self.canvas.create_line(0, cy + i, w, cy + i, fill="#f0f0f0")
            self.canvas.create_line(0, cy - i, w, cy - i, fill="#f0f0f0")

        # Оси
        self.canvas.create_line(cx, 0, cx, h, width=2, arrow=tk.LAST)
        self.canvas.create_line(0, cy, w, cy, width=2, arrow=tk.LAST)
        
        self.canvas.create_text(w-15, cy+15, text="X")
        self.canvas.create_text(cx+15, 15, text="Y")

        # Подписи (адаптивный шаг)
        step_nums = 1
        if s < 30: step_nums = 5
        if s < 10: step_nums = 10
        
        for i in range(step_nums, (w//2)//s + 1, step_nums):
            self.canvas.create_text(cx + i*s, cy + 10, text=str(i), font=("Arial", 7))
            self.canvas.create_text(cx - i*s, cy + 10, text=str(-i), font=("Arial", 7))
            
        for i in range(step_nums, (h//2)//s + 1, step_nums):
            self.canvas.create_text(cx + 10, cy - i*s, text=str(i), font=("Arial", 7))
            self.canvas.create_text(cx + 10, cy + i*s, text=str(-i), font=("Arial", 7))

    def plot(self, x, y, color="black", alpha=1.0):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx, cy = w // 2, h // 2
        s = int(self.scale)

        sx = cx + x * s
        sy = cy - (y + 1) * s 
        
        fill_c = color
        if alpha < 1.0:
            gray = int(255 * (1 - alpha))
            fill_c = f"#{gray:02x}{gray:02x}{gray:02x}"

        self.canvas.create_rectangle(sx, sy, sx + s, sy + s, fill=fill_c, outline="#ccc")

    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def clear_all(self):
        self.history = []
        self.log_area.delete(1.0, tk.END)
        self.redraw()

    def on_build(self):
        try:
            x1 = int(self.ent_x1.get())
            y1 = int(self.ent_y1.get())
            x2 = int(self.ent_x2.get())
            y2 = int(self.ent_y2.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Координаты должны быть целыми")
            return

        mode = self.algo_var.get()
        
        # Сохраняем в историю
        self.history.append({'func': mode, 'args': [x1, y1, x2, y2]})
        
        self.log(f"--- {mode} ---")
        t0 = time.perf_counter_ns()
        
        if mode == "step": self.step_algo(x1, y1, x2, y2, silent=False)
        elif mode == "dda": self.dda_algo(x1, y1, x2, y2, silent=False)
        elif mode == "bres_line": self.bres_line(x1, y1, x2, y2, silent=False)
        elif mode == "bres_circle": self.bres_circle(x1, y1, abs(y2), silent=False)
        elif mode == "castle": self.castle_algo(x1, y1, x2, y2, silent=False)
        elif mode == "wu": self.wu_algo(x1, y1, x2, y2, silent=False)

        dt = (time.perf_counter_ns() - t0) / 1_000_000
        self.log(f"Время: {dt:.4f} мс")
        self.log("-" * 10)

    # 1. Пошаговый
    def step_algo(self, x1, y1, x2, y2, silent=False):
        if x1 == x2 and y1 == y2:
            self.plot(x1, y1)
            return
        dx, dy = x2 - x1, y2 - y1
        
        if dx == 0:
            step = 1 if y2 > y1 else -1
            for y in range(y1, y2 + step, step):
                self.plot(x1, y, "blue")
            return

        k = dy / dx
        b = y1 - k * x1
        if not silent: self.log(f"k={k:.2f}, b={b:.2f}")
        
        if abs(dx) >= abs(dy):
            step = 1 if x2 > x1 else -1
            for x in range(x1, x2 + step, step):
                y = k * x + b
                self.plot(x, round(y), "blue")
                if not silent and abs(x-x1) < 3: self.log(f"x={x}, y={y:.2f}")
        else:
            step = 1 if y2 > y1 else -1
            for y in range(y1, y2 + step, step):
                x = (y - b) / k
                self.plot(round(x), y, "blue")

    # 2. ЦДА
    def dda_algo(self, x1, y1, x2, y2, silent=False):
        dx, dy = x2 - x1, y2 - y1
        L = max(abs(dx), abs(dy))
        if L == 0: 
            self.plot(x1, y1, "red")
            return
        sx, sy = dx / L, dy / L
        cx, cy = x1, y1
        for i in range(L + 1):
            self.plot(round(cx), round(cy), "red")
            if not silent and i < 3: self.log(f"{i}: {cx:.1f}, {cy:.1f}")
            cx += sx
            cy += sy

    # 3. Брезенхем (линия)
    def bres_line(self, x1, y1, x2, y2, silent=False):
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        steep = dy > dx
        
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
            dx, dy = abs(x2 - x1), abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            
        err = 2 * dy - dx
        x, y = x1, y1
        
        if not silent: self.log(f"Init err={err}")
        
        for i in range(dx + 1):
            if steep: self.plot(y, x, "green")
            else: self.plot(x, y, "green")
            
            if not silent and i < 3: self.log(f"e={err}")
            
            if err >= 0:
                y += sy
                err -= 2 * dx
            x += sx
            err += 2 * dy

    # 4. Брезенхем (окружность)
    def bres_circle(self, xc, yc, r, silent=False):
        x = 0
        y = r
        d = 3 - 2 * r
        self.draw_sym_circle(xc, yc, x, y)
        while y >= x:
            x += 1
            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6
            self.draw_sym_circle(xc, yc, x, y)
            if not silent and x < 3: self.log(f"x={x}, y={y}, d={d}")

    def draw_sym_circle(self, xc, yc, x, y):
        pts = [(x, y), (-x, y), (x, -y), (-x, -y), (y, x), (-y, x), (y, -x), (-y, -x)]
        for dx, dy in pts:
            self.plot(xc + dx, yc + dy, "purple")

    # 5. Кастла-Питвея
    def castle_algo(self, x1, y1, x2, y2, silent=False):
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        swap = dy > dx
        if swap: dx, dy = dy, dx
        
        a, b = dx, dy
        m1, m2 = ['s'], ['d']
        
        if b == 0:
            ops = ['s'] * a
        else:
            cx, cy = a - b, b
            count = 0
            while cx != cy and count < 1000:
                count += 1
                if cx > cy:
                    cx -= cy
                    m2 = m1 + m2
                else:
                    cy -= cx
                    m1 = m2 + m1
            ops = (m2 + m1) * cx
            
        curr_x, curr_y = x1, y1
        self.plot(curr_x, curr_y, "orange")
        for op in ops:
            if op == 's':
                if not swap: curr_x += sx
                else: curr_y += sy
            else:
                curr_x += sx
                curr_y += sy
            self.plot(curr_x, curr_y, "orange")

    # 6. Ву
    def wu_algo(self, x1, y1, x2, y2, silent=False):
        def ipart(x): return int(x)
        def round_f(x): return ipart(x + 0.5)
        def fpart(x): return x - ipart(x)
        def rfpart(x): return 1 - fpart(x)

        dx, dy = x2 - x1, y2 - y1
        steep = abs(dy) > abs(dx)
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
            dx, dy = dy, dx
        if x2 < x1:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            
        grad = dy / dx if dx != 0 else 1.0
        
        xend = round_f(x1)
        yend = y1 + grad * (xend - x1)
        xgap = rfpart(x1 + 0.5)
        xpxl1 = xend
        ypxl1 = ipart(yend)

        if steep:
            self.plot(ypxl1, xpxl1, alpha=rfpart(yend)*xgap)
            self.plot(ypxl1+1, xpxl1, alpha=fpart(yend)*xgap)
        else:
            self.plot(xpxl1, ypxl1, alpha=rfpart(yend)*xgap)
            self.plot(xpxl1, ypxl1+1, alpha=fpart(yend)*xgap)

        intery = yend + grad
        xend = round_f(x2)
        yend = y2 + grad * (xend - x2)
        xgap = rfpart(x2 + 0.5)
        xpxl2 = xend
        ypxl2 = ipart(yend)
        
        if steep:
            self.plot(ypxl2, xpxl2, alpha=rfpart(yend)*xgap)
            self.plot(ypxl2+1, xpxl2, alpha=fpart(yend)*xgap)
        else:
            self.plot(xpxl2, ypxl2, alpha=rfpart(yend)*xgap)
            self.plot(xpxl2, ypxl2+1, alpha=fpart(yend)*xgap)
            
        for x in range(xpxl1 + 1, xpxl2):
            if steep:
                self.plot(ipart(intery), x, alpha=rfpart(intery))
                self.plot(ipart(intery)+1, x, alpha=fpart(intery))
            else:
                self.plot(x, ipart(intery), alpha=rfpart(intery))
                self.plot(x, ipart(intery)+1, alpha=fpart(intery))
            intery += grad

if __name__ == "__main__":
    root = tk.Tk()
    app = RasterApp(root)
    root.mainloop()