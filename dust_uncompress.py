import json
from PIL import Image, ImageDraw, ImageTk

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

    def draw_texture(self):
        buffer_index = 0
        error_margin = 20

        # create image with extra padding until algorithm is solved
        self.img = Image.new('RGB', (
            self.width + error_margin, 
            self.height+error_margin
        ), color='cyan')
        draw = ImageDraw.Draw(self.img)

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

            debug_scanline = []   # DEBUG: list for printing values in scanline
            # draw pixels
            for _ in range(scanline_count):
                byte = self.data[buffer_index]

                # fix color lookup ... either the clut is not being produced correctly
                # or this is part of the algorithm
                fixed_color_index = (byte+1)%255

                # DEBUG: add fixed color index to list, can be replaced with "byte"
                debug_scanline.append(fixed_color_index)

                # format color as triplet
                color = (
                    self.clut[fixed_color_index][0],
                    self.clut[fixed_color_index][1],
                    self.clut[fixed_color_index][2],
                )

                # draw pixel
                if fixed_color_index > 128: # swallow bytes under 128
                    self.img.putpixel((x+horizontal_offset,y), color)

                    x += 1

                # move to next index of self.data
                buffer_index += 1
            
            # move scanline down 1
            y += 1

            print(debug_scanline)

        self.img.show()
        self.img.save(".png")

def main():

    texture = dust_texture("Textures/apple")
    texture.draw_texture()

if __name__ == "__main__":
    main()