from PIL import Image
import os

# Создаем папку icons если её нет
icons_dir = "icons"
if not os.path.exists(icons_dir):
    os.makedirs(icons_dir)

# Открываем изображение
img = Image.open("pic.jpg")

# Размеры иконок
sizes = [16, 48, 128]

# Конвертируем в PNG нужных размеров
for size in sizes:
    resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
    output_file = os.path.join(icons_dir, f"icon{size}.png")
    # Конвертируем в RGBA если нужно
    if resized_img.mode != 'RGBA':
        resized_img = resized_img.convert('RGBA')
    resized_img.save(output_file, "PNG")

print("Icons created successfully!")
