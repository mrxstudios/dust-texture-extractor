import json
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
import matplotlib.pyplot as plt
import math


def read_int16(buffer,index):
    if not index+1 > len(buffer):
        return int.from_bytes(buffer[index:index+1],byteorder="little")
    else:
        raise IndexError("Read Int16 index out of range.")

def init_argparser():
    pass

class dust_texture():
    def __init__(self, path):
        self.path = path
        self.clut = self.parse_clut()
        self.data = self.parse_data()
        self.original_img = self.parse_original_image()
        self.nudged_img = self.parse_nudged_image()

    def parse_clut(self):
        with open(self.path+"/clut.txt","r") as f:
            clut = json.loads(f.read())
        return clut

    def parse_data(self):
        with open(self.path+"/texture_binary","rb") as f:
            buffer = bytearray(f.read())

        # Read header values
        self.height = read_int16(buffer,0)
        self.width = read_int16(buffer,2)
        self.offset_y = read_int16(buffer,4)
        self.offset_x = read_int16(buffer,6)

        return buffer[8:]


    def parse_original_image(self):
        self.histo_orig = []
        try:
            img = Image.open(self.path+"/ingame_edited.png") 
            rgb_img = img.convert('RGB')

            width = img.width
            height = img.height


            for x in range(width):
                for y in range(height):
                    r, g, b = rgb_img.getpixel((x, y))
                    f = r+256*g+b*256**2
                    if f != 13693183:
                        self.histo_orig.append(f)

            return rgb_img
        
        except Exception:
            print("ingame_nudged.png not found or inaccessable")
            return None

    def parse_nudged_image(self):
        try:
            img = Image.open(self.path+"/ingame_nudged.png") 
            rgb_img = img.convert('RGB')

            return rgb_img

        except Exception:
            print("ingame_nudged.png not found or inaccessable")
            return None


    def img_to_color_histogram(self, img):
        width = img.width
        height = img.height

        histogram = []

        for x in range(width):
            for y in range(height):
                r, g, b = img.getpixel((x, y))
                histogram.append((r+256*g+b*256**2))

        return histogram

    def compare_histograms(self,histo1,histo2):
        count = 0
        q = set(histo2)
        for x in histo1:
            count += 1 if x in q else 0
        return count
        #len(set(histo1).intersection(set(histo2)))
        

    def draw_texture(self):
        buffer_index = 0
        error_margin = 20
        self.histo_new = []

        # create image with extra padding until algorithm is solved
        self.img = Image.new('RGB', (
            self.width + error_margin, 
            self.height+error_margin
        ), color='magenta')

        # draw size the image should be in magenta
        # draw.rectangle(((0,0), (self.width, self.height)), fill="magenta")

        x = 0
        y = 0
        # draw scanline
        while buffer_index < len(self.data):
            x = 0

            # read the amount of bytes in the current scanline
            scanline_count = read_int16(self.data,buffer_index)
            buffer_index += 2

            # offsets the pixels so they are drawn from the middle outwards
            # horizontal_offset = self.offset_x - int(scanline_count/2) + 1
            horizontal_offset = 0

            debug_scanline = []   # DEBUG: list for printing values in scanline
            # draw pixels
            for _ in range(scanline_count):
                byte = self.data[buffer_index]

                # fix color lookup ... either the clut is not being produced correctly
                # or this is part of the algorithm
                fixed_color_index = (byte+1)%256

                # DEBUG: add fixed color index to list, can be replaced with "byte"
                debug_scanline.append(fixed_color_index)

                # format color as triplet
                color = (
                    int(self.clut[fixed_color_index][0]),
                    int(self.clut[fixed_color_index][1]),
                    int(self.clut[fixed_color_index][2]),
                )

                # draw pixel
                # if fixed_color_index > 128: # swallow bytes under 128 (should be 4 for checkers)
                    # if fixed_color_index == 255:
                self.img.putpixel((x+horizontal_offset,y), color)
                self.histo_new.append(color[0]+256*color[1]+color[2]*256**2)

                x += 1

                # move to next index of self.data
                buffer_index += 1
            
            # move scanline down 1
            y += 1

            print(len(debug_scanline),self.width,debug_scanline)

        # self.img.show()
        # self.img.save(".png")
        plt.hist(self.histo_orig, label='orig')
        plt.hist(self.histo_new, label='interpret')
        plt.legend(loc='upper right')

    def draw_final_texture(self):
        buffer_index = 0
        error_margin = 20

        # create image with extra padding until algorithm is solved
        self.final_img = Image.new('RGB', (
            self.width, 
            self.height
        ), color='cyan')
        draw = ImageDraw.Draw(self.final_img)

        # draw size the image should be in magenta
        draw.rectangle(((0,0), (self.width, self.height)), fill="magenta")

        x = 0
        y = 0
        # draw scanline
        while buffer_index < len(self.data):
            x = 0

            # read the amount of bytes in the current scanline
            scanline_count = read_int16(self.data,buffer_index)
            buffer_index += 2

            # offsets the pixels so they are drawn from the middle outwards
            horizontal_offset = self.offset_x - int(scanline_count/2) + 1
            # horizontal_offset = 0

            # draw pixels
            for _ in range(scanline_count):
                byte = self.data[buffer_index]

                # fix color lookup ... either the clut is not being produced correctly
                # or this is part of the algorithm
                fixed_color_index = (byte+1)%256

                # format color as triplet
                color = (
                    int(self.clut[fixed_color_index][0]),
                    int(self.clut[fixed_color_index][1]),
                    int(self.clut[fixed_color_index][2]),
                )

                # draw pixel
                if fixed_color_index > 128: # swallow bytes under 128 (should be 4 for checkers)
                    # if fixed_color_index == 255:
                    self.final_img.putpixel((x+horizontal_offset,y), color)
                    x += 1

                # move to next index of self.data
                buffer_index += 1
            
            # move scanline down 1
            y += 1        

    def draw_comparison_image(self):
        error_margin = 20

        # create image with extra padding until algorithm is solved
        compare_img = Image.new('RGB', (
            self.width + error_margin, 
            self.height * 4 + error_margin
        ), color='cyan')

        for y in range(self.height):
            for x in range(self.width):
                # data
                r, g, b = self.img.getpixel((x, y))
                compare_img.putpixel((x,y*4+0), (r,g,b))
                # final
                r, g, b = self.final_img.getpixel((x, y))
                compare_img.putpixel((x,y*4+1), (r,g,b))
                # original
                r, g, b = self.nudged_img.getpixel((x, y))
                compare_img.putpixel((x,y*4+2), (r,g,b))
        compare_img.show()
        compare_img.save("compare.png")

    def compare_color_count(self,image1,image2):
        image1_colors = []
        for y in range(image1.height):
            colors_in_scanline = []
            for x in range(image1.width):
                r, g, b = image1.getpixel((x, y))
                f = r+256*g+b*256**2
                colors_in_scanline.append(f)
            print(set(colors_in_scanline))
            image1_colors.append(len(set(colors_in_scanline)))
            
            
        
        image2_colors = []
        for y in range(image2.height):
            colors_in_scanline = []
            for x in range(image2.width):
                r, g, b = image2.getpixel((x, y))
                f = r+256*g+b*256**2
                colors_in_scanline.append(f)
            image2_colors.append(len(set(colors_in_scanline)))
        
        for s in range(len(image1_colors)):
            print(str(s)+":",image1_colors[s],image2_colors[s])


def main():
    texture = dust_texture("Textures/apple")
    print("width:",texture.width)
    print("height:",texture.height)
    texture.draw_texture()
    texture.draw_final_texture()
    # texture.draw_comparison_image()
    texture.final_img.show()
    # texture.compare_color_count(texture.final_img,texture.original_img)


if __name__ == "__main__":
    main()