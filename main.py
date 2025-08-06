import re
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime

class MarkdownConverter:
    """处理Markdown中LaTeX语法转换的核心类"""
    
    def __init__(self):
        # 定义转换规则的正则表达式
        # 转换规则：
        # 1. 行内公式 \( ... \) -> $...$
        # 2. 块级公式 \[ ... \] -> 去掉外层符号，内容保持原样
        # 使用[\s\S]*?以匹配跨行内容
        # 仅定义行内公式的转换规则；块级公式将在 convert 方法中进行特殊处理
        self.patterns = [
            (r'\\\(\s*([\s\S]*?)\s*\\\)', r'$\1$')   # 行内
        ]
    
    def convert(self, text):
        """执行LaTeX语法转换
        
        Args:
            text (str): 输入的markdown文本
            
        Returns:
            str: 转换后的markdown文本
        """
        if not text or not text.strip():
            return text
            
        converted_text = text
        
        # 1. 处理行内公式
        for pattern, replacement in self.patterns:
            converted_text = re.sub(pattern, replacement, converted_text)

        # 2. 处理块级公式，根据是否包含 "\\begin" 和 "\\end" 采用不同策略
        def _replace_block(match: re.Match) -> str:
            content = match.group(1)
            # 如果内容中包含 \begin 和 \end ...
            if re.search(r'\\begin', content) and re.search(r'\\end', content):
                # 检测是否为 matrix 系列环境（matrix, bmatrix, pmatrix, vmatrix 等）
                if re.search(r'\\begin\{[^}]*matrix[^}]*\}', content, re.IGNORECASE):
                    # 将外层符号替换为块级数学定界 $$ $$
                    return f'$$\n{content}\n$$'
                # 其他环境保持原样（去掉外层符号）
                return content
            # 否则转换为行内公式
            return f'${content}$'

        converted_text = re.sub(r'\\\[\s*([\s\S]*?)\s*\\\]', _replace_block, converted_text)

        return converted_text
    
    def get_conversion_stats(self, original_text, converted_text):
        """获取转换统计信息
        
        Args:
            original_text (str): 原始文本
            converted_text (str): 转换后文本
            
        Returns:
            dict: 包含转换统计的字典
        """
        stats = {
            'inline_math_converted': 0,  # \( \) 转换数量
            'display_math_converted': 0,  # \[ \] 转换数量
            'total_conversions': 0
        }
        
        # 统计 \( \) 转换数量
        inline_matches = re.findall(r'\\\(\s*[\s\S]*?\s*\\\)', original_text)
        stats['inline_math_converted'] = len(inline_matches)
        
        # 统计 \[ \] 转换数量
        display_matches = re.findall(r'\\\[\s*[\s\S]*?\s*\\\]', original_text)
        stats['display_math_converted'] = len(display_matches)
        
        stats['total_conversions'] = stats['inline_math_converted'] + stats['display_math_converted']
        
        return stats


