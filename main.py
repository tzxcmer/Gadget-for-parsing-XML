# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import csv
import os
import re


# 检查给定文件是否在自研代码目录下。
#
# 参数：
# file：要检查的文件。
# required_patterns：必需的目录列表。
# excluded_patterns：排除的目录列表。
#
# 返回值：
# 如果文件包含所有必需模式并且不包含任何排除模式，则返回True；否则返回False。
def check_file(file, required_patterns, excluded_patterns):
    for pattern in required_patterns:
        if pattern not in file:
            return False
    for pattern in excluded_patterns:
        if pattern in file:
            return False
    return True

# 
required_patterns = ['/BSW/']
excluded_patterns = ['/BSW/gPtp/']

# 在给定文件中添加根元素。
#
# 参数：
# original_file：原始文件。
# new_file：新文件。
# 
# 返回值：
# 无。
def add_root_element(original_file, new_file):
    #
    with open(original_file, 'r') as f:
        content = f.read()
    # 
    new_content = '<errors>\n' + content + '</errors>'
    # 
    with open(new_file, 'w') as f:
        f.write(new_content)

# 解析XML文件。
#
# 参数：
# xml_file：XML文件。
# pattern_name：检查器名称。
#
# 返回值：
# 检查器计算结果。
def parse_xml(xml_file,pattern_name):
    # 
    cnt = 0
    base_name = os.path.basename(xml_file)
    checker_value = base_name.split('.')[0]
    checker_value = checker_value.replace('_with_root', '')
    
    # 
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # 
    with open(f'output_{checker_value}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        # 
        writer.writerow(['file', 'function', 'line', 'description_value'])
        # 
        for error in root.findall('error'):
            # 
            checker = error.find('checker').text
            if checker == checker_value:
                file = error.find('file').text
                if check_file(file, required_patterns, 
                                    excluded_patterns):
                    cnt = cnt + 1
                    function = error.find('function').text
                    line = error.find('event').find('line').text
                    description = error.find('event').find('description').text
                    pattern = r'\{%s\}(.{0,2300})\{' % pattern_name
                    number =  re.search(pattern, description).group(1)
                    number = number.replace('{', '').replace('}', '')
                    if pattern_name == 'CALLING' and number == '0.00':
                        cnt = cnt - 1
                
                    writer.writerow([file, function, line, number])
    return cnt

       
# 计算每个检查器的错误数量。
pattern_names = {"COMF":0,"PATH":0,"GOTO":0,"CCM":0,"CALLING":0,"CALLS":0,
                 "PARAM":0,"STMT":0,"LEVEL":0,"RETURN":0,"VOCF":0,"CYCLE":0}

# 文件路径
folder_name = "MRTOS result"

for pattern_name in pattern_names.keys():
    sourname = '%s\\HIS_%s.errors.xml' % (folder_name, pattern_name)
    destname = '%s\\HIS_%s_with_root.errors.xml' % (folder_name, pattern_name)
    add_root_element(sourname, destname)
    pattern_names[pattern_name] = parse_xml(destname,pattern_name)
    
# 读取STMT检查器的结果。
with open('output_HIS_STMT.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    stmt_functions = {row[1] for row in reader}
    
# 读取COMF检查器的结果。
with open('output_HIS_COMF.csv', 'r') as f:
    reader = csv.reader(f)
    comf_data = list(reader)

# 过滤掉COMF检查器的结果中不在STMT检查器结果中的行。
filtered_comf_data = [row for row in comf_data if row[1] in stmt_functions]

# 写入过滤后的COMF检查器的结果。
with open('filtered_output_HIS_COMF.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(filtered_comf_data)
    
# 填入COMF检查器的错误数量的最终结果。
pattern_names['COMF'] = len(filtered_comf_data)

print(pattern_names)

sum = 0

# 计算总函数数量。
with open('In+Latest_MRTOS_ALL_functions.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        Function, File,*_ = row
        if check_file(File, required_patterns, excluded_patterns):
            sum = sum + 1


print("The TOTAL_FUNCS is {}".format(sum))

ans = 0

# 检查器对应的加权值
Coefficients = {"COMF":0.045,"PATH":0.090,"GOTO":0.090,"CCM":0.090,
               "CALLING":0.045,"CALLS":0.045,"PARAM":0.130,"STMT":0.090,
               "LEVEL":0.090,"RETURN":0.090,"VOCF":0.045,"CYCLE":0.130}

# 计算最终结果
for key,value in Coefficients.items():
    ans = ans + (pattern_names[key]/sum) * value
    
print("The ans is {:.2f}%".format(ans*100))
