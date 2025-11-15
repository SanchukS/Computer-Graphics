import tkinter as tk
from tkinter import colorchooser
import colorsys

class ColorConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Конвертер Цветов (CMYK-RGB-HSV)")
        self.geometry("500x800")

        self.updating = False  # Флаг для предотвращения рекурсивных обновлений

        # Костыль
        self.set_by_cmyk = False
        self.set_by_hsv = False
        self.set_by_rgb = False

        # Переменные для хранения значений
        self.cmyk_vars = [tk.DoubleVar() for _ in range(4)]
        self.rgb_vars = [tk.IntVar() for _ in range(3)]
        self.hsv_vars = [tk.DoubleVar() for _ in range(3)]

        # --- Основной фрейм ---
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Отображение цвета ---
        self.color_display = tk.Label(main_frame, text="", bg="black", height=5)
        self.color_display.pack(fill=tk.X, pady=(0, 10))

        # --- Создание секций для каждой модели ---
        self.create_color_model_ui(main_frame, "CMYK", ["C", "M", "Y", "K"], self.cmyk_vars, [100, 100, 100, 100])
        self.create_color_model_ui(main_frame, "RGB", ["R", "G", "B"], self.rgb_vars, [255, 255, 255])
        self.create_color_model_ui(main_frame, "HSV", ["H", "S", "V"], self.hsv_vars, [360, 100, 100])

        # --- Кнопка выбора цвета ---
        color_picker_btn = tk.Button(main_frame, text="Выбрать цвет из палитры", command=self.pick_color)
        color_picker_btn.pack(pady=10)

        # Установка начального цвета (черный)
        self.update_from_rgb()

    def create_color_model_ui(self, parent, model_name, labels, a_vars, max_values):
        frame = tk.LabelFrame(parent, text=model_name, padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        for i, label in enumerate(labels):
            row = tk.Frame(frame)
            row.pack(fill=tk.X, pady=2)
            
            lbl = tk.Label(row, text=label, width=2)
            lbl.pack(side=tk.LEFT)

            scale = tk.Scale(row, from_=0, to=max_values[i], variable=a_vars[i], orient=tk.HORIZONTAL,
                             command=lambda val, model=model_name: self.update_from_scale(model))
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

            entry = tk.Entry(row, textvariable=a_vars[i], width=5)
            entry.pack(side=tk.LEFT, padx=(5, 0))
            entry.bind("<Return>", lambda event, model=model_name: self.update_from_scale(model))
            
    def pick_color(self):
        # Открывает палитру для выбора цвета
        color = colorchooser.askcolor()
        if color and color[0]:
            r, g, b = color[0]
            self.rgb_vars[0].set(int(r))
            self.rgb_vars[1].set(int(g))
            self.rgb_vars[2].set(int(b))
            self.update_from_rgb()

    def update_from_scale(self, model):
        # Вызывается при изменении значения на слайдере
        if self.updating:
            return
        
        if model == "RGB":
            self.update_from_rgb()
        elif model == "CMYK":
            self.update_from_cmyk()
        elif model == "HSV":
            self.update_from_hsv()

    def update_color_display(self, r, g, b):
        # Обновляет цвет в прямоугольнике
        hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        self.color_display.config(bg=hex_color)

    def update_from_rgb(self):
        # Основная функция обновления, начинает с RGB
        self.updating = True
        
        r, g, b = [v.get() for v in self.rgb_vars]
        self.update_color_display(r, g, b)

        r_ = r / 255.0
        g_ = g / 255.0
        b_ = b / 255.0

        # RGB -> HSV
        if not self.set_by_hsv:
            cmax = max(r_, g_, b_)
            cmin = min(r_, g_, b_)
            delta = cmax - cmin

            if delta < 1e-4:
                h = 0
            elif cmax == r_:
                h = (60 * ((g_ - b_) / delta)) % 360
            elif cmax == g_:
                h = 60 * (((b_ - r_) / delta) + 2)
            else:
                h = 60 * (((r_ - g_) / delta) + 4)

            if cmax < 1e-4:
                s = 0
            else:
                s = delta / cmax

            v = cmax

            self.hsv_vars[0].set(round(h))
            self.hsv_vars[1].set(round(s * 100))
            self.hsv_vars[2].set(round(v * 100))

        # RGB -> CMYK
        if not self.set_by_cmyk:
            if max(r, g, b) < 1e-4:
                r, g, b = 0.001, 0.001, 0.001

            r_ = r / 255.0
            g_ = g / 255.0
            b_ = b / 255.0

            k_val = min(1 - r_, 1 - g_, 1 - b_)
            c = (1 - r_ - k_val) / (1 - k_val)
            m = (1 - g_ - k_val) / (1 - k_val)
            y = (1 - b_ - k_val) / (1 - k_val)
            c, m, y, k = round(c*100), round(m*100), round(y*100), round(k_val*100)

            self.cmyk_vars[0].set(c)
            self.cmyk_vars[1].set(m)
            self.cmyk_vars[2].set(y)
            self.cmyk_vars[3].set(k)
        
        self.updating = False
        self.set_by_cmyk = False
        self.set_by_hsv = False

    def update_from_cmyk(self):
        self.updating = True
        self.set_by_cmyk = True

        c, m, y, k = [v.get() for v in self.cmyk_vars]

        self.cmyk_vars[0].set(round(c))
        self.cmyk_vars[1].set(round(m))
        self.cmyk_vars[2].set(round(y))
        self.cmyk_vars[3].set(round(k))
        
        # CMYK -> RGB
        r = 255 * (1 - c/100) * (1 - k/100)
        g = 255 * (1 - m/100) * (1 - k/100)
        b = 255 * (1 - y/100) * (1 - k/100)

        self.rgb_vars[0].set(round(r))
        self.rgb_vars[1].set(round(g))
        self.rgb_vars[2].set(round(b))
        self.updating = False
        
        self.update_from_rgb() # Пересчитываем все из RGB

    def update_from_hsv(self):
        self.updating = True
        self.set_by_hsv = True
        h, s, v = [var.get() for var in self.hsv_vars]

        self.hsv_vars[0].set(round(h))
        self.hsv_vars[1].set(round(s))
        self.hsv_vars[2].set(round(v))

        # HSV -> RGB
        h = min(h, 359) / 360.0
        s = s / 100.0
        v = v / 100.0

        if s == 0:
            r = g = b = v
        else:
            h_for_i = h * 6
            i = int(h_for_i)
            f = h_for_i - i
            p = v * (1 - s)
            q = v * (1 - f * s)
            t = v * (1 - (1 - f) * s)

            if i == 0:
                r, g, b = v, t, p
            elif i == 1:
                r, g, b = q, v, p
            elif i == 2:
                r, g, b = p, v, t
            elif i == 3:
                r, g, b = p, q, v
            elif i == 4:
                r, g, b = t, p, v
            else:
                r, g, b = v, p, q

        r = round(r * 255)
        g = round(g * 255)
        b = round(b * 255)

        r = min(max(r, 0), 255)
        g = min(max(g, 0), 255)
        b = min(max(b, 0), 255)

        self.rgb_vars[0].set(r)
        self.rgb_vars[1].set(g)
        self.rgb_vars[2].set(b)
        self.updating = False

        self.update_from_rgb() # Пересчитываем все из RGB


if __name__ == "__main__":
    app = ColorConverterApp()
    app.mainloop()