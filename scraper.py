import requests
from bs4 import BeautifulSoup
import time
import os
import re
# 基础URL
base_url = "https://you.ctrip.com/sight/shaoxing18/s0-p{}.html"
headers = {
    "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64) AppleWebKit / 537.36(KHTML, like Gecko) Chrome / 80.0.3987.122  Safari / 537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9"
}


def parse_detail(url):
    """解析景点详情页"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'  # 强制使用 UTF-8 解码
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 提取景点名称
        name = soup.find("div", class_="title").find("h1").text.strip() if soup.find("div", class_="title") else None
        
        # 提取热度值
        heat_score = soup.find("div", class_="heatScoreText").text.strip() if soup.find("div", class_="heatScoreText") else None
        
        # 提取评分
        comment_score = soup.find("p", class_="commentScoreNum").text.strip() if soup.find("p", class_="commentScoreNum") else None
        
        # 提取景点地址 - 新增
        address = None
        address_div = soup.find("div", class_="baseInfoItem")
        if address_div:
            address_p = address_div.find("p", class_="baseInfoText")
            if address_p:
                address = address_p.text.strip()
        
        # 提取用户评论
        comments = []
        comment_items = soup.find_all("div", class_="commentItem")
        for item in comment_items:
            content = item.find("div", class_="commentDetail").text.strip() if item.find("div", class_="commentDetail") else ""
            comments.append(content)
        
        return {
            "景点名称": name,
            "热度值": heat_score,
            "评分": comment_score,
            "景点地址": address,  # 新增
            "用户评论": comments
        }

    except Exception as e:
        print(f"详情页解析失败: {url}, 错误: {str(e)}")
        return None


def crawl_shaoxing_attractions(max_pages=1):
    """爬取绍兴景点数据"""
    all_data = []
    for page in range(1, max_pages+1):
        current_url = base_url.format(page)
        try:
            response = requests.get(current_url, headers=headers, timeout=10)
            response.encoding = 'utf-8'  # 强制使用 UTF-8 解码
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 提取景点列表
            sight_items = soup.find_all("div", class_="sightItemCard_box__2FUEj")
            if not sight_items:
                print(f"第{page}页未找到景点元素，可能已无更多数据")
                break
            
            for item in sight_items:
                # 提取景点详情页链接
                title_div = item.find("div", class_="titleModule_name__Li4Tv")
                if title_div:
                    a_tag = title_div.find("a", href=True)
                    if a_tag:
                        detail_url = a_tag["href"]
                        # 处理相对URL
                        if detail_url.startswith("/"):
                            detail_url = "https://you.ctrip.com" + detail_url
                        # 解析详情页
                        data = parse_detail(detail_url)
                        if data:
                            all_data.append(data)
                        # 防止请求过快
                        time.sleep(1)
        
        except Exception as e:
            print(f"第{page}页爬取失败: {str(e)}")
            continue
        
        # 控制分页爬取速度
        time.sleep(2)
    
    return all_data


def save_to_file(data):
    """保存数据到桌面文件"""
    try:
        # 获取桌面路径
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path = os.path.join(desktop, "绍兴景点数据.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            for idx, item in enumerate(data, 1):
                f.write(f"景点 {idx}:\n")
                f.write(f"  名称: {item['景点名称']}\n")
                f.write(f"  热度值: {item['热度值']}\n")
                f.write(f"  评分: {item['评分']}\n")
                f.write(f"  地址: {item['景点地址']}\n")  # 新增
                f.write("  用户评论:\n")
                for comment_idx, comment in enumerate(item['用户评论'], 1):
                    f.write(f"    {comment_idx}. {comment}\n")
                f.write("\n" + "-"*50 + "\n")
        
        print(f"数据已成功保存到: {file_path}")
    except Exception as e:
        print(f"保存文件失败: {str(e)}")


# 执行爬取（示例爬取1页数据，可根据需要调整max_pages参数）
if __name__ == "__main__":
    data = crawl_shaoxing_attractions(max_pages=3)
    
    # 保存到文件 - 新增
    save_to_file(data)
    
    # 打印结果（可注释掉，只保留文件保存）
    for item in data:
        print(f"景点名称: {item['景点名称']}")
        print(f"热度值: {item['热度值']}")
        print(f"评分: {item['评分']}")
        print(f"地址: {item['景点地址']}")  # 新增
        print("用户评论:")
        for idx, comment in enumerate(item['用户评论'], 1):
            print(f"{idx}. {comment}")
        print("\n" + "-"*50)