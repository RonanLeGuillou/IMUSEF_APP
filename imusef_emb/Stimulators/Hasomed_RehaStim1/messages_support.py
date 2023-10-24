#!/usr/bin/python
# Filename: messages_support.py

import binascii
# import struct

safety_limit = 90

version = '0.1'

get_bin = lambda x, n: x >= 0 and str(bin(x))[2:].zfill(n) or "-" + str(bin(x))[3:].zfill(n)

#type of command
CHANNEL_INIT = 0
CHANNEL_UPDATE = 1
CHANNEL_STOP = 2
SINGLE_PULSE = 3

def generate_single_pulse(_channel_number,_pulse_width,_pulse_current):
    global safety_limit
    ident = SINGLE_PULSE
    channel_number = _channel_number-1
    pulse_width = _pulse_width
    if (_pulse_current < safety_limit):
        pulse_current = _pulse_current
    else:
        print("SAFETY LIMIT (of " + str(safety_limit) + " EXCEEDED. Request of " + str(_pulse_current) + "dropped to limit")
        pulse_current = safety_limit  
    checksum = (channel_number + pulse_width + pulse_current) % 32
    #print("checksum verify = " + str(checksum))

    #print("binary command: \n" + 
    #"\t" + get_bin(ident,2) +  "\t\t#ident\t\t"+ str(len(get_bin(ident,2))) + "\n" + 
    #"\t" + get_bin(checksum, 5) + "\t\t#checksum\t" + str(len(get_bin(checksum, 5))) + "\n" +  
    #"\t" + get_bin(channel_number,3) + "\t\t#channel_number\t" + str(len(get_bin(channel_number,3))) + "\n" +  
    #"\t" + get_bin(pulse_width,9) + "\t#pulse_width\t" + str(len(get_bin(pulse_width,9))) + "\n" +  
    #"\t" + get_bin(pulse_current,7) + "\t\t#pulse_current\t" + str(len(get_bin(pulse_current,7))) + "\n" 
    #) 
    binarized_cmd = get_bin(ident,2) + get_bin(checksum, 5) + get_bin(channel_number,3) + get_bin(pulse_width,9) + get_bin(pulse_current,7)
    cmd_pointer = 0
    new_cmd_pointer = 0
    proper_cmd= ["0" for x in range(32)]

    for c in proper_cmd:
        if new_cmd_pointer == 0: #add a 1
            proper_cmd[new_cmd_pointer]="1"
        elif new_cmd_pointer == (9-1) or new_cmd_pointer == (17-1) or new_cmd_pointer == (25-1): #add a 0 
            proper_cmd[new_cmd_pointer]="0"
        elif new_cmd_pointer == (13-1) or new_cmd_pointer == (14-1): #add a X
            proper_cmd[new_cmd_pointer]="0"
        else:
            proper_cmd[new_cmd_pointer]=binarized_cmd[cmd_pointer]
            cmd_pointer+=1
        new_cmd_pointer+=1

    proper_bin_command = ''.join(map(str,proper_cmd))
    #print(proper_bin_command)

    hex_command = (hex(int(proper_bin_command, 2)).replace("0x",''))
    hex_command = hex_command.replace("L",'')
    # print(hex(int(proper_bin_command, 2)))
    # print("final output hex_command : ",hex_command)
    return(binascii.unhexlify(hex_command))
# End of singlepulse.py

## This message terminates the connection with the stimulator.
## To start communicating with it again you will have to unplug and replug the device to the computer
def generate_terminate_connection():
    proper_bin_command = '11000000'
    return(binascii.unhexlify(proper_bin_command))
 #    hex_command = (hex(int(proper_bin_command, 2)).replace("0x",''))
    # hex_command = hex_command.replace("L",'')
    # print(hex(int(proper_bin_command, 2)))
    # return(binascii.unhexlify(hex_command))




