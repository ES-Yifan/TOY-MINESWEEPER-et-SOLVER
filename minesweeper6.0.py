import random, copy, time
matrix = lambda h,w,var=0: [[var]*w for i in range(h)]


def displayer(map_, entry_width=3, replacement=dict()):
    h,w = len(map_), len(map_[0])
    print("  \\x", end=" ")
    for n in range(w):
        print(f"{n:>{entry_width}}", end="")
    print("\n  y\\", "-"*(w*4))
    for i in range(h):
        row = map_[i]
        print(f"{i:>3}| ", end="")
        for entry in row:
            if type(entry) == float:
                to_be_printed = f"{entry:.2f}"[:4]
            else:
                to_be_printed = f"{entry}"[:4]
            for i, j in replacement.items():
                to_be_printed = to_be_printed.replace(i,j)
            print(f"{to_be_printed:>{entry_width}}", end="")
        print()


""" (0,0) ---w, j---  x
        |
    h, i|
        |

        y
"""


######## Minesweeper Scetion #########
class Minesweeper:
    def __init__(self, map_size="9*9", bomb_num=10):
        
        self.h, self.w = map(int,map_size.split("*"))
        self.bomb_num = bomb_num
        h, w = self.h, self.w
        if h * w - bomb_num < 0:
            raise ValueError
        bombs_seq = [1]*bomb_num + [0]*(h * w - bomb_num)
        random.shuffle(bombs_seq)
        
        #private attribute: distribution of bombs (cannot be obtained from outside)
        self.__bombs_map = [bombs_seq[w * n: w * (n+1)] for n in range(h)]
        
        #displayer(self.__bombs_map, replacement={"0":""})  #this step is only for confirmation****

        values_map = matrix(h,w,0)
        for n in range(h):
            for m in range(w):
                for i in range(max(n-1, 0), min(n+2, h)):
                    for j in range(max(m-1, 0), min(m+2, w)):
                        if self.__bombs_map[i][j] == 1:
                            values_map[n][m] += 1
                        else:
                            continue
        
        #private attribute: distribution of numbered blocks and their value (cannot be obtained from outside)
        self.__values_map = values_map

        self.masks_map = matrix(h,w,"?")
        
        self.clear=False
        self.in_game = False

    def start_game(self):
        self.in_game = True

    def click(self, x, y, reported=True, shown=True):
        "when user clicks on a block check if it s a bomb"
        if self.__bombs_map[y][x] == 1:
            #clicked on a bomb
            self.masks_map[y][x] = "##" 
            self.in_game = self.clear = False
            if reported:
                print("failed")
            if shown:
                print("the mines are",*self.__bombs_map,sep="\n")
            pass
        
        else:
            self.uncover(x ,y, first_click=True)
            self.judge()

    def uncover(self, x, y, first_click=False):
        "uncover the given block and those surrounding it"
    
        self.masks_map[y][x] = self.__values_map[y][x]
        
        #uncover the blocks nearby

        if self.__values_map[y][x] == 0:
            for i in range(max(y-1, 0), min(y+2, self.h)):
                for j in range(max(x-1, 0), min(x+2, self.w)):
                    if self.masks_map[i][j] == "?":
                        self.uncover(j,i)  #recursion

        elif first_click:  
            #when the user clicks on a >0 valued block, the 0's near it will be uncovered; while when a >0 block is uncovered by recursion, no more recursion is allowed
            for i in range(max(y-1, 0), min(y+2, self.h)):
                for j in range(max(x-1, 0), min(x+2, self.w)):
                    if self.__values_map[i][j] == 0 and self.masks_map[i][j] == "?":
                        self.uncover(j,i)  #recursion

    def display(self):
        "display the current masks_map"
        displayer(self.masks_map, replacement={"0":"","?":"??"})

    def judge(self):
        "judge if the game is passed"
        if sum([row.count("?") for row in self.masks_map]) == self.bomb_num:
            self.in_game == False
            self.clear = True
            print("clear")

    def output(self):
        "output the masks_map as a copy"
        mapcopy = copy.deepcopy(self.masks_map)
        return mapcopy


######## Minesweepe Solver Section

#with "?" = undiscovered block, "M" = "known mine", "W" = beyond the wall, "N" = no mine for sure

def slicing_25(masks_map, x, y):
    "finding a 5*5 slice surrounding the given coordinates from the masks_map matrix"
    chunk = matrix(5,5,"W")
    h = len(masks_map); w = len(masks_map[0])
    for i in range(max(y-2, 0), min(y+3, h)):
        for j in range(max(x-2, 0), min(x+3, w)):
            chunk[i-y+2][j-x+2] = masks_map[i][j]
    return chunk

def find_probability(slice_25,mode):
    #initial values
    summed = 0
    default_product = product = 1
    valid_numbers = 0  #how many numbered blocks there are
    for i in range(1,4):
        for j in range(1,4):

            if slice_25[i][j] in ("W", "?", "M", 'N'):
                continue  #non-numbered blocks excluded

            valid_numbers +=1
            total_undiscovered = 0
            undiscovered_mines = int(slice_25[i][j])

            for n in range(i-1,i+2):
                for m in range(j-1, j+2):   #cycle for the blocks neighbouring the chosen numbered block
                    total_undiscovered += 1 if slice_25[n][m] == "?" else 0 #increase the dedominator
                    undiscovered_mines -= 1 if slice_25[n][m] == "M" else 0 #decrease the total number of unpositioned mines
                    #numbered blocks and walls are already discovered, and dont affect the denominator.

            probability_weight = undiscovered_mines/total_undiscovered \
                if undiscovered_mines!=0 else 0.0 #to catch the situation of 0/0
            
            if probability_weight == 0 or probability_weight == 1:
                return probability_weight
            else:
                summed += probability_weight
                product *= 1-probability_weight  #geometrical average
                default_product *=probability_weight


    if valid_numbers == 0:
        return float("nan")
    elif mode == "ari":
        return summed/valid_numbers
    elif mode == 'geo':
        return 1 - product**(1/valid_numbers) 
    elif mode == "dgm":
        return default_product**(1/valid_numbers)
    elif mode == "rdm":
        return 0.5
        