class FileManager:
    """处理文件保存操作的类"""
    
    def __init__(self):
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    
    def save_to_desktop(self, content, filename=None):
        """将内容保存到桌面的.md文件
        
        Args:
            content (str): 要保存的文件内容
            filename (str, optional): 文件名，如果不提供则自动生成
            
        Returns:
            tuple: (success: bool, filepath: str, message: str)
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'converted_markdown_{timestamp}.md'
            
            # 确保文件名以.md结尾
            if not filename.endswith('.md'):
                filename += '.md'
            
            filepath = os.path.join(self.desktop_path, filename)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, filepath, f'文件已成功保存到桌面：{filename}'
            
        except PermissionError:
            return False, '', '权限错误：无法写入桌面文件'
        except Exception as e:
            return False, '', f'保存文件时发生错误：{str(e)}'


class MarkdownConverterGUI:
    """Markdown转换器的图形用户界面类"""
    
    def __init__(self):
        self.converter = MarkdownConverter()
        self.file_manager = FileManager()
        self.setup_gui()
    
    def setup_gui(self):
        """设置GUI界面"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title('Markdown LaTeX转换器')
        self.root.geometry('800x600')
        self.root.resizable(True, True)
        
        # 居中显示窗口
        self.center_window()
        
        # 创建界面组件
        self.create_widgets()
    
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """创建界面组件"""
        # 标题标签
        title_label = tk.Label(
            self.root, 
            text='Markdown LaTeX语法转换器',
            font=('Arial', 16, 'bold'),
            pady=10
        )
        title_label.pack()
        
        # 说明标签
        info_label = tk.Label(
            self.root,
            text='将 \\( 内容 \\) 转换为 $内容$，\\[ 内容 \\] 转换为 $内容$',
            font=('Arial', 10),
            fg='gray'
        )
        info_label.pack(pady=(0, 10))
        
        # 输入区域标签
        input_label = tk.Label(
            self.root,
            text='请粘贴Markdown源码：',
            font=('Arial', 12),
            anchor='w'
        )
        input_label.pack(fill='x', padx=20, pady=(0, 5))
        
        # 文本输入框（带滚动条）
        self.text_input = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=('Consolas', 10)
        )
        self.text_input.pack(fill='both', expand=True, padx=20, pady=5)
        
        # 按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # 转换按钮
        self.convert_button = tk.Button(
            button_frame,
            text='转换并保存到桌面',
            command=self.convert_and_save,
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.convert_button.pack(side='left', padx=5)
        
        # 清空按钮
        clear_button = tk.Button(
            button_frame,
            text='清空',
            command=self.clear_text,
            font=('Arial', 12),
            bg='#f44336',
            fg='white',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        clear_button.pack(side='left', padx=5)
        
        # 状态标签
        self.status_label = tk.Label(
            self.root,
            text='准备就绪',
            font=('Arial', 10),
            fg='green',
            pady=10
        )
        self.status_label.pack()
    
    def convert_and_save(self):
        """执行转换并保存文件"""
        try:
            # 获取输入文本
            input_text = self.text_input.get('1.0', tk.END).strip()
            
            if not input_text:
                messagebox.showwarning('警告', '请输入要转换的Markdown文本！')
                return
            
            # 更新状态
            self.status_label.config(text='正在转换...', fg='orange')
            self.root.update()
            
            # 执行转换
            converted_text = self.converter.convert(input_text)
            
            # 获取转换统计
            stats = self.converter.get_conversion_stats(input_text, converted_text)
            
            # 保存文件
            success, filepath, message = self.file_manager.save_to_desktop(converted_text)
            
            if success:
                # 显示成功信息
                stats_message = f"转换完成！\n" \
                              f"行内公式转换: {stats['inline_math_converted']} 个\n" \
                              f"块级公式转换: {stats['display_math_converted']} 个\n" \
                              f"总计转换: {stats['total_conversions']} 个\n\n" \
                              f"{message}"
                
                messagebox.showinfo('转换成功', stats_message)
                self.status_label.config(text=f'转换成功 - {stats["total_conversions"]} 个公式已转换', fg='green')
            else:
                messagebox.showerror('保存失败', message)
                self.status_label.config(text='保存失败', fg='red')
                
        except Exception as e:
            error_message = f'转换过程中发生错误：{str(e)}'
            messagebox.showerror('错误', error_message)
            self.status_label.config(text='转换失败', fg='red')
    
    def clear_text(self):
        """清空文本输入框"""
        self.text_input.delete('1.0', tk.END)
        self.status_label.config(text='已清空', fg='blue')
    
    def run(self):
        """启动GUI应用"""
        self.root.mainloop()


def main():
    """主程序入口"""
    try:
        # 创建并运行GUI应用
        app = MarkdownConverterGUI()
        app.run()
    except Exception as e:
        print(f"应用启动失败：{str(e)}")
        input("按Enter键退出...")


if __name__ == '__main__':
    main()