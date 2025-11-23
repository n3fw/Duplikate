from PIL import Image, ImageTk, UnidentifiedImageError
import pathlib as pl
import os
import tkinter as tk
from tkinter import filedialog
import ctypes as ct
from math import log2, ceil, dist
import numpy as np
import region

class File:
    def __init__(self, name: str) -> None:
        self.__name = name
        self.__size = (0,0)
        self.__ext = {1:'.jpeg', 2:'.jpg', 3:'.png', 4:'.gif', 5:'.ico', 6:'.bmp', 7:'.psd'}
        self.__pixels = []
    
    def ret_name(self):
        return self.__name
    
    def ret_pixels(self):
        return self.__pixels
    
    def ret_size(self):
        return self.__size
    
    def exists(self) -> bool:
        """
        checks if file exists \n
        supported error in case of not existing : \n
        FileNotFoundError, FileExistsError, UnidentifiedImageError

        :return true if yes, false else
        """
        try:
            file = Image.open(self.__name)
        except FileNotFoundError or FileExistsError or UnidentifiedImageError:
            return False
        return True
    
    def size_get(self) -> None:
        """
        changes self.size to the size of the image
        """
        img = Image.open(self.__name)
        self.__size = img.size
    
    def is_image(self) -> bool:
        """
        dtermines if a file is an image by its extension
        """
        res: bool = False
        extension = pl.Path(self.__name).suffix
        for i in range(1, 8):
            if self.__ext.get(i) == extension:
                res = True
                break
        return res

    def pixel_list(self) -> None:
        """
        changes self.__pixels to the list of average RGB byte value of every pixel in the image
        """
        self.size_get()
        img = Image.open(self.__name)
        self.__pixels = [ [0 for i in range(self.__size[1])] for j in range(self.__size[0]) ]
        for x in range(self.__size[0]):
            for y in range(self.__size[1]):
                pix = img.getpixel((x, y))
                self.__pixels[x][y] = pix
            
