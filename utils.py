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
        determines if a file is an image by its extension
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
        self.__path: str = path
        self.__content: list[str] = []
        self.__images: list[File] = []
    
    def ret_content(self):
        return self.__content
    
    def ret_images(self) -> list[File]: 
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
        if len(t1) == 2:
            return (t1[0] + t2[0], t1[1] + t2[1])
        elif len(t1) == 3:
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
                            r, g, b = tabpix[x][y][:3]  # pixel format expected: (r,g,b)

                            ker_r += int(r)
                            ker_g += int(g)
                            ker_b += int(b)
                            nbpi += 1

                # normalize if we collected any pixel
                if nbpi > 0:
                    ker = (ker_r / nbpi, ker_g / nbpi, ker_b / nbpi)
                    conv[i // buffer].append(ker)

        return conv
    
    def fast_find(self, conv1: list, conv2: list, img1: File, img2: File):
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
    
    def dist_center_regions(self, rg1: region.Region, rg2: region.Region):
        center1, center2 = (0, 0), (0, 0)
        for i in range ( len(rg1.group) if len(rg1.group) >= len(rg2.group) else len(rg2.group)):
            if i < len(rg1.group):
                center1 = self.sum_of_t(center1, rg1.group[i])
            if i < len(rg2.group):
                center2 = self.sum_of_t(center2, rg2.group[i])
        center1 = (center1[0] / len(center1), center1[1] / len(center1))
        center2 = (center2[0] / len(center2), center2[1] / len(center2))
        return dist(center1, center2)
    
    def accurate_find(self, rgs1: list[region.Region], rgs2: list[region.Region]):
        #penalty for the number of region behind different from one image to the other
        rgs_nbr_pen = abs(len(rgs1) - len(rgs2)) * -0.1

        # Couples making of regions
        nbr_comp = min(len(rgs1), len(rgs2))
        base = True if nbr_comp == len(rgs1) else False
        couples = []
        skip = []
        for i in range(nbr_comp):
            corres = 1000000
            ind = 0
            if base:
                for j in range(len(rgs2)):
                    if dist(rgs1[i].avg, rgs2[j].avg) < corres and rgs2[j] not in skip:
                        corres = dist(rgs1[i].avg, rgs2[j].avg)
                        ind = j
                couples.append((rgs1[i], rgs2[ind]))
                skip.append(rgs2[ind])
            else:
                for j in range(len(rgs1)):
                    if dist(rgs2[i].avg, rgs1[j].avg) < corres and rgs1[j] not in skip:
                        corres = dist(rgs2[i].avg, rgs1[j].avg)
                        ind = j
                couples.append((rgs2[i], rgs1[ind]))
                skip.append(rgs1[ind])
        
        #IoU determination
        def region_iou_normalized(rA: region.Region, rB: region.Region, resolution=256):
            g_norm1, g_norm2 = [(pix[0]/rA.dims[0], pix[1]/rA.dims[1]) for pix in rA.group], [(pix[0]/rB.dims[0], pix[1]/rB.dims[1]) for pix in rB.group]
            (x_max1, y_max1) = (max(pix[0] for pix in g_norm1), max(pix[1] for pix in g_norm1))
            (x_min1, y_min1) = (min(pix[0] for pix in g_norm1), min(pix[1] for pix in g_norm1))
            (x_max2, y_max2) = (max(pix[0] for pix in g_norm2), max(pix[1] for pix in g_norm2))
            (x_min2, y_min2) = (min(pix[0] for pix in g_norm2), min(pix[1] for pix in g_norm2))
            x_min_score = abs(x_min1 - x_min2)
            y_min_score = abs(y_min1 - y_min2)
            x_max_score = abs(x_max1 - x_max2)
            y_max_score = abs(y_max1 - y_max2)
            return x_min_score + x_max_score + y_min_score + y_max_score
        
        IoU_score = 0
        Centroid_score = 0
        r1, g1, b1, r2, g2, b2 = 0, 0, 0, 0, 0, 0
        dmax = (rgs1[0].dims[0]*rgs1[0].dims[0] + rgs1[0].dims[1]*rgs1[0].dims[1])**5 if base else (rgs2[0].dims[0]*rgs2[0].dims[0] + rgs2[0].dims[1]*rgs2[0].dims[1])**5
        for i in range(len(couples)):
            r1 += rgs1[i].avg[0] 
            g1 += rgs1[i].avg[1] 
            b1 += rgs1[i].avg[2]
            r2 += rgs2[i].avg[0] 
            g2 += rgs2[i].avg[1] 
            b2 += rgs2[i].avg[2] 
            IoU_score += region_iou_normalized(couples[i][0], couples[i][1])
            dist_center = self.dist_center_regions(couples[i][0], couples[i][1])
            if dist_center != 0.0:
                Centroid_score += 1 - min(dist_center/dmax, 1)

        Centroid_score /= len(rgs2) if base else len(rgs1)
        IoU_score /= nbr_comp 
        red_score, green_score, blue_score = abs(r1 - r2) / (100*len(couples)), abs(g1 - g2) / (100*len(couples)), abs(b1 - b2) / (100*len(couples))
        total = round((rgs_nbr_pen - Centroid_score - IoU_score - red_score - green_score - blue_score), 3)
        return total

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
        start_menu.geometry("800x400")
        start_menu.title("Select Directory")
        start_menu.iconbitmap(self.find_logo())

        start_menu.update_idletasks()
        x = (start_menu.winfo_screenwidth()//2)-400
        y = (start_menu.winfo_screenheight()//2)-200
        start_menu.geometry(f'{800}x{400}+{x}+{y}')

        title = tk.Label(start_menu, text = "Welcome to our image recognition program", font = ("Times New Roman", 20, "bold"))
        title.pack(pady=10)


        def browsefunc():
            foldername = filedialog.askdirectory()
            ent1.insert(tk.END, foldername)

        browseText = tk.Label(start_menu, text = "Click here to choose the images you want to compare :", font = ("Times New Roman", 12))
        browseText.pack(pady = 10)
        browse_b = tk.Button(start_menu, text='Browse...', font = ("Times New Roman", 10), command = browsefunc,
                             width = 10, height = 2)
        browse_b.pack(pady = 2)

        pathText = tk.Label(start_menu, text = "URL :", font = ("Times New Roman", 12))
        pathText.pack(pady = 2)
        path = tk.StringVar()
        ent1 = tk.Entry(start_menu, font=40, textvariable=path)
        ent1.pack(side="top", anchor="center", pady=2)

        saveText = tk.Label(start_menu, text="Click here to save the selected images and launch the research :", font=("Times New Roman", 12))
        saveText.pack(pady=10)
        save_button = tk.Button(start_menu, text = "Save", font = ("Times New Roman", 10), command = start_menu.destroy,
                                width = 10, height = 2)
        save_button.pack(pady = 2)
        start_menu.mainloop()

        return path.get()

    def comp_wind(self, im1: str, im2: str):
        self.wind = tk.Tk()
        self.wind.geometry("1000x600")
        self.wind.title("Comparison Window")
        self.wind.iconbitmap(self.find_logo())
        self.wind.update_idletasks()
        x = (self.wind.winfo_screenwidth() // 2) - 500
        y = (self.wind.winfo_screenheight() // 2) - 300
        self.wind.geometry(f'{1000}x{600}+{x}+{y}')


        img_data1 = Image.open(im1)
        prop1 = img_data1.size
        ratio1 = 250/prop1[1]
        width1 = int(prop1[0]*ratio1)
        img_data1 = img_data1.resize((width1, 250))
        item1 = ImageTk.PhotoImage(img_data1)
        ImLabel1 = tk.Label(self.wind, image = item1)

        img_data2 = Image.open(im2)
        prop2 = img_data2.size
        ratio2 = 250/prop2[1]
        width2 = int(prop2[0]*ratio2)
        img_data2 = img_data2.resize((width2, 250))
        item2 = ImageTk.PhotoImage(img_data2)
        ImLabel2 = tk.Label(self.wind, image = item2)

        ImLabel1.place_configure(relx = 0.25, rely = 0.15, anchor = "n")
        ImLabel2.place_configure(relx = 0.75, rely = 0.15, anchor = "n")

        buttonText = tk.Label(text = "These two images seem to be identical.", font = ("Times New Roman", 20))
        buttonText.pack(pady = 20)

        buttonText = tk.Label(text="Do you confirm this statement ? (Answer with either yes or no) ", font=("Times New Roman", 20))
        buttonText.place_configure(relx = 0.5, rely = 0.7, anchor = "center")

        button_conf = tk.Button(self.wind, text = "Yes", font = ("Times New Roman", 20), command = lambda: self.is_dup(id = True))
        button_conf.place_configure(relx = 0.45, rely= 0.8, anchor = "center")

        button_deny = tk.Button(self.wind, text = "No", font = ("Times New Roman", 20), command = lambda: self.is_dup(id = False))
        button_deny.place_configure(relx = 0.55, rely = 0.8, anchor = "center")

        self.wind.mainloop()

class RunApp:
    def __init__(self, mode):
        self.ui = UI()
        self.folder = None
        self.mode = mode
    
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
        return (len(self.folder.ret_images())-1)*len(self.folder.ret_images()) // 2

    def region_det(self, name_img) -> list[region.Region]:
        img_f = File(name_img)
        arr = []
        for i in range(1):
            convu = self.folder.convolution(img1 = img_f, buffer = 16)
            convu = [row for row in convu if len(row) > 0]

            arr = np.array(convu, dtype=np.float32)
            arr = arr.astype(np.uint8)
            img_res = Image.fromarray(arr, mode = 'RGB')
            img_res.save("temp/temp.png")
            img_f = File("temp/temp.png")

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
        
        img_res.close()
        os.remove("temp/temp.png")
        return regions

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

        if (self.mode == "F"):
            convs = [self.folder.convolution(im, 4) for im in images]
        else:
            regions = [self.region_det(im.ret_name()) for im in images]

        while len(images) != 0:
            if images[0].exists():
                dups = []
                dups_ind = []
                for i in range(1, len(images)):
                    print("treating comparison " + f"{compt}" + " out of a maximum of " + f"{total}")
                    if self.mode == "F" and self.folder.fast_find(conv1 = convs[0], conv2 = convs[i], img1 = images[0], img2 = images[i]):
                        dups.append(images[i])
                    if self.mode == "A":
                        score = self.folder.accurate_find(rgs1 = regions[0], rgs2 = regions[i])
                        if score > -1.0:
                            dups.append(images[i])
                            dups_ind.append(i)
                    compt += 1

                if len(dups) != 0:
                    for j in range(len(dups)):
                        self.ui.comp_wind(images[0].ret_name(), dups[j].ret_name())
                        if self.ui.action_id == 1:
                            os.remove(dups[j].ret_name())
                            images.pop(dups_ind[j])
                            regions.pop(dups_ind[j])
                            self.ui.reset_id()
            images.pop(0)
            regions.pop(0)