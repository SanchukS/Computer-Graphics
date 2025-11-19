import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import numpy as np
from PIL import Image, ImageTk

# --- Алгоритмы обработки ---

def apply_padding(image, pad_h, pad_w, mode, value=0):
    # Добавляем рамку вокруг изображения для обработки краев
    if mode == 'constant':
        return np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode=mode, constant_values=value)
    return np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode=mode)

def convolve(image, kernel):
    # Свертка изображения с ядром
    h, w = kernel.shape
    pad_h, pad_w = h // 2, w // 2
    padded = apply_padding(image, pad_h, pad_w, 'edge')
    
    output = np.zeros_like(image, dtype=np.float32)
    kernel_sum = kernel.sum()
    if kernel_sum == 0: kernel_sum = 1
    
    # Проходим окном по всему изображению
    rows, cols = image.shape
    for y in range(rows):
        for x in range(cols):
            region = padded[y:y+h, x:x+w]
            val = np.sum(region * kernel)
            output[y, x] = val / kernel_sum
            
    return np.clip(output, 0, 255).astype(np.uint8)

def morphology(image, se, mode):
    # Морфологические операции
    h, w = se.shape
    pad_h, pad_w = h // 2, w // 2
    
    # Для эрозии фон белый (255), для дилатации черный (0)
    pad_val = 255 if mode == 'erosion' else 0
    padded = apply_padding(image, pad_h, pad_w, 'constant', pad_val)
    
    output = np.zeros_like(image)
    rows, cols = image.shape
    
    for y in range(rows):
        for x in range(cols):
            region = padded[y:y+h, x:x+w]
            # Выбираем пиксели, попадающие под маску структурного элемента
            masked = region[se == 1]
            
            if mode == 'erosion':
                # Если все пиксели под маской белые -> ставим белый
                if np.all(masked == 255): output[y, x] = 255
            elif mode == 'dilation':
                # Если хоть один пиксель под маской белый -> ставим белый
                if np.any(masked == 255): output[y, x] = 255
                
    return output

# --- Данные для фильтров ---

def get_kernels():
    # Гаусс 7x7 (аппроксимация)
    gaussian = np.array([
        [1, 1, 2, 2, 2, 1, 1],
        [1, 3, 5, 5, 5, 3, 1],
        [2, 5, 9, 12, 9, 5, 2],
        [2, 5, 12, 15, 12, 5, 2],
        [2, 5, 9, 12, 9, 5, 2],
        [1, 3, 5, 5, 5, 3, 1],
        [1, 1, 2, 2, 2, 1, 1]
    ])
    return {"Однородный 7x7": np.ones((7, 7)), "Гаусс 7x7": gaussian}

def get_se(shape, size):
    if shape == "Крест":
        se = np.zeros((size, size), dtype=np.uint8)
        center = size // 2
        se[center, :] = 1
        se[:, center] = 1
        return se
    return np.ones((size, size), dtype=np.uint8) # Квадрат

