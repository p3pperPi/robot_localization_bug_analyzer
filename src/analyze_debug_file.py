# ---------------------------------------------------------
# import

from  enum import   Enum

import os, csv, sys


# ---------------------------------------------------------
# class / function

class Block(Enum):
    HEADER = -1
    OTHER_PROCESS = 0

    PREDICT = 1
    CORRECT = 2

class State(Enum):
    NONE        = 0
    STATE       = 1
    PREDICT     = 2
    MEASUREMENT = 3

def getStringFromTo(str_in,str_from,str_to='',contain_base_str = False):
    # 文字列検索 検索対象が''だと0,一致するものがないと-1をそれぞれ返す
    i_from = str_in.find(str_from)
    i_to   = str_in.find(str_to)
    
    if(i_from == -1 or i_to == -1 or str_in == ''):
        return ''
    
    if(str_from == ''):
        i_from= 0
    if(str_to   == ''):
        i_to  = len(str_in)

    if contain_base_str:
        i_to +=  len(str_to)
    else:
        i_from += len(str_from)
    
    return str_in[i_from:i_to]

# ---------------------------------------------------------
# constants

READ_FILE_NAME = 'debug.txt'
DATA_TYPE = ['pose','twist','acceleration']
CSV_HEADER =[
              ['TIME' ,'STATE'      ,'' ,'' ,''    ,''     ,''   ,''  ,''  ,''  ,''     ,''      ,''    ,''   ,''   ,''   
                       'PREDICT'    ,'' ,'' ,''    ,''     ,''   ,''  ,''  ,''  ,''     ,''      ,''    ,''   ,''   ,''   
                      ,'MEASUREMENT','' ,'' ,''    ,''     ,''   ,''  ,''  ,''  ,''     ,''      ,''    ,''   ,''   ,''
              ],
              ['t[ns]','x'          ,'y','z','roll','pitch','yaw','dx','dy','dz','droll','dpitch','dyaw','ddx','ddy','ddz'
                      ,'x'          ,'y','z','roll','pitch','yaw','dx','dy','dz','droll','dpitch','dyaw','ddx','ddy','ddz'
                      ,'x'          ,'y','z','roll','pitch','yaw','dx','dy','dz','droll','dpitch','dyaw','ddx','ddy','ddz'
              ]
            ]

# ---------------------------------------------------------
# variables


read_file_fullpath = os.path.join( os.path.dirname(os.getcwd()) , READ_FILE_NAME)

current_block = Block.HEADER
update_data_array = []

write_csv_names = []
current_msg_type = ''
current_data_type = ''

next_line = State.NONE
has_predict = []

reading_line = 0 
current_time = 0
current_list_no = -1
current_csv_line = [0.0] * 46


# ---------------------------------------------------------
# main process

print ('open file :'  + read_file_fullpath)