"""*
    *ident             2 bits        00 for init
    *check             3 bits        0..7 checksum
    *_N_factor         3 bits        0..7
    *_channels_stim 8 bits        0..255 
    * Please for ease of use give channels status to the top function like this : 
    * '00000100' for channel 3 only or '00001100' for channels 3 and 4 to be ON, etc ...
    *_channels_lf     8 bits        0..255
    *_group_time     5 bits        0..31
    *_main_time     11 bits        0..2047
    *"""
def generate_channel_list_mode_init(_N_factor,_channels_stim,_channels_lf,_group_time,_main_time):

    ident = CHANNEL_INIT
    N_factor = _N_factor
    channels_stim = get_channels_as_int_from_bin(_channels_stim)
    channels_lf = get_channels_as_int_from_bin(_channels_lf)
    group_time = _group_time
    main_time = _main_time


    checksum = (N_factor + channels_stim + channels_lf + group_time + main_time) % 8#32
    #print("checksum verify = " + str(checksum))

    binarized_cmd = get_bin(ident,2) + get_bin(checksum, 3) + get_bin(N_factor,3) \
    + get_bin(channels_stim,8) + get_bin(channels_lf,8) + get_bin(group_time,5) + get_bin(main_time,11) 
    cmd_pointer = 0
    new_cmd_pointer = 0
    proper_cmd= ["0" for x in range(48)]

    for c in proper_cmd:
        if new_cmd_pointer == 0: #add a 1
            proper_cmd[new_cmd_pointer]="1"
        elif new_cmd_pointer == (9-1) or new_cmd_pointer == (17-1) or new_cmd_pointer == (25-1):
            #add a 0 for bytes 2,3 and 4
            proper_cmd[new_cmd_pointer]="0"
        elif new_cmd_pointer == (33-1) or new_cmd_pointer == (40-1):
            #add a 0 for bytes 5 and 6
            proper_cmd[new_cmd_pointer]="0"
        elif new_cmd_pointer == (29-1) or new_cmd_pointer == (30-1):
            #add a X on byte 4 bit 3 and 2
            proper_cmd[new_cmd_pointer]="0"
        else:
            proper_cmd[new_cmd_pointer]=binarized_cmd[cmd_pointer]
            cmd_pointer+=1
        new_cmd_pointer+=1

    proper_bin_command = ''.join(map(str,proper_cmd));
    print([proper_bin_command[i:i+8] for i in range(0, len(proper_bin_command), 8)])

    hex_command = (hex(int(proper_bin_command, 2)).replace("0x",''))
    hex_command = hex_command.replace("L",'')
    #print(hex(int(proper_bin_command, 2)))
    return(binascii.unhexlify(hex_command))

"""*
    *ident             2 bits        00 for init
    *check             3 bits        0..7 checksum
    *_N_factor         3 bits        0..7
    *_channels_stim 8 bits           0..255 
    * Please for ease of use give channels status to the top function like this : 
    * '00000100' for channel 3 only or '00001100' for channels 3 and 4 to be ON, etc ...
    *_channels_lf     8 bits        0..255
    *_group_time     5 bits        0..31
    *_main_time     11 bits        0..2047
    *"""
