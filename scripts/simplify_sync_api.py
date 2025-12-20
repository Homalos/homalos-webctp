#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简化 sync_api.py 文件的脚本"""

import re

def simplify_docstring(docstring: str) -> str:
    """简化文档字符串，保留核心信息"""
    lines = docstring.split('\n')
    
    # 保留第一行描述
    result = [lines[0]] if lines else []
    
    # 查找 Args 部分
    in_args = False
    in_example = False
    for line in lines[1:]:
        stripped = line.strip()
        
        # 跳过示例部分
        if 'Example:' in stripped or '>>>' in stripped:
            in_example = True
            continue
        if in_example:
            continue
            
        # 保留 Args, Returns, Raises 标题
        if stripped.startswith(('Args:', 'Returns:', 'Raises:')):
            result.append(line)
            in_args = 'Args:' in stripped
            continue
        
        # 在 Args 部分，只保留参数名和简短描述（第一行）
        if in_args and stripped and not stripped.startswith(('Returns:', 'Raises:', 'Example:')):
            # 参数行格式: "param_name: description"
            if ':' in stripped and not stripped.startswith(' '):
                param_line = stripped.split(':', 1)
                if len(param_line) == 2:
                    # 只保留第一句话
                    desc = param_line[1].strip().split('。')[0] + '。' if '。' in param_line[1] else param_line[1].strip()
                    result.append(f"            {param_line[0]}: {desc}")
            continue
        
        # 保留 Returns 和 Raises 的简短描述
        if not in_args and stripped and not stripped.startswith(('Example:', '>>>')):
            if any(x in line for x in ['Returns:', 'Raises:']):
                result.append(line)
            elif result and any(x in result[-1] for x in ['Returns:', 'Raises:']):
                # 只保留第一行描述
                result.append(line)
                in_args = False
    
    return '\n'.join(result)

def process_file(input_path: str, output_path: str):
    """处理文件，简化文档字符串"""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式匹配文档字符串
    def replace_docstring(match):
        indent = match.group(1)
        docstring = match.group(2)
        simplified = simplify_docstring(docstring)
        return f'{indent}"""\n{simplified}\n{indent}"""'
    
    # 匹配三引号文档字符串
    pattern = r'(    """)\n(.*?)\n(    """)'
    content = re.sub(pattern, replace_docstring, content, flags=re.DOTALL)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"文件已简化: {output_path}")

if __name__ == '__main__':
    process_file('src/strategy/sync_api.py.backup', 'src/strategy/sync_api_simplified.py')
