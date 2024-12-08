import sys
import ctypes

# -------------------------- register  setting--------------------------- #
def format_as_hex(n): 
    return f"{n & ((1 << 32) - 1):08x}"

def two_imm(imm_str): # 2진수 -> 정수
    if imm_str[0] == '0':
        return int(imm_str,2)
    elif imm_str[0] == '1':
        return int(imm_str,2) - (2**len(imm_str))

class Memory:
    def __init__(self, address, value):
        self.address = address
        self.value = value
        
    def set_value(self, value):
        self.value = value
    
    def get_value(self):
        return self.value
    
    def set_address(self, address):
        self.address = address
    
    def get_address(self):
        return self.address


class Register: 
    def __init__(self, name, address, value):
        self.address = address
        self.name = name
        
        if name == 0:  # x0의 경우 값이 항상 0이어야 함
            self.value = 0
        else:
            self.value = value
    
    def set_value(self, value):
        if self.name != 0:  # x0의 경우 값 변경이 불가능해야 함
            self.value = value
        else:
            self.value = 0
    
    def get_value(self):
        return self.value
    
    def set_address(self, address):
        self.address = address
    
    def get_address(self):
        return self.address
    
    def print_value(self):
        print(f"x{self.name}: 0x{format_as_hex(self.value)}")

register_list = []
memory_space = [] 
for i in range(32): # 레지스터 초기화 
    register = Register(name= i, address=i, value=0x00000000)  # address 값 변경 필요
    register_list.append(register)

for address in range(0x10000000, 0x10010000,4): # 메모리 초기화
    memory = Memory(address=address, value = -1)
    memory_space.append(memory)

memory_ascii = Memory(address = 0x20000000, value = 0)
memory_space.append(memory_ascii)

inst_list = [] # inst list 로 해석할 예정
inst_cnt = 0
bin_data = []

