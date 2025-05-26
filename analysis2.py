import pandas as pd
import matplotlib.pyplot as plt
import jieba
from wordcloud import WordCloud
from PIL import Image
import numpy as np
import re
import os
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 设置文件路径（自动定位到桌面）
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
file_path = os.path.join(desktop, "绍兴景点数据.txt")
output_path = desktop  # 图表保存路径

# ----------------------
# 一、数据解析模块（带严格清洗）
# ----------------------
def parse_scenic_data(file_path):
    """
    解析景点数据文本，包含严格的数据清洗和异常处理
    返回：DataFrame（包含名称、热度值、评分、评论等字段）
    """
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:  # 忽略编码错误
            content = f.read()
            
            # 分割景点（支持中文数字/阿拉伯数字编号，兼容多行格式）
            pattern = r'(景点\s*(?:一|二|三|四|五|六|七|八|九|十|\d+):)([\s\S]*?)(?=景点|$)'
            scenic_list = re.findall(pattern, content)
            
            for idx, scenic_content in enumerate(scenic_list, 1):
                lines = [line.strip() for line in scenic_content[1].split('\n') if line.strip()]
                item = {
                    '景点编号': idx,
                    '名称': None,
                    '热度值': np.nan,  # 使用NaN表示缺失值
                    '评分': np.nan,
                    '评论列表': []
                }
                
                for line in lines:
                    # 提取核心字段（使用正则确保格式兼容）
                    name_match = re.match(r'名称:\s*(.*)', line)
                    heat_match = re.match(r'热度值:\s*(\d+\.?\d*)', line)
                    score_match = re.match(r'评分:\s*(\d+\.?\d*)', line)
                    comment_match = re.match(r'^\[(\d+|一|十)\] ', line)  # 处理评论编号

                    if name_match:
                        item['名称'] = name_match.group(1).strip()
                    elif heat_match:
                        item['热度值'] = float(heat_match.group(1))
                    elif score_match:
                        item['评分'] = float(score_match.group(1))
                    elif item['名称'] and '用户评论:' in line:
                        item['comment_flag'] = True  # 标记评论开始
                    elif item.get('comment_flag', False):
                        # 处理多行评论，允许无编号评论
                        if comment_match:
                            item['评论列表'].append(line[comment_match.end():].strip())
                        else:
                            item['评论列表'].append(line.strip())
                
                # 仅保留有效数据（名称、热度、评分至少两项非空）
                if item['名称'] and not (np.isnan(item['热度值']) and np.isnan(item['评分'])):
                    data.append(item)
        
        return pd.DataFrame(data).dropna(subset=['名称'])  # 剔除名称为空的记录

    except FileNotFoundError:
        print(f" 错误：文件未找到 - {file_path}")
        return None
    except Exception as e:
        print(f" 数据解析错误：{str(e)}，请检查文件格式")
        return None

# ----------------------
# 二、可视化模块（整合图表生成）
# ----------------------
def generate_visualizations(df):
    """生成整合图表（直方图+散点图+柱状图）"""
    plt.figure(figsize=(18, 12), facecolor='#f9f9f9')
    
    # 子图1：热度值分布直方图
    plt.subplot(2, 2, 1)
    plt.hist(
        df['热度值'], 
        bins=10, 
        edgecolor='white', 
        alpha=0.8, 
        color='#1f77b4',
        label='景点数量'
    )
    plt.title('绍兴景点热度值分布', fontsize=14, pad=20)
    plt.xlabel('热度值', fontsize=12)
    plt.ylabel('景点数量', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.legend()

    # 子图2：热度-评分散点图
    plt.subplot(2, 2, 2)
    scatter = plt.scatter(
        df['热度值'], 
        df['评分'], 
        alpha=0.9, 
        c=df['评分'], 
        cmap='viridis', 
        edgecolors='white',
        s=80
    )
    plt.title('热度与评分相关性分析', fontsize=14, pad=20)
    plt.xlabel('热度值', fontsize=12)
    plt.ylabel('评分', fontsize=12)
    plt.colorbar(label='评分等级', shrink=0.8)
    plt.grid(True, alpha=0.2)

    # 子图3：评分Top10柱状图
    plt.subplot(2, 1, 2)
    top10 = df.sort_values('评分', ascending=False).head(10)
    bars = plt.bar(
        top10['名称'], 
        top10['评分'], 
        color='#2ca02c', 
        edgecolor='white',
        width=0.6
    )
    plt.title('评分最高的10大景点', fontsize=14, pad=20)
    plt.xlabel('景点名称', fontsize=12)
    plt.ylabel('评分（满分5.0）', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.grid(axis='y', alpha=0.3)
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2, 
            height + 0.1, 
            f'{height:.1f}', 
            ha='center', 
            fontsize=10
        )
    
    plt.tight_layout(pad=5)
    plt.savefig(os.path.join(output_path, '绍兴景点分析整合图表.png'), dpi=300)
    plt.show()

# ----------------------
# 三、词云生成模块（带智能过滤）
# ----------------------
def generate_comment_word_cloud(df):
    """生成用户评论词云图，自动过滤无效词汇"""
    # 合并所有评论并进行深度清洗
    all_comments = ' '.join([
        comment for comments in df['评论列表'] 
        for comment in comments 
        if len(comment) > 5  # 过滤短评论
    ])
    
    # 自定义分词优化
    jieba.add_word('乌篷船', freq=500)
    jieba.add_word('鲁迅故里', freq=800)
    jieba.add_word('曲水流觞', freq=300)
    stop_words = {'这里', '非常', '感觉', '这个', '可以', '就是', '景点'}  # 动态过滤词
    
    # 分词与过滤
    words = [
        word for word in jieba.cut(all_comments)
        if len(word) >= 2 
        and word not in stop_words
        and not re.match(r'[0-9a-zA-Z]+', word)
    ]
    text = ' '.join(words)
    
    # 生成词云（带蒙版）
    try:
        mask = np.array(Image.open(os.path.join(output_path, '水乡蒙版.png')))  # 自定义蒙版路径
    except:
        mask = None
    
    wc = WordCloud(
        font_path='simhei.ttf', 
        mask=mask,
        background_color='#f0f0f0',
        max_words=500,
        max_font_size=150,
        width=1500,
        height=1000
    ).generate(text)
    
    plt.figure(figsize=(15, 10))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.title('用户评论核心关键词云', fontsize=18, pad=30)
    plt.savefig(os.path.join(output_path, '用户评论词云图.png'), dpi=300)
    plt.show()

# ----------------------
# 四、主程序（整合执行流程）
# ----------------------
if __name__ == "__main__":
    # 1. 数据解析与清洗
    df = parse_scenic_data(file_path)
    if df is None or df.empty:
        print("数据解析失败，程序终止")
        exit(1)
    
    # 2. 数据类型转换
    df['热度值'] = df['热度值'].astype(float)
    df['评分'] = df['评分'].astype(float)
    
    # 3. 生成整合图表
    print("正在生成数据分析图表...")
    generate_visualizations(df)
    
    # 4. 生成词云图
    print("正在生成用户评论词云...")
    generate_comment_word_cloud(df)
    
    print("\n 所有任务完成，结果已保存至桌面")