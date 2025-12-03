class Region:
    def __init__(self, dims):
        self.dims = dims
        self.group = []
        self.avg = ()
    
    def avg_det(self, convu):
        avg_r, avg_g, avg_b = 0, 0, 0
        for pos in self.group:
            avg_r += int(convu[pos[0]][pos[1]][0])
            avg_g += int(convu[pos[0]][pos[1]][1])
            avg_b += int(convu[pos[0]][pos[1]][2])
        avg_r /= len(self.group)
        avg_g /= len(self.group)
        avg_b /= len(self.group)
        self.avg = (avg_r, avg_g, avg_b)


    def avg_clrs(groups: list["Region"], convu) -> list[tuple]:
        if groups == []:
            return []
        for rg in groups:
            rg.avg_det(convu)
        return groups