with open(read_file_fullpath) as f:
    for line in f:
        reading_line += 1
        
        # ---------------------------------------------------------
        # HEADER
        if(current_block == Block.HEADER):
            if('Subscribed to' in line):
                # message format : 
                # > Subscribed to $TOPIC_NAME ($TOPIC_TYPE)
                current_msg_type = getStringFromTo(line,'(',')')
            
            elif(current_msg_type !=  ''):
                # message format : 
                # > $TOPIC_TYPE $DATA_TYPE update vector is ($FLAG_ARRAY)
                for d_type in DATA_TYPE:
                    if (((d_type + ' update vector') in line) and ('true' in line) ):
                        update_data_array.append([current_msg_type ,  d_type])
            
                # END HEADER
                if(line == '\n' or line == '\r\n' ):
                    print('read data  is ')
                    for m_type,d_type  in update_data_array:
                        print(m_type + '  ' + d_type)
                        
                        
                        tmp_csv_name = m_type+'_'+d_type+'.csv'
                        
                        write_csv_names.append(tmp_csv_name)
                        with open(tmp_csv_name,'w') as f:
                            writer = csv.writer(f)
                            writer.writerows(CSV_HEADER)
                    current_block = Block.OTHER_PROCESS
                    
                    
        # ---------------------------------------------------------
        # OTHER_PROCESS
        elif(current_block == Block.OTHER_PROCESS):
            if('time is' in line):
                if('Measurement time is' in line):
                    # message format : 
                    # > Integration time is $UNIX_SECOND.$UNIX_.1NANOSECOND
                    current_time =  float(int(getStringFromTo(line,'Measurement time is ',',')))/1000000000.0
                    
                elif('Integration time is' in line):
                    # message format : 
                    # > Measurement time is $NANOSECOND, last measurement time is $NANOSECOND_P, delta is $NANOSECOND_D
                    current_time =  float(getStringFromTo(line,'Integration time is '))

            elif(' FilterBase::processMeasurement' in line):
                # message format : 
                # > ------ FilterBase::processMeasurement ($TOPIC_TYPE_$DATA_TYPE) ------
                current_msg_type  = getStringFromTo(line,'(','_')
                current_data_type = getStringFromTo(line,'_',')')
                current_list_no   = update_data_array.index([getStringFromTo(line,'(','_'),getStringFromTo(line,'_',')')])
            
            elif('/FilterBase::processMeasurement' in line):
                # message format : 
                # > ------/FilterBase::processMeasurement ($TOPIC_TYPE_$DATA_TYPE) ------
                current_msg_type  = ''
                current_data_type = ''
                current_list_no   = -1
            
            elif(current_list_no != -1):
                if(' Ekf::predict' in line):
                    # message format : 
                    # > ---------------------- Ekf::correct ----------------------
                    current_block =Block.PREDICT
                    
                elif(' Ekf::correct' in line):
                    # message format : 
                    # > ---------------------- Ekf::predict ----------------------
                    current_block =Block.CORRECT
                
            
        
        # ---------------------------------------------------------
        # Predict
        elif(current_block == Block.PREDICT):
            if('Predicted state is:' in line):
                # > Predicted state is: 
                # > [state]
                next_line = State.PREDICT
            elif(next_line == State.PREDICT):
                i = 0
                for data in getStringFromTo(line,'[',']').split():
                    current_csv_line[16+i] = float(data)
                    i += 1
                next_line = State.NONE

            elif('/Ekf::predict' in line):
                # message format : 
                # > ----------------------/Ekf::predict ----------------------
                current_block = Block.OTHER_PROCESS


        # ---------------------------------------------------------
        # Correct
        elif(current_block == Block.CORRECT):
            if('Measurement is:' in line):
                # > Measurement is:
                # > [state]
                next_line = State.MEASUREMENT
            elif(next_line == State.MEASUREMENT):
                i = 0
                for data in getStringFromTo(line,'[',']').split():
                    current_csv_line[31+i] = float(data)
                    i += 1
                next_line = State.NONE
                
            elif('Corrected full state is:' in line):
                # > Corrected full state is:
                # > [state]
                next_line = State.STATE
            elif(next_line == State.STATE):
                i = 0
                for data in getStringFromTo(line,'[',']').split():
                    current_csv_line[1+i] = float(data)
                    i += 1
                next_line = State.NONE
                

            elif('/Ekf::correct' in line):
                # message format : 
                # > ----------------------/Ekf::correct ----------------------
                #
                # write csv line
                current_csv_line[0] = current_time
                
                with open(update_data_array[current_list_no][0]+'_'+update_data_array[current_list_no][1]+'.csv','a') as f:
                    writer = csv.writer(f)
                    writer.writerow(current_csv_line)
                
                # Clear csv line
                current_csv_line = [0.0] * 46
                current_block = Block.OTHER_PROCESS
                
                print('reading line {:10d}'.format(reading_line) ,end='\r')


        
        # ---------------------------------------------------------
        #  temporary Max buffer
        # if(reading_line >  1000):
            # sys.exit()

print('')
print('Done.')
print('Read ' + str(reading_line) + 'lines. exported file is:')
print(write_csv_names)