def generate_channel_list_mode_init2(_N_factor,_channels_stim,_channels_lf,_group_time,_main_time):
    
    # Command to initialze Channel-List-Mode
    ident = CHANNEL_INIT

    # Factor for lower stimulation frequency of some channels
    N_factor = validateRange(_N_factor, 0, 7);

    # Get stimulation Channels
    channels_stim = get_channels_as_int_from_bin(_channels_stim)
    channels_stim = validateRange(channels_stim,0,255)

    # Get stimulation channels to which the "low-frequency" should be applied
    channels_lf   = get_channels_as_int_from_bin(_channels_lf)
    channels_lf = validateRange(channels_lf,0,255)
    
    # Defines the Inter-pulse-interval during N-let Stimulation (doublets/triplets)
    group_time = validateRange(_group_time,0,31)
    
    # Defines the main stimulation frequency
    main_time = validateRange(_main_time,0,2047)

    # Calculate checksum
    checksum = (N_factor + channels_stim + channels_lf + group_time + main_time) % 8 #32
    #print("checksum verify = " + str(checksum))


    # Get binary String representation of the values of interest
    intent_str = get_bin(ident,2)
    #print("Indent String = " + intent_str)

    checksum_str = get_bin(checksum,3)
    #print("Checksum String = " + checksum_str)

    n_factor_str = get_bin(N_factor,3)
    #print("N-Factor String = " + n_factor_str)

    channels_stim_str = get_bin(channels_stim,8)
    #print("Channels String = " + channels_stim_str)

    channels_lf_str = get_bin(channels_lf,8)
    #print("Channels LF String = " + channels_lf_str)

    group_time_str = get_bin(group_time,5)
    #print("Group_time String = " + group_time_str)

    main_time_str = get_bin(main_time,11)
    #print("Main_time String = " + main_time_str)
    
    # Build Bytes
    Byte1 = '1'
    Byte1 += intent_str[0]
    Byte1 += intent_str[1]
    Byte1 += checksum_str[0]
    Byte1 += checksum_str[1]
    Byte1 += checksum_str[2]
    Byte1 += n_factor_str[0]
    Byte1 += n_factor_str[1]

    Byte2 = '0'
    Byte2 += n_factor_str[2]
    Byte2 += channels_stim_str[0]
    Byte2 += channels_stim_str[1]
    Byte2 += channels_stim_str[2]
    Byte2 += channels_stim_str[3]
    Byte2 += channels_stim_str[4]
    Byte2 += channels_stim_str[5]

    Byte3 = '0'
    Byte3 += channels_stim_str[6]
    Byte3 += channels_stim_str[7]
    Byte3 += channels_lf_str[0]
    Byte3 += channels_lf_str[1]
    Byte3 += channels_lf_str[2]
    Byte3 += channels_lf_str[3]
    Byte3 += channels_lf_str[4]
       
    Byte4 = '0'
    Byte4 += channels_lf_str[5]
    Byte4 += channels_lf_str[6]
    Byte4 += channels_lf_str[7]
    Byte4 += '00'  # X - not used
    Byte4 += group_time_str[0]
    Byte4 += group_time_str[1]

    Byte5 = '0'
    Byte5 += group_time_str[2]
    Byte5 += group_time_str[3]
    Byte5 += group_time_str[4]
    Byte5 += main_time_str[0]
    Byte5 += main_time_str[1]
    Byte5 += main_time_str[2]
    Byte5 += main_time_str[3]

    Byte6 = '0'
    Byte6 += main_time_str[4]
    Byte6 += main_time_str[5]
    Byte6 += main_time_str[6]
    Byte6 += main_time_str[7]
    Byte6 += main_time_str[8]
    Byte6 += main_time_str[9]
    Byte6 += main_time_str[10]
 
    # Merge to message
    proper_bin_command = Byte1 + Byte2 + Byte3 + Byte4 + Byte5 + Byte6
    print([proper_bin_command[i:i+8] for i in range(0, len(proper_bin_command), 8)])

    hex_command = (hex(int(proper_bin_command, 2)).replace("0x",''))
    hex_command = hex_command.replace("L",'')
    #print(hex(int(proper_bin_command, 2)))
    return(binascii.unhexlify(hex_command))



"""*
    *ident             2 bits        01 for init
    *check             5 bits        0..31 checksum
    *_Mode_list         2 bits        0..2
    *_pulse_width_list     9 bits        0,10..500     10 by 10  pulse width in uS
    *_pulse_current_list     7 bits        0..127   current in mA
    *"""
