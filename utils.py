from PIL import Image, ImageTk, UnidentifiedImageError
import pathlib as pl
import os
import tkinter as tk
from tkinter import filedialog
import ctypes as ct

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
        checks if file exists

        :return true if yes, false else
        """
        try:
            file = Image.open(self.__name)
        except UnidentifiedImageError:
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
        img = Image.open(self.__name)
        self.__pixels = [ [0 for i in range(self.__size[1])] for j in range(self.__size[0]) ]
        for x in range(self.__size[0]):
            for y in range(self.__size[1]):
                pix = img.getpixel((x, y))
                self.__pixels[x][y] = (pix[0] + pix[1] + pix[2]) / 3
            
class Folder:
    def __init__(self, path: str | None = None) -> None:
        self.__path = path
        self.__content = []
        self.__images = []
    
    def ret_content(self):
        return self.__content
    
    def ret_images(self):
        return self.__images
    
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
        for i in self.__content:
            f = File( (self.__path if self.__path != None else "") + "/" + i)
            if f.is_image():
                self.__images.append(f)

    def check_by_pix(self, ind: int) -> list[int]:
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
    
    def gndc(self, data1: File, data2: File) -> tuple[int, int, int, int, 1|2, 1|2]:
        """
        determines the size of kernels for convolution
        :returns a tuple
        :last two elements of tuple are which image is the bigger in x and y respectively. 

        check up for an existing image given as argument needed to be done before.
        see documentation for more info. 
        """
        data1.size_get()
        data2.size_get()
        size1 = data1.ret_size()
        size2 = data2.ret_size()
        divx = max(size1[0], size2[0]) // min(size1[0], size2[0])
        rx = max(size1[0], size2[0]) % min(size1[0], size2[0])
        divy = max(size1[1], size2[1]) // min(size1[1], size2[1])
        ry = max(size1[1], size2[1]) % min(size1[1], size2[1])
        return (divx, divy, rx, ry, 1 if max(size1[0], size2[0]) == size1[0] else 2, 1 if max(size1[1], size2[1]) == size1[1] else 2)

    def sum_of_t(self, t1, t2):
        return (t1[0] + t2[0], t1[1] + t2[1], t1[2] + t2[2])

    def convolution(self, prop: tuple[int, int, int, int, int, int], img1: File):
        """
        prop structure:
        :0 -> size of kernel in x
        :1 -> size of kernel in y
        :2 -> rest of pixels to dispatch in x
        :3 -> rest of pixels to dispatch in y
        :4 -> number of kernel by ligne (x)
        :5 -> number of kernel by column (y)

        returns a dim2 list of kernels. determines the amount of kernel to do according
        to the gndc. takes into account the rest of pixel that couldn't fit in the kernels. 
        makes the first kernels slightly bigger for this matter. 
        Calculations for which dimensions to use for kernel list to do apart. 
        assumes the image given needs to add the rest that couldn't fit as part
        of the kernels as the correct one. if the image used is the smaller of the duo,
        don't forget to mark both x/y rests are 0. 

        see documentation for more info. 
        """
        img1.pixel_list()
        tabpix1 = img1.ret_pixels()
        conv = [[] for i in range(0, prop[5], prop[1])]
        compx, compy = 0, 0
        for i in range(0, prop[5], prop[1]):
            for j in range(0, prop[4], prop[0]):
                group = 0
                if i + prop[1] - 1 + (1 if prop[3] != compy else 0) < img1.ret_size()[1] and i + prop[0] - 1 + (1 if prop[2] != compx else 0) < img1.ret_size()[0]:
                    for k in range(prop[1] + (1 if prop[3] != compy else 0)):
                        for l in range(prop[0] + (1 if prop[2] != compx else 0)):
                            group += tabpix1[i + k][j + l]
                    conv[i // prop[1]].append(round(group, 2))
                    compx += 1
                    compy += 1
        return conv

    def reduce_im(self):
        self.__images.pop(0)

class UI:
    def __init__(self):
        self.wind = None
        self.action_id = None
    
    def is_dup(self, id):
        self.wind.destroy()
        if id:
            self.action_id = 1
        else:
            self.action_id = 0

    def start_menu(self) -> str:
        start_menu = tk.Tk()
        start_menu.geometry("300x100")
        start_menu.title("Select Directory")
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
    
    def run(self):
        dups = []
        self.folder.get_content()
        self.folder.det_images()
        if self.folder.ret_images() == []:
            exit()
        images = self.folder.ret_images()
        compt = 0
        ref = len(images)
        while compt != ref:
            for i in range(0, len(images)):
                if i != compt:
                    if self.folder.convolution(images[compt], images[i]):
                        dups.append(images[i])
            compt += 1
            self.folder.reduce_im()
            for j in dups:
                self.ui.comp_wind(images[compt].ret_name(), dups[j].ret_name())
                if self.ui.action_id == 1:
                    None
                else:
                    None

