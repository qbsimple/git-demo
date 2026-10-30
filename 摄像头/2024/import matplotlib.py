import matplotlib.pyplot as plt
import numpy as np

def draw_path(start, end, obstacles, path):
    # 创建图形
    plt.figure(figsize=(10, 7))
    ax = plt.gca()
    
    # 设置网格线
    ax.set_xticks(np.arange(0.5, COLS + 0.5, 1), minor=True)
    ax.set_yticks(np.arange(0.5, ROWS + 0.5, 1), minor=True)
    ax.grid(which="minor", color='gray', linestyle='-', linewidth=0.5)
    ax.set_xticks(np.arange(0, COLS + 1, 1))
    ax.set_yticks(np.arange(0, ROWS + 1, 1))
    ax.set_xlim(0, COLS)
    ax.set_ylim(0, ROWS)
    ax.set_aspect('equal')
    ax.invert_yaxis()  # 为了匹配数组坐标系 (0,0)在左上角
    
    # 绘制障碍物 (红色方块)
    for obs in obstacles.T:
        x, y = obs[0]-1, obs[1]-1  # 转换为0-based
        rect = plt.Rectangle((x, y), 1, 1, color='red', alpha=0.5)
        ax.add_patch(rect)
    
    # 绘制起点 (绿色三角形)
    start_x, start_y = start[0]-1, start[1]-1
    plt.plot(start_x + 0.5, start_y + 0.5, 'g^', markersize=15, label='Start')
    
    # 绘制终点 (紫色五角星)
    end_x, end_y = end[0]-1, end[1]-1
    plt.plot(end_x + 0.5, end_y + 0.5, 'm*', markersize=15, label='End')
    
    # 绘制路径线 (蓝色带箭头)
    path_x = [p[0]-0.5 for p in path]  # 转换为格子中心坐标
    path_y = [p[1]-0.5 for p in path]
    for i in range(len(path)-1):
        dx = path_x[i+1] - path_x[i]
        dy = path_y[i+1] - path_y[i]
        ax.arrow(path_x[i], path_y[i], dx, dy, 
                head_width=0.2, head_length=0.2, fc='blue', ec='blue')
    
    # 添加坐标标签 (1-based)
    for x in range(COLS):
        for y in range(ROWS):
            plt.text(x + 0.5, y + 0.5, f'({x+1},{y+1})', 
                    ha='center', va='center', fontsize=8)
    
    plt.title('Path Planning Visualization\n(Red=Obstacles, Green=Start, Purple=End)')
    plt.legend()
    plt.show()

# 从C代码中提取的参数
ROWS, COLS = 7, 9
start = np.array([1, 1])
end = np.array([1, 9])
obstacles = np.array([[2, 2, 2], [2, 3, 4]])  # 三个障碍物的x,y坐标

# 模拟C程序输出的路径 (实际使用时替换为Planning函数的真实输出)
path = []
for y in range(1, 10): path.append([1, y])  # 第一行
for x in range(2, 8):
    if x % 2 == 0:
        for y in range(1, 10): 
            if not (x == 2 and 2 <= y <= 4): path.append([x, y])
    else:
        for y in range(9, 0, -1): 
            if not (x == 2 and 2 <= y <= 4): path.append([x, y])

# 调用绘图函数
draw_path(start, end, obstacles, path)