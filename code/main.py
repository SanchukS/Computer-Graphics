import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

# Реализация алгоритмов

def _apply_padding(image, kernel_shape):
    k_h, k_w = kernel_shape
    pad_top = k_h // 2
    pad_bottom = k_h - pad_top - 1
    pad_left = k_w // 2
    pad_right = k_w - pad_left - 1
    
    padded_image = cv2.copyMakeBorder(image, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_REPLICATE)
    return padded_image

def manual_median_filter(image, kernel_size):
    if len(image.shape) == 3:
        h, w, c = image.shape
        output_image = np.zeros_like(image)
        for i in range(c):
            output_image[:, :, i] = manual_median_filter(image[:, :, i], kernel_size)
        return output_image

    h, w = image.shape
    padded_image = _apply_padding(image, (kernel_size, kernel_size))
    output_image = np.zeros_like(image)

    for y in range(h):
        for x in range(w):
            neighborhood = padded_image[y : y + kernel_size, x : x + kernel_size]
            output_image[y, x] = np.median(neighborhood)
            
    return output_image

def manual_dilate(image, kernel):
    k_h, k_w = kernel.shape
    padded_image = _apply_padding(image, (k_h, k_w))
    output_image = np.zeros_like(image)
    h, w = image.shape
    
    for y in range(h):
        for x in range(w):
            neighborhood = padded_image[y : y + k_h, x : x + k_w]
            masked_neighborhood = neighborhood[kernel != 0]
            output_image[y, x] = np.max(masked_neighborhood)
            
    return output_image

# Графический интерфейс

class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа 2")

        self.original_image = None
        self.processed_image = None
        
        top_frame = ttk.Frame(root, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        image_frame = ttk.Frame(root, padding=10)
        image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        ttk.Button(top_frame, text="Загрузить изображение", command=self.load_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Настроить и применить", command=self.open_settings_dialog).pack(side=tk.LEFT, padx=5)

        self.orig_label = ttk.Label(image_frame, text="Исходное изображение", relief="solid", anchor=tk.CENTER)
        self.orig_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.proc_label = ttk.Label(image_frame, text="Преобразованное изображение", relief="solid", anchor=tk.CENTER)
        self.proc_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

    def load_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.webp")])
        if not filepath: return
        
        try:
            pil_image = Image.open(filepath).convert('RGB')
            numpy_image = np.array(pil_image)
            self.original_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
            
            self.display_image(self.original_image, self.orig_label)
            self.proc_label.config(image='', text="Преобразованное изображение")
            self.proc_label.image = None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")

    def open_settings_dialog(self):
        if self.original_image is None:
            messagebox.showwarning("Внимание", "Сначала загрузите изображение!")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки алгоритма")
        dialog.geometry("300x220")
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Выберите алгоритм:").pack(anchor=tk.W)
        algorithm_var = tk.StringVar(value="Медианный фильтр")
        ttk.Radiobutton(main_frame, text="Медианный фильтр", variable=algorithm_var, value="Медианный фильтр").pack(anchor=tk.W)
        ttk.Radiobutton(main_frame, text="Дилатация", variable=algorithm_var, value="Дилатация").pack(anchor=tk.W)

        kernel_var = tk.IntVar(value=5)
        kernel_label_text = tk.StringVar()

        def update_label(value):
            int_value = int(float(value))
            kernel_label_text.set(f"Размер ядра: {int_value}")

        update_label(kernel_var.get()) 
        
        ttk.Label(main_frame, textvariable=kernel_label_text).pack(anchor=tk.W, pady=(10,0))
        
        ttk.Scale(main_frame, from_=1, to=15, orient=tk.HORIZONTAL, variable=kernel_var, command=update_label, length=280).pack()

        def on_apply():
            k_size = kernel_var.get()
            algo = algorithm_var.get()
            dialog.destroy()
            self.apply_processing(algo, k_size)
        
        ttk.Button(main_frame, text="Применить", command=on_apply).pack(pady=10)

    def apply_processing(self, algorithm, kernel_size):
        k_size = max(1, kernel_size if kernel_size % 2 != 0 else kernel_size + 1)
        
        if algorithm == "Медианный фильтр":
            self.processed_image = manual_median_filter(self.original_image, k_size)
        
        elif algorithm == "Дилатация":
            gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
            result = manual_dilate(binary, kernel)
            self.processed_image = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            
        self.display_image(self.processed_image, self.proc_label)
        
    def display_image(self, cv_image, label):
        max_w = label.winfo_width()
        max_h = label.winfo_height()
        if max_w < 50 or max_h < 50: max_w, max_h = 400, 400
        
        h, w = cv_image.shape[:2]
        scale = min(max_w / w, max_h / h)
        if scale < 1:
            resized_img = cv2.resize(cv_image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        else:
            resized_img = cv_image

        img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        tk_img = ImageTk.PhotoImage(pil_img)
        
        label.config(image=tk_img, text="")
        label.image = tk_img

if __name__ == '__main__':
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.geometry("1000x600")
    root.mainloop()