def minesweeper_solver(masks_map, bomb_num,displayed=False, output=False, mode="ari"):
    h = len(masks_map); w = len(masks_map[0])
    probabilities = matrix(h, w, 2.0) #let the default prob=2, so the prob for already-uncovered blocks = 2, to avoid auto_decider opening them
    known_mine_num = 0
    undeteremined_block_num = 0
    nan_position = (-1,-1)

    for y in range(len(masks_map)):
        for x in range(len(masks_map[0])):
            match masks_map[y][x]:
                case "?":
                    probability= find_probability(slicing_25(masks_map, x, y),mode=mode)

                case "M":
                    probability = 1.0
            
                case "N":
                    probability = 0.0

                case _: #numbered block
                    continue
            

            if probability == 1.0:
                masks_map[y][x] = "M"
                known_mine_num += 1
            elif probability == 0.0:
                masks_map[y][x] = "N"
            elif str(probability) == "nan":
                undeteremined_block_num += 1
                nan_position = (x,y)
            else:
                known_mine_num += probability 
                

            probabilities[y][x] = probability
            
            
    estimation_of_nan = min(1,(bomb_num-known_mine_num)/undeteremined_block_num) \
          if undeteremined_block_num !=0 and bomb_num > known_mine_num\
              else 0.0

    if displayed:
        displayer(probabilities, entry_width=4, replacement={"1.00":"M", "0.":".","2.00":"-"})
        print("estimation of nan is\n", round(estimation_of_nan,3),("+ misfortune factor" if estimation_of_nan !=0 else ""))
    
    if output:
        return probabilities, estimation_of_nan, nan_position

#---------main------------

#all functions outside the Class "Minesweeper" are PROHIBITED from calling the __bombs_map and __values_map attributes


auto_solve = True

#initialise the map



def auto_decider(probabilities, nan_probabilities, nan_position, ratio = 3 ):
    h = len(probabilities)
    min_probabilities = [1]*h
    x_positions_min = [0]*h
    for i in range(h):
        if 0.0 in probabilities[i]:
            return (probabilities[i].index(0.0),i)
        valid_blocks = list(filter(lambda x: str(x) != "nan", probabilities[i]))
        if valid_blocks != []:
            min_probabilities[i]=min(valid_blocks)
            x_positions_min[i] = probabilities[i].index(min_probabilities[i])
    
    min_probability = min(min_probabilities)
    if min_probability <= ratio* nan_probability or nan_position == (-1,-1):
        y_position_min = min_probabilities.index(min_probability)
        x_position_min = x_positions_min[y_position_min]
        return (x_position_min,y_position_min)
    else:
        return nan_position

        

if auto_solve:
    clear_n = 0
    max_repeat= 1
    for repeat_n in range(max_repeat):
        layout = "16*16"; bomb_num=35
        map1 = Minesweeper(layout, bomb_num)

        while map1.in_game == False:
            #print("\n\n\n")
            map1 = Minesweeper(layout, bomb_num)
            map1.start_game() 
            map1.click(int(map1.w/2),int(map1.h/2),reported=False, shown=False)
        print("start game")
        while map1.in_game==True and map1.clear==False:
        

            print("\n")
            map1.display()
            masks_map = map1.output() #redefine the masks_map, for the new step

            minesweeper_solver(masks_map,bomb_num) #1st iteration, with masks_map altered globally
            #print("\nsolver's suggestion (in coordinates):")
            minesweeper_solver(masks_map,bomb_num)
            probabilities, nan_probability, nan_position = minesweeper_solver(masks_map,bomb_num, mode="ari", displayed=False, output=True) #2nd iteration, to improve accuracy
            click_coordinates = auto_decider(probabilities, nan_probability, nan_position, ratio = 3)
            #print(click_coordinates)
            map1.click(*click_coordinates, shown=False)

            time.sleep(0.5)
        map1.display()
        if map1.clear == True:
            clear_n += 1
    print(clear_n,"/",max_repeat)

    


else:

    while True:
        try:
            layout = input("choose layout   ")
            bomb_num = int(input("choose the number of bombs   "))
            
            
            map1 = Minesweeper(layout, bomb_num)

            
            break
        except:
            continue







    print()
    print()
    map1.start_game()
    print("start game")


    map1.display()
    masks_map = map1.output()



    while True:
        try:
            map1.click(*map(int,input("click on x,y: \n").split(",")))
            break
        except ValueError:
            continue

    while map1.in_game==True and map1.clear==False:
        
        print()
        print()
        map1.display()
        masks_map = map1.output() #redefine the masks_map, for the new step

        minesweeper_solver(masks_map,bomb_num) #1st iteration, with masks_map altered globally
        print("\nsolver's suggestion (in probabilities):")
        minesweeper_solver(masks_map,bomb_num, displayed=True) #2nd iteration, to improve accuracy
        #aid the use by showing the prob distr


        #wait for user's input
        while True:
            try:
                map1.click(*map(int,input("click on x,y: \n").split(",")))
                break
            except Exception:
                continue