# --- Интерфейс ---

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №2")
        self.root.geometry("1100x650")
        self.root.minsize(800, 500)

        self.img_orig = None
        self.img_proc = None
        
        self.setup_ui()

    def setup_ui(self):
        # Левая панель управления
        control_frame = tk.Frame(self.root, width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        control_frame.pack_propagate(False)

        # Правая часть с изображениями
        self.display_frame = tk.Frame(self.root)
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Настройка сетки 1x2
        self.display_frame.grid_columnconfigure(0, weight=1, uniform="group1")
        self.display_frame.grid_columnconfigure(1, weight=1, uniform="group1")
        self.display_frame.grid_rowconfigure(0, weight=1)

        # Рамки для картинок
        frame_orig = tk.LabelFrame(self.display_frame, text="Оригинал")
        frame_orig.grid(row=0, column=0, sticky="nsew", padx=5)
        self.lbl_orig = tk.Label(frame_orig)
        self.lbl_orig.pack(fill=tk.BOTH, expand=True)

        frame_proc = tk.LabelFrame(self.display_frame, text="Результат")
        frame_proc.grid(row=0, column=1, sticky="nsew", padx=5)
        self.lbl_proc = tk.Label(frame_proc)
        self.lbl_proc.pack(fill=tk.BOTH, expand=True)

        # Кнопки и меню
        tk.Button(control_frame, text="Открыть изображение", command=self.load_img).pack(fill=tk.X, pady=5)
        self.btn_save = tk.Button(control_frame, text="Сохранить результат", command=self.save_img, state=tk.DISABLED)
        self.btn_save.pack(fill=tk.X)

        ttk.Separator(control_frame).pack(fill=tk.X, pady=15)

        # Выбор режима
        self.mode_var = tk.StringVar(value="smooth")
        tk.Radiobutton(control_frame, text="Сглаживание", variable=self.mode_var, value="smooth", command=self.toggle_controls).pack(anchor="w")
        tk.Radiobutton(control_frame, text="Морфология", variable=self.mode_var, value="morph", command=self.toggle_controls).pack(anchor="w")

        # Настройки сглаживания
        self.frame_smooth = tk.Frame(control_frame)
        tk.Label(self.frame_smooth, text="Матрица свертки:").pack(anchor="w", pady=(10, 0))
        self.combo_kernel = ttk.Combobox(self.frame_smooth, values=list(get_kernels().keys()), state="readonly")
        self.combo_kernel.current(0)
        self.combo_kernel.pack(fill=tk.X, pady=5)

        # Настройки морфологии
        self.frame_morph = tk.Frame(control_frame)
        tk.Label(self.frame_morph, text="Операция:").pack(anchor="w", pady=(10, 0))
        self.combo_morph = ttk.Combobox(self.frame_morph, values=["Эрозия", "Дилатация", "Размыкание", "Замыкание", "Границы"], state="readonly")
        self.combo_morph.current(0)
        self.combo_morph.pack(fill=tk.X, pady=5)

        tk.Label(self.frame_morph, text="Структурный элемент:").pack(anchor="w", pady=(5, 0))
        self.combo_shape = ttk.Combobox(self.frame_morph, values=["Квадрат", "Крест"], state="readonly")
        self.combo_shape.current(0)
        self.combo_shape.pack(fill=tk.X, pady=5)
        
        tk.Label(self.frame_morph, text="Размер (px):").pack(anchor="w")
        self.spin_size = ttk.Spinbox(self.frame_morph, from_=3, to=21, increment=2)
        self.spin_size.set(3)
        self.spin_size.pack(fill=tk.X, pady=5)

        self.frame_smooth.pack(fill=tk.X) # Показываем сглаживание по умолчанию

        ttk.Separator(control_frame).pack(fill=tk.X, pady=15)
        
        self.btn_apply = tk.Button(control_frame, text="Применить", command=self.process, bg="#dddddd", state=tk.DISABLED)
        self.btn_apply.pack(fill=tk.X, pady=5)
        
        tk.Button(control_frame, text="Сброс", command=self.reset).pack(fill=tk.X)

        # Событие изменения размера окна
        self.display_frame.bind("<Configure>", self.on_resize)

    def toggle_controls(self):
        if self.mode_var.get() == "smooth":
            self.frame_morph.pack_forget()
            self.frame_smooth.pack(fill=tk.X)
        else:
            self.frame_smooth.pack_forget()
            self.frame_morph.pack(fill=tk.X)

    def on_resize(self, event):
        if not self.img_orig: return
        
        # Вычисляем размеры области просмотра
        w = self.display_frame.winfo_width() // 2 - 20
        h = self.display_frame.winfo_height() - 40
        if w < 1 or h < 1: return

        # Считаем коэффициент масштабирования по оригиналу
        iw, ih = self.img_orig.size
        scale = min(w/iw, h/ih)
        new_size = (int(iw * scale), int(ih * scale))

        self.show_image(self.lbl_orig, self.img_orig, new_size)
        self.show_image(self.lbl_proc, self.img_proc, new_size)

    def show_image(self, label, img, size):
        if img:
            # Используем Lanczos для качественного ресайза
            resized = img.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
            label.config(image=photo)
            label.image = photo
        else:
            label.config(image="")
            label.image = None

    def load_img(self):
        path = filedialog.askopenfilename()
        if path:
            try:
                self.img_orig = Image.open(path)
                self.img_proc = None
                self.btn_apply.config(state=tk.NORMAL)
                self.btn_save.config(state=tk.DISABLED)
                self.on_resize(None)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def save_img(self):
        if self.img_proc:
            path = filedialog.asksaveasfilename(defaultextension=".png")
            if path:
                self.img_proc.save(path)

    def reset(self):
        self.img_proc = None
        self.btn_save.config(state=tk.DISABLED)
        self.on_resize(None)

    def process(self):
        if not self.img_orig: return
        
        # Переводим в numpy array
        img_rgb = self.img_orig.convert("RGB")
        arr = np.array(img_rgb)

        if self.mode_var.get() == "smooth":
            # Применяем свертку к каждому каналу R, G, B
            kernel = get_kernels()[self.combo_kernel.get()]
            channels = []
            for i in range(3):
                channels.append(convolve(arr[:,:,i], kernel))
            res = np.stack(channels, axis=2)
            self.img_proc = Image.fromarray(res)
            
        else:
            # Для морфологии нужно бинарное изображение
            # Сначала в оттенки серого, потом порог 128
            gray = np.array(self.img_orig.convert("L"))
            binary = np.where(gray > 128, 255, 0).astype(np.uint8)
            
            se = get_se(self.combo_shape.get(), int(self.spin_size.get()))
            op = self.combo_morph.get()
            
            if op == "Эрозия":
                res = morphology(binary, se, 'erosion')
            elif op == "Дилатация":
                res = morphology(binary, se, 'dilation')
            elif op == "Размыкание":
                tmp = morphology(binary, se, 'erosion')
                res = morphology(tmp, se, 'dilation')
            elif op == "Замыкание":
                tmp = morphology(binary, se, 'dilation')
                res = morphology(tmp, se, 'erosion')
            elif op == "Границы":
                eroded = morphology(binary, se, 'erosion')
                res = binary - eroded
                
            self.img_proc = Image.fromarray(res)

        self.btn_save.config(state=tk.NORMAL)
        self.on_resize(None)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()