class Folder:
    def __init__(self, path: str | None = None) -> None:
        self.__path = path
        self.__content = []
        self.__images = []
    
    def ret_content(self):
        return self.__content
    
    def ret_images(self):
        return self.__images
    
    def ret_path(self):
        return self.__path
    
    def get_content(self) -> None:
        """
        gets all files in the specified directory
        """
        try:    
            self.__content = os.listdir(self.__path)
        except FileNotFoundError:
            ct.windll.user32.MessageBoxW(0, "No directory specified !", "Error", 0)
        else:
            self.__content = os.listdir(self.__path)
    
    def det_images(self):
        """
        uses self.__content to determine self.__images 

        :returns nothing, modifies self.__images
        """
        for i in self.__content:
            f = File( (self.__path if self.__path != None else "") + "/" + i)
            if f.is_image():
                self.__images.append(f)

    def check_by_pix(self, ind: int) -> list[int]:
        """
        unused method for checking same images 

        :returns a list of duplicate images (not optimized)
        """
        duplicates = []
        im_data = self.__images[ind]
        im_data.size_get()
        im_data.pixel_list()
        pix = im_data.ret_pixels()
        for i in range(1, len(self.__images)):
            im_data2 = self.__images[i]
            im_data2.size_get()
            if im_data.ret_size() == im_data2.ret_size(): 
                im_data2.pixel_list()
                pix2 = im_data2.ret_pixels()
                if pix == pix2:
                    print("image", i, "is a duplicate")
                    duplicates.append(im_data2)
                else:
                    print("image", i, "is not a duplicate")
        return duplicates

    def sum_of_t(self, t1, t2):
        return (t1[0] + t2[0], t1[1] + t2[1], t1[2] + t2[2])

    def convolution(self, img1: File, buffer: int):
        """
        Creates a list of kernels by downsampling the image.
        Each kernel represents a BufferxBuffer block (Buffer² pixels).
        """
        img1.pixel_list()
        tabpix = img1.ret_pixels()
        w, h = img1.ret_size()

        # step = buffer because we group Buffer×Buffer pixels
        conv = [[] for _ in range(0, h, buffer)]

        for i in range(0, h, buffer):
            for j in range(0, w, buffer):

                ker_r = 0
                ker_g = 0
                ker_b = 0
                nbpi = 0

                # iterate through Buffer×Buffer block (Buffer² pixels)
                for di in range(buffer):
                    for dj in range(buffer):
                        y = i + di
                        x = j + dj

                        if y < h and x < w:
                            r, g, b = tabpix[x][y]  # pixel format expected: (r,g,b)

                            ker_r += int(r)
                            ker_g += int(g)
                            ker_b += int(b)
                            nbpi += 1

                # normalize if we collected any pixel
                if nbpi > 0:
                    ker = (ker_r / nbpi, ker_g / nbpi, ker_b / nbpi)
                    conv[i // buffer].append(ker)

        return conv


    def reduce_im(self):
        self.__images.pop(0)
    
    def accurate_find(self, conv1: list, conv2: list, img1: File, img2: File):
        """
        determines if two images are the same or not  \n
        two cases -> same size or different sizes
        (approximated accuracy : 98.98% / set accuracy : 95% (can be changed))

        :returns true if detected same, false else
        """
        res: bool = False
        if (img1.ret_size() == img2.ret_size()):
            dif0, dif1, dif2 = 0, 0, 0
            for i in range (len(conv1)):
                for j in range (len(conv1[i])):
                    if (conv1[i][j][0] == 0 and conv2[i][j][0] != 0) or (conv1[i][j][0] != 0 and conv2[i][j][0] == 0):
                        dif0 += 1
                    elif conv1[i][j][0] == conv2[i][j][0]:
                        pass
                    else:
                        dif0 += abs(conv2[i][j][0] - conv1[i][j][0]) / conv1[i][j][0]

                    if (conv1[i][j][1] == 0 and conv2[i][j][1] != 0) or (conv1[i][j][1] != 0 and conv2[i][j][1] == 0):
                        dif1 +=1
                    elif  conv1[i][j][1] == conv2[i][j][1]:
                        pass
                    else:
                        dif1 += abs(conv2[i][j][1] - conv1[i][j][1]) / conv1[i][j][1]

                    if (conv1[i][j][2] == 0 and conv2[i][j][2] != 0) or (conv1[i][j][2] != 0 and conv2[i][j][2] == 0):
                        dif2 += 1
                    elif  conv1[i][j][2] == conv2[i][j][2]:
                        pass
                    else:
                        dif2 += abs(conv2[i][j][2] - conv1[i][j][2]) / conv1[i][j][2]

            dif0 = (dif0 / ( len(conv1) * len(conv1[0]) ) ) * 100
            dif1 = (dif1 / ( len(conv1) * len(conv1[0]) ) ) * 100
            dif2 = (dif2 / ( len(conv1) * len(conv1[0]) ) ) * 100
            if dif0 < 5.0 and dif1 < 5.0 and dif2 < 5.0:
                res = True
        else:    
            r1, g1, b1, r2, g2, b2 = 0, 0, 0, 0, 0, 0
            for i in range(0, len(conv1)):
                for j in range(0, len(conv1[i])):
                    r1 += conv1[i][j][0]
                    g1 += conv1[i][j][1]
                    b1 += conv1[i][j][2]
            r1 = r1 / (len(conv1) * len(conv1[0]))
            g1 = g1 / (len(conv1) * len(conv1[0]))
            b1 = b1 / (len(conv1) * len(conv1[0]))
            for i in range(0, len(conv2)):
                for j in range(len(conv2[i])):
                    r2 += conv2[i][j][0]
                    g2 += conv2[i][j][1]
                    b2 += conv2[i][j][2]
            r2 = r2 / (len(conv2) * len(conv2[0]))
            g2 = g2 / (len(conv2) * len(conv2[0]))
            b2 = b2 / (len(conv2) * len(conv2[0]))
            difR, difB, difG = (r2 - r1)/r1*100, (b2 - b1)/b1*100, (g2 - g1)/g1*100
            if -5.0 < difR < 5.0 and -5.0 < difB < 5.0 and -5.0 < difG < 5.0:
                res = True
        return res

class UI:
    def __init__(self):
        self.wind = None
        self.action_id = None

    def find_logo(self) -> str:
        """
        find logo if present, else logo is base tk
        """
        try:
            os.open("resources/main_logo.ico", os.O_RDONLY)
        except FileNotFoundError:
            return None
        else:
            return "resources/main_logo.ico"
    
    def is_dup(self, id):
        self.wind.destroy()
        if id:
            self.action_id = 1
        else:
            self.action_id = 0

    def reset_id(self):
        self.action_id = None

    def start_menu(self) -> str:
        start_menu = tk.Tk()
        start_menu.geometry("300x100")
        start_menu.title("Select Directory")
        start_menu.iconbitmap(self.find_logo())
        path = tk.StringVar()
        ent1 = tk.Entry(start_menu, font=40, textvariable=path)
        ent1.pack(side = "top", anchor = "nw", padx = 10, pady = 10)

        def browsefunc():
            foldername = filedialog.askdirectory()
            ent1.insert(tk.END, foldername)

        browse_b = tk.Button(start_menu, text='Browse...', font = 40, command = browsefunc)
        browse_b.place_configure(relx = 0.7, rely = 0.09)

        save_button = tk.Button(start_menu, text = "Save", font = 40, command = start_menu.destroy)
        save_button.pack(side = "bottom", pady = 15)
        start_menu.mainloop()

        return path.get()

    def comp_wind(self, im1: str, im2: str):
        self.wind = tk.Tk()
        self.wind.geometry("1000x600")
        self.wind.title("Comparison Window")
        self.wind.iconbitmap(self.find_logo())

        img_data1 = Image.open(im1)
        prop1 = img_data1.size
        img_data1 = img_data1.resize( ( round(prop1[1] / (prop1[1]/400)), round(prop1[0] / (prop1[0]/400)) ) )
        item1 = ImageTk.PhotoImage(img_data1)
        ImLabel1 = tk.Label(self.wind, image = item1)

        img_data2 = Image.open(im2)
        prop2 = img_data2.size
        img_data2 = img_data2.resize( ( round(prop2[1] / (prop2[1]/400)), round(prop2[0] / (prop2[0]/400)) ) )
        item2 = ImageTk.PhotoImage(img_data2)
        ImLabel2 = tk.Label(self.wind, image = item2)

        ImLabel1.place_configure(relx = 0.05, rely = 0.05)
        ImLabel2.place_configure(relx = 0.55, rely = 0.05)

        button_conf = tk.Button(self.wind, text = "Yes", font = ("Arial", 20), command = lambda: self.is_dup(id = True))
        button_conf.place_configure(relx = 0.37, rely= 0.8)
        button_deny = tk.Button(self.wind, text = "No", font = ("Arial", 20), command = lambda: self.is_dup(id = False))
        button_deny.place_configure(relx = 0.6, rely = 0.8)
        self.wind.mainloop()

class RunApp:
    def __init__(self):
        self.ui = UI()
        self.folder = None
    
    def get_path(self):
        self.folder = Folder(self.ui.start_menu())
    
    def pixel_by_pixel(self):
        self.folder.get_content()
        self.folder.det_images()
        numb_im = len(self.folder.ret_images()) - 1
        while numb_im != 0:
            dups = self.folder.check_by_pix(0)
            for i in range(len(dups)):
                self.ui.comp_wind(self.folder.ret_images()[0].ret_name(), dups[i].ret_name())
                if self.ui.action_id == 1:
                    print("duplicate found")
                else:
                    print("not a duplicate")
            numb_im -= 1
            self.folder.reduce_im()
        
    def progression(self):
        """
        :returns an approximate number of operations to complete in order to work on a folder
        """
        return ceil(len(self.folder.ret_content()) * (log2( len(self.folder.ret_content()) ) - 1))

    def test_region(self):

        #just convolution of an image.
        self.folder = Folder("sample/")
        img = "bh.jpg"
        img_f = File(self.folder.ret_path() + img)
        arr = []
        for i in range(1):
            convu = self.folder.convolution(img1 = img_f, buffer = 16)
            convu = [row for row in convu if len(row) > 0]

            arr = np.array(convu, dtype=np.float32)
            arr = arr.astype(np.uint8)
            img_res = Image.fromarray(arr, mode = 'RGB')
            img_res.save("Test.png")
            img_f = File("Test.png")

        img_f.size_get()

        regions: list[region.Region] = []
        for i in range(len(arr)): 
            for j in range(len(arr[i])):
                verif = False
                for k in range(len(regions)):
                    if dist(arr[i][j], regions[k].avg) <= 50:
                        regions[k].group.append((i, j))
                        verif = True
                        break
                if not verif:
                    new_rg = region.Region(img_f.ret_size())
                    new_rg.group.append((i, j))
                    regions.append(new_rg)
                    regions = region.Region.avg_clrs(regions, arr)
        
        print(len(regions))
        colors = np.array([
        [255,   0,   0],   # rouge
        [  0, 255,   0],   # vert
        [  0,   0, 255],   # bleu
        [255, 255,   0],   # jaune
        [255,   0, 255],   # magenta
        [  0, 255, 255],   # cyan
        [255, 128,   0],   # orange
        [128,   0, 255],   # violet
        [  0, 128, 255],   # bleu clair
        [128, 255,   0],   # vert clair
        [255,   0, 128],   # rose
        [128,   0,   0],   # rouge foncé
        [  0, 128,   0],   # vert foncé
        [  0,   0, 128],   # bleu foncé
        [128, 128,   0],   # kaki
        [  0, 128, 128]    # turquoise foncé
        ], dtype=np.uint8)

        for i in range(len(regions)):
            for pix in regions[i].group:
                arr[pix[0]][pix[1]] = colors[i]
        
        img_res = Image.fromarray(arr, mode = 'RGB')
        img_res.save("Test_color.png")
    
    def run(self):
        self.get_path()
        self.folder.get_content()
        self.folder.det_images()
        total = self.progression()
        compt = 1
        if self.folder.ret_images() == []:
            ct.windll.user32.MessageBoxW(0, "No images found in the given folder !", "Error", 0)
            exit()
        images = self.folder.ret_images()
        while len(images) != 0:
            if images[0].exists():
                images[0].size_get()
                convu = self.folder.convolution(images[0])
                dups = []
                for i in range(1, len(images)):
                    print("treating comparison " + f"{compt}" + " out of " + f"{total}")
                    images[i].size_get()
                    if self.folder.accurate_find(conv1 = convu, conv2 = self.folder.convolution(images[i]), img1 = images[0], img2 = images[i]):
                        dups.append(images[i])
                    compt += 1

                if len(images) != 0:
                    for j in dups:
                        self.ui.comp_wind(images[0].ret_name(), j.ret_name())
                        if self.ui.action_id == 1:
                            os.remove(j.ret_name())
                            self.ui.reset_id()
            images.pop(0)

r = RunApp()
r.test_region()