def decode_instruction(binary_str):
    
    opcode = binary_str[25:32]
    
    if opcode == "0110111":  # U-type (lui)
        imm = binary_str[0:20] + "000000000000"
        rd = binary_str[20:25]
        return f"lui x{int(rd,2)}, {two_imm(imm)}"
    elif opcode == "0010111":  # U-type (auipc)     
        imm = binary_str[0:20] + "000000000000"
        rd = binary_str[20:25]
        return f"auipc x{int(rd,2)}, {two_imm(imm)}"
    elif opcode == "1101111":  # UJ-type (jal)
        imm = binary_str[0] + binary_str[12:20] + binary_str[11] + binary_str[1:11] + "0"
        rd = binary_str[20:25]
        return f"jal x{int(rd,2)}, {two_imm(imm)}"
    elif opcode == "1100011":  # SB-type (beq, bne, blt, bge, bltu, bgeu)
        funct3=binary_str[17:20]
        rs1=binary_str[12:17]
        rs2=binary_str[7:12]
        imm = binary_str[0] + binary_str[24] +binary_str[1:7] + binary_str[20:24] + "0"
        if funct3 =="000":
            return f"beq x{int(rs1,2)}, x{int(rs2,2)}, {two_imm(imm)}"  #beq
        elif funct3 == "001":
            return f"bne x{int(rs1,2)}, x{int(rs2,2)}, {two_imm(imm)}"  #bne
        elif funct3 == "100":
            return f"blt x{int(rs1,2)}, x{int(rs2,2)}, {two_imm(imm)}"  #blt
        elif funct3 == "101":
            return f"bge x{int(rs1,2)}, x{int(rs2,2)}, {two_imm(imm)}"  #bge
        elif funct3 == "110":
            return f"bltu x{int(rs1,2)}, x{int(rs2,2)}, {two_imm(imm)}"  #bltu
        elif funct3 == "111":
            return f"bgeu x{int(rs1,2)}, x{int(rs2,2)}, {two_imm(imm)}"  #bgeu
    elif opcode == "0100011":  # S-type (sb, sh, sw)
        funct3 = binary_str[17:20]
        rs1 =binary_str[12:17]
        rs2 = binary_str[7:12]
        imm = binary_str[0:7] + binary_str[20:25]
        if funct3 == "000":
            return f"sb x{int(rs2,2)}, {two_imm(imm)}(x{int(rs1,2)})" #sb
        elif funct3 == "001":
            return f"sh x{int(rs2,2)}, {two_imm(imm)}(x{int(rs1,2)})" #sh
        elif funct3 == "010":
            return f"sw x{int(rs2,2)}, x{int(rs1,2)}, {two_imm(imm)}" #sw
    elif opcode == "1100111":  # I-type (jalr)
        imm = binary_str[0:12]
        rs1 = binary_str[12:17]
        rd = binary_str[20:25]
        return f"jalr x{int(rd,2)}, x{int(rs1,2)}, {two_imm(imm)}" #jalr x4 20(x3)
    elif opcode == "0000011":  # I-type (lb, lh, lw, lbu, lhu) #lw x9, -123(x20)
        funct3 = binary_str[17:20]
        imm = binary_str[0:12]
        rs1 = binary_str[12:17]
        rd = binary_str[20:25]
        if funct3 == "000":
            return f"lb x{int(rd,2)}, {two_imm(imm)}(x{int(rs1,2)})" #lb
        elif funct3 == "001":
            return f"lh x{int(rd,2)}, {two_imm(imm)}(x{int(rs1,2)})"  #lh
        elif funct3 == "010":
            return f"lw x{int(rd,2)}, x{int(rs1,2)}, {two_imm(imm)}" #lw
        elif funct3 == "100":
            return f"lbu x{int(rd,2)}, {two_imm(imm)}(x{int(rs1,2)})" #lbu
        elif funct3 == "101":
            return f"lhu x{int(rd,2)}, {two_imm(imm)}(x{int(rs1,2)})" #lhu
    elif opcode == "0010011":  # I-type (addi, slti, sltiu, xori, ori, andi, slli, srli, srai)
        funct3 = binary_str[17:20]
        funct7 = binary_str[0:7]
        rd = binary_str[20:25]
        rs1 = binary_str[12:17]
        imm = binary_str[0:12]
        shamt =binary_str[7:12]
        if funct3 == "000":
            return f"addi x{int(rd,2)}, x{int(rs1,2)}, {two_imm(imm)}"  # addi
        elif funct3 == "010":
            return f"slti x{int(rd,2)}, x{int(rs1,2)}, {two_imm(imm)}" # slti
        elif funct3 == "011":
            return f"sltiu x{int(rd,2)}, x{int(rs1,2)}, {two_imm(imm)}" # sltiu
        elif funct3 == "100":
            return f"xori x{int(rd,2)}, x{int(rs1,2)}, {two_imm(imm)}"  # xori
        elif funct3 == "110":
            return f"ori x{int(rd,2)}, x{int(rs1,2)}, {two_imm(imm)}"  # ori
        elif funct3 == "111":
            return f"andi x{int(rd,2)}, x{int(rs1,2)}, {two_imm(imm)}"  # andi
        elif funct3 == "001" and funct7 == "0000000":
            return f"slli x{int(rd,2)}, x{int(rs1,2)}, {int(shamt,2)}"  # slli
        elif funct3 == "101" and funct7 == "0000000":
            return f"srli x{int(rd,2)}, x{int(rs1,2)}, {int(shamt,2)}"  # srli
        elif funct3 == "101" and funct7 == "0100000":
            return f"srai x{int(rd,2)}, x{int(rs1,2)}, {int(shamt,2)}"  # srai
    elif opcode == "0110011":  # R-type (add, sub, sll, slt, sltu, xor, srl, sra, or, and)
        # ex -> add x0, x1, x2
        funct3 = binary_str[17:20]
        funct7 = binary_str[0:7]
        rd = binary_str[20:25]
        rs1=binary_str[12:17]
        rs2=binary_str[7:12]
        if funct3 == "000" and funct7 == "0000000":
            return f"add x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # add
        elif funct3 == "000" and funct7 == "0100000":
            return f"sub x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # sub
        elif funct3 == "001" and funct7 == "0000000":
            return f"sll x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # sll
        elif funct3 == "010" and funct7 == "0000000":
            return f"slt x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # slt
        elif funct3 == "011" and funct7 == "0000000":
            return f"sltu x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # sltu
        elif funct3 == "100" and funct7 == "0000000":
            return f"xor x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # xor
        elif funct3 == "101" and funct7 == "0000000":
            return f"srl x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # srl
        elif funct3 == "101" and funct7 == "0100000":
            return f"sra x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # sra
        elif funct3 == "110" and funct7 == "0000000":
            return f"or x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}"  # or
        elif funct3 == "111" and funct7 == "0000000":
            return f"and x{int(rd,2)}, x{int(rs1,2)}, x{int(rs2,2)}" # and

    return "unknown instruction"