def generate_channel_list_mode_update(_Mode_list,_pulse_width_list,_pulse_current_list):

    ident = CHANNEL_UPDATE
    Mode_list = _Mode_list # 0 for single pulse, 1 for doublets, 2 for triplets
    pulse_width_list = _pulse_width_list
    pulse_current_list = _pulse_current_list

    number_of_channels = len(_pulse_width_list)
    #print("number_of_channels :",number_of_channels)

    checksum = 0

    for i in range(number_of_channels):
        #print("checksum pass")
        checksum += Mode_list[i] + pulse_width_list[i] + pulse_current_list[i]#%32
    checksum = (checksum) % 32
    #print("checksum verify = " + str(checksum))


    binarized_cmd = get_bin(ident,2) + get_bin(checksum, 5)

    for i in range(number_of_channels):
        binarized_cmd += get_bin(Mode_list[i],2) + get_bin(pulse_width_list[i], 9) + get_bin(pulse_current_list[i], 7)

    #print("binarized_cmd to send : ",binarized_cmd)
    cmd_pointer = 0
    new_cmd_pointer = 0
    proper_cmd= ["0" for x in range(8+number_of_channels*8*3)]

    #print("proper_cmd len :",len(proper_cmd)," proper_cmd raw : ",proper_cmd)
    channel_done_counter = 0
    channel_pointer_offset = 0
    for c in proper_cmd:

         #Test if channel_counter needs +=1
        if new_cmd_pointer == channel_pointer_offset + 8 + 8*3:
        # If pointer postition is offset + base + entire channel
            channel_done_counter += 1
            channel_pointer_offset = channel_done_counter*8*3

        if new_cmd_pointer == 0: #add a 1
            proper_cmd[new_cmd_pointer]="1"

        elif new_cmd_pointer == (9-1 + channel_pointer_offset) or \
        new_cmd_pointer == (17-1 + channel_pointer_offset) or \
        new_cmd_pointer == (25-1 + channel_pointer_offset):
            #add a 0 for each first bit on each channel bytes
            proper_cmd[new_cmd_pointer]="0"

        elif new_cmd_pointer == (12-1 + channel_pointer_offset) or \
        new_cmd_pointer == (13-1 + channel_pointer_offset) or \
        new_cmd_pointer == (14-1 + channel_pointer_offset):
            #add a X for first channel byte on bits 4, 3 and 2
            proper_cmd[new_cmd_pointer]="0"

        else:
            proper_cmd[new_cmd_pointer]=binarized_cmd[cmd_pointer]
            cmd_pointer+=1
        new_cmd_pointer+=1

    proper_bin_command = ''.join(map(str,proper_cmd))
    #print(proper_bin_command)

    hex_command = (hex(int(proper_bin_command, 2)).replace("0x",''))
    hex_command = hex_command.replace("L",'')
    #print(hex(int(proper_bin_command, 2)))
    #print("final output message : ",hex_command)
    return(binascii.unhexlify(hex_command))





def generate_channel_list_mode_stop():

    ident = CHANNEL_STOP

    checksum = 0 #(0) % 32
    #print("checksum verify = " + str(checksum))

    binarized_cmd = get_bin(ident,2) + get_bin(checksum, 5)
    cmd_pointer = 0
    new_cmd_pointer = 0
    proper_cmd= ["0" for x in range(8)]

    for c in proper_cmd:
        if new_cmd_pointer == 0: #add a 1
            proper_cmd[new_cmd_pointer]="1"
        else:
            proper_cmd[new_cmd_pointer]=binarized_cmd[cmd_pointer]
            cmd_pointer+=1
        new_cmd_pointer+=1

    proper_bin_command = ''.join(map(str,proper_cmd))
#print(proper_bin_command)

    hex_command = (hex(int(proper_bin_command, 2)).replace("0x",''))
    hex_command = hex_command.replace("L",'')
    #print(hex(int(proper_bin_command, 2)))
    return(binascii.unhexlify(hex_command))



def get_channels_as_int_from_bin(channels_bin_as_string_format):
    return int(channels_bin_as_string_format,2)


"""*
    *Checks and corrects a given value with respect to a defined range

    *value          Value to be checked and corrected
    *lowerLimit     Lower limit for the given value
    *upperLimit     Upper limit for the given value
    *"""
def validateRange(value, lowerLimit, upperLimit):
    
    if value < lowerLimit:
        value = lowerLimit
    if value > upperLimit:
        value = upperLimit

    return value