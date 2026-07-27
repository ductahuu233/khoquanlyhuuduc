from PIL import Image

def remove_white_background(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # Check if pixel is white or near-white background
        r, g, b, a = item
        if r > 235 and g > 235 and b > 235:
            new_data.append((255, 255, 255, 0)) # Fully transparent
        else:
            new_data.append((r, g, b, a))

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Successfully processed image and saved transparent PNG to {output_path}")

if __name__ == "__main__":
    remove_white_background("static/logo.png", "static/logo.png")