# -------------------------- open file --------------------------- #
if len(sys.argv) > 4:
    sys.exit(1)

input_inst = sys.argv[1]
input_inst_num = 0
try:
    with open(input_inst, 'rb') as f:
        j = 0
        while True:
            chunk = f.read(4)
            if not chunk:
                break
            binary_str = bin(int.from_bytes(chunk, byteorder='little'))[2:].zfill(32)  # Convert binary to 32-bit string
            hex_str = hex(int(binary_str, 2))[2:].zfill(8)
            inst_list.append(f"{decode_instruction(binary_str)}")
            j += 1
except FileNotFoundError:
    print("File not found")

if len(sys.argv) == 3:
    input_inst_num = sys.argv[2]
    inst_cnt = int(input_inst_num)

elif len(sys.argv) == 4:
    input_inst_num = sys.argv[3]
    inst_cnt = int(input_inst_num)
    input_bin_data = sys.argv[2]
    try:
        with open(input_bin_data, 'rb') as f:
            while True:
                chunk = f.read(4)
                if not chunk:
                    break
                binary_str = bin(int.from_bytes(chunk, byteorder='little'))[2:].zfill(32)  # Convert binary to 32-bit string
                bin_data.append(f"{binary_str}")
    except FileNotFoundError:
        print("File not found")

# -------------------------- memory --------------------------- #
data_index = 0
for data_index in range(len(bin_data)):
    memory_space[data_index].set_value(two_imm(bin_data[data_index]))
        
# -------------------------- register --------------------------- #
temp_pc = 0
temp_cnt = 1

while(1):
    if len(inst_list) < temp_pc+1 or temp_cnt > inst_cnt :
        break
    temp_inst = inst_list[temp_pc].replace(',', '').split()
    
    if temp_inst[0] == 'add':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        register_list[rd].set_value(register_list[rs1].get_value() + register_list[rs2].get_value())
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'sub':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        register_list[rd].set_value(register_list[rs1].get_value() - register_list[rs2].get_value())
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'addi':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        register_list[rd].set_value(register_list[rs1].get_value() + imm)
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'lui':
        rd = int(temp_inst[1][1:])
        imm = int(temp_inst[2])
        register_list[rd].set_value(imm)
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'ori':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        register_list[rd].set_value(register_list[rs1].get_value() | imm)
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'xori':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        register_list[rd].set_value(register_list[rs1].get_value() ^ imm)
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'xor':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        register_list[rd].set_value(register_list[rs1].get_value() ^ register_list[rs2].get_value())
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'or':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        register_list[rd].set_value(register_list[rs1].get_value() | register_list[rs2].get_value())
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'and':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        register_list[rd].set_value(register_list[rs1].get_value() & register_list[rs2].get_value())
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'andi':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        register_list[rd].set_value(register_list[rs1].get_value() & imm)
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'slli':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        register_list[rd].set_value(register_list[rs1].get_value() << imm)
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'srli': 
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        register_list[rd].set_value(((register_list[rs1].get_value() & 0xFFFFFFFF) >> imm))
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'srai': 
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        register_list[rd].set_value((register_list[rs1].get_value() >> imm)) 
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1 
        
    elif temp_inst[0] == 'slti':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        value_rs1 = register_list[rs1].get_value()
        register_list[rd].set_value(1 if value_rs1 < imm else 0 )
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'slt':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        value_rs1 = register_list[rs1].get_value()
        value_rs2 = register_list[rs2].get_value()
        register_list[rd].set_value(1 if value_rs1 < value_rs2 else 0)
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'sll':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        register_list[rd].set_value(register_list[rs1].get_value() << (register_list[rs2].get_value() & 0b11111))
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'srl':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        register_list[rd].set_value((register_list[rs1].get_value() & 0xFFFFFFFF) >> (register_list[rs2].get_value() & 0b11111))
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'sra':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        rs2 = int(temp_inst[3][1:])
        register_list[rd].set_value(register_list[rs1].get_value() >> (register_list[rs2].get_value() & 0b11111))
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'auipc':
        rd = int(temp_inst[1][1:])
        imm = int(temp_inst[2])
        register_list[rd].set_value(imm + temp_pc*4) 
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'beq':
        rs1 = int(temp_inst[1][1:])
        rs2 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        if (register_list[rs1].get_value() == register_list[rs2].get_value()) :
            temp_pc = temp_pc + (int)(imm/4)
        else: 
            temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'bne':
        rs1 = int(temp_inst[1][1:])
        rs2 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        if (register_list[rs1].get_value() != register_list[rs2].get_value()) :
            temp_pc = temp_pc + (int)(imm/4)
        else: 
            temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'blt':
        rs1 = int(temp_inst[1][1:])
        rs2 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        value_rs1 = register_list[rs1].get_value()
        value_rs2 = register_list[rs2].get_value()
        if (value_rs1 < value_rs2) :
            temp_pc = temp_pc + (int)(imm/4)
        else: 
            temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'bge':
        rs1 = int(temp_inst[1][1:])
        rs2 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        value_rs1 = register_list[rs1].get_value()
        value_rs2 = register_list[rs2].get_value()
        if (value_rs1 >= value_rs2) :
            temp_pc = temp_pc + (int)(imm/4)
        else: 
            temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1

    elif temp_inst[0] == 'jal':
        rd = int(temp_inst[1][1:])
        imm = int(temp_inst[2])
        register_list[rd].set_value(4*temp_pc + 4)
        temp_pc = temp_pc + (int)(imm/4)
        temp_cnt = temp_cnt + 1
        
    elif temp_inst[0] == 'jalr':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        register_list[rd].set_value(4*(temp_pc+1))
        temp_pc = (int)((register_list[rs1].get_value() + imm)/4)
        temp_cnt = temp_cnt + 1
        
    elif temp_inst[0] == 'lw':
        rd = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        addr = register_list[rs1].get_value() + imm
        target_memory = None
        for memory in memory_space:
            if memory.get_address() == addr:
                target_memory = memory
                break
        if target_memory is not None:
             register_list[rd].set_value(target_memory.get_value())
        if target_memory.get_address() == 0x20000000 :
            num = int(input())
            register_list[rd].set_value(num)
            
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    elif temp_inst[0] == 'sw': 
        rs2 = int(temp_inst[1][1:])
        rs1 = int(temp_inst[2][1:])
        imm = int(temp_inst[3])
        addr = register_list[rs1].get_value() + imm
        target_memory = None
        for memory in memory_space:
            if memory.get_address() == addr:
                target_memory = memory
                break
        if target_memory is not None:
            target_memory.set_value(register_list[rs2].get_value())
        if target_memory.get_address() == 0x20000000 :
            print(chr(target_memory.get_value()),end='')
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
    else:
        temp_pc = temp_pc+1
        temp_cnt = temp_cnt+1
        
for register in register_list:
    